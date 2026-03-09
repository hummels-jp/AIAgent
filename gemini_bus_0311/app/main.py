import json
import os
import re
from typing import Any

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from openai import OpenAI
from pydantic import BaseModel, Field
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

load_dotenv()

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY in system environment variables.")

if not GOOGLE_MAPS_API_KEY:
    raise RuntimeError("Missing GOOGLE_MAPS_API_KEY in system environment variables.")

client = OpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

app = FastAPI(title="Gemini Bus & Metro Transfer Agent")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


class RouteRequest(BaseModel):
    origin: str = Field(min_length=1, max_length=120)
    destination: str = Field(min_length=1, max_length=120)


def _build_http_session() -> requests.Session:
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=0.8,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


HTTP_SESSION = _build_http_session()
REQUEST_TIMEOUT = (8, 30)


def _strip_html(text: str | None) -> str:
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", "", text)
    return clean.replace("&nbsp;", " ").strip()


def _normalize_transit_step(step: dict[str, Any]) -> dict[str, Any]:
    mode = step.get("travel_mode", "UNKNOWN")
    transit_details = step.get("transit_details", {}) if mode == "TRANSIT" else {}

    vehicle = transit_details.get("line", {}).get("vehicle", {})
    line = transit_details.get("line", {})

    return {
        "mode": mode,
        "instruction": _strip_html(step.get("html_instructions")),
        "distance_text": step.get("distance", {}).get("text"),
        "duration_text": step.get("duration", {}).get("text"),
        "polyline": (step.get("polyline") or {}).get("points"),
        "transit": {
            "vehicle_type": vehicle.get("type"),
            "vehicle_name": vehicle.get("name"),
            "line_name": line.get("name") or line.get("short_name") or line.get("id"),
            "line_color": line.get("color"),
            "departure_stop": (transit_details.get("departure_stop") or {}).get("name"),
            "arrival_stop": (transit_details.get("arrival_stop") or {}).get("name"),
            "num_stops": transit_details.get("num_stops"),
        }
        if mode == "TRANSIT"
        else None,
    }


def get_transit_routes(origin: str, destination: str) -> dict[str, Any]:
    response = HTTP_SESSION.get(
        "https://maps.googleapis.com/maps/api/directions/json",
        params={
            "origin": origin,
            "destination": destination,
            "mode": "transit",
            "alternatives": "true",
            "language": "zh-CN",
            "key": GOOGLE_MAPS_API_KEY,
        },
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    data = response.json()

    status = data.get("status")
    if status != "OK":
        if status == "ZERO_RESULTS":
            raise ValueError("未找到可用的公交/地铁换乘路线")
        error_msg = data.get("error_message") or status
        raise RuntimeError(f"Google Maps Directions 请求失败: {error_msg}")

    routes = []
    for idx, route in enumerate(data.get("routes", [])[:5], start=1):
        legs = route.get("legs", [])
        if not legs:
            continue

        leg = legs[0]
        steps = [_normalize_transit_step(step) for step in leg.get("steps", [])]

        route_info = {
            "route_index": idx,
            "summary": route.get("summary") or f"方案 {idx}",
            "distance_text": leg.get("distance", {}).get("text"),
            "duration_text": leg.get("duration", {}).get("text"),
            "departure_time": (leg.get("departure_time") or {}).get("text"),
            "arrival_time": (leg.get("arrival_time") or {}).get("text"),
            "start_address": leg.get("start_address"),
            "end_address": leg.get("end_address"),
            "fare": (route.get("fare") or {}).get("text"),
            "overview_polyline": (route.get("overview_polyline") or {}).get("points"),
            "steps": steps,
        }
        routes.append(route_info)

    if not routes:
        raise ValueError("未找到可用的公交/地铁换乘路线")

    return {
        "origin": origin,
        "destination": destination,
        "routes": routes,
    }


def run_transfer_agent(origin: str, destination: str) -> dict[str, Any]:
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_transit_routes",
                "description": "查询起点和终点之间的公交地铁换乘路线（可返回多条备选线路）",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "origin": {"type": "string", "description": "起点站或地点"},
                        "destination": {"type": "string", "description": "终点站或地点"},
                    },
                    "required": ["origin", "destination"],
                    "additionalProperties": False,
                },
            },
        }
    ]

    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": (
                "你是公交地铁换乘助手。"
                "必须优先调用工具获得路线数据，再用中文总结推荐方案。"
                "输出应对比多个方案，说明时间、换乘次数、线路名称。"
            ),
        },
        {
            "role": "user",
            "content": f"请查询从{origin}到{destination}的公交地铁换乘路线",
        },
    ]

    latest_plan: dict[str, Any] | None = None

    for _ in range(5):
        response = client.chat.completions.create(
            model=GEMINI_MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
        message = response.choices[0].message
        tool_calls = message.tool_calls or []

        if not tool_calls:
            if message.content:
                return {"reply": message.content, "plan": latest_plan}
            raise RuntimeError("Gemini 返回为空")

        messages.append(message.model_dump(exclude_none=True))

        for call in tool_calls:
            if call.function.name != "get_transit_routes":
                continue

            args = json.loads(call.function.arguments or "{}")
            call_origin = args.get("origin", origin)
            call_destination = args.get("destination", destination)
            result = get_transit_routes(call_origin, call_destination)
            latest_plan = result

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )

    raise RuntimeError("Gemini 工具调用轮次超限")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "google_maps_api_key": GOOGLE_MAPS_API_KEY,
        },
    )


@app.post("/api/transit-agent")
def transit_agent(payload: RouteRequest):
    try:
        result = run_transfer_agent(payload.origin.strip(), payload.destination.strip())
        return {"ok": True, **result}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"路线服务请求失败: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {exc}") from exc
