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

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")
MAPBOX_API_KEY = os.environ.get("MAPBOX_API_KEY")
MAPILLARY_API_KEY = os.environ.get("MAPILLARY_API_KEY")
GEMINI_MODEL_FALLBACKS = ["gemini-2.5-flash", "gemini-2.5-pro"]

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


def _request_directions(origin: str, destination: str, mode: str) -> dict[str, Any]:
    response = HTTP_SESSION.get(
        "https://maps.googleapis.com/maps/api/directions/json",
        params={
            "origin": origin,
            "destination": destination,
            "mode": mode,
            "alternatives": "true",
            "language": "zh-CN",
            "departure_time": "now",
            "key": GOOGLE_MAPS_API_KEY,
        },
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def _format_distance_text(meters: float | int | None) -> str | None:
    if meters is None:
        return None
    km = float(meters) / 1000.0
    if km >= 1:
        return f"{km:.1f} 公里"
    return f"{int(round(float(meters)))} 米"


def _format_duration_text(seconds: float | int | None) -> str | None:
    if seconds is None:
        return None
    total_minutes = int(round(float(seconds) / 60.0))
    if total_minutes < 60:
        return f"{max(total_minutes, 1)}分钟"
    hours = total_minutes // 60
    minutes = total_minutes % 60
    if minutes == 0:
        return f"{hours}小时"
    return f"{hours}小时{minutes}分钟"


def _mapbox_geocode(query: str) -> dict[str, Any] | None:
    if not MAPBOX_API_KEY:
        return None

    response = HTTP_SESSION.get(
        f"https://api.mapbox.com/geocoding/v5/mapbox.places/{requests.utils.quote(query)}.json",
        params={
            "access_token": MAPBOX_API_KEY,
            "limit": 1,
            "language": "zh",
            "autocomplete": "false",
        },
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    features = (response.json() or {}).get("features") or []
    return features[0] if features else None


def _google_geocode(query: str) -> dict[str, Any] | None:
    response = HTTP_SESSION.get(
        "https://maps.googleapis.com/maps/api/geocode/json",
        params={
            "address": query,
            "language": "zh-CN",
            "key": GOOGLE_MAPS_API_KEY,
        },
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    data = response.json() or {}
    if data.get("status") != "OK":
        return None

    results = data.get("results") or []
    if not results:
        return None

    top = results[0]
    location = ((top.get("geometry") or {}).get("location") or {})
    lat = location.get("lat")
    lng = location.get("lng")
    if lat is None or lng is None:
        return None

    return {
        "lng": float(lng),
        "lat": float(lat),
        "place_name": top.get("formatted_address") or query,
    }


def _mapbox_directions(origin: str, destination: str) -> dict[str, Any] | None:
    if not MAPBOX_API_KEY:
        return None

    # Use Google geocoding first for better station-name resolution in Asia.
    origin_geo = _google_geocode(origin)
    destination_geo = _google_geocode(destination)

    if not origin_geo or not destination_geo:
        origin_feature = _mapbox_geocode(origin)
        destination_feature = _mapbox_geocode(destination)
        if not origin_feature or not destination_feature:
            return None
        origin_center = origin_feature.get("center") or []
        destination_center = destination_feature.get("center") or []
        if len(origin_center) != 2 or len(destination_center) != 2:
            return None
        origin_geo = {
            "lng": float(origin_center[0]),
            "lat": float(origin_center[1]),
            "place_name": origin_feature.get("place_name") or origin,
        }
        destination_geo = {
            "lng": float(destination_center[0]),
            "lat": float(destination_center[1]),
            "place_name": destination_feature.get("place_name") or destination,
        }

    if not origin_geo or not destination_geo:
        return None

    coords = f"{origin_geo['lng']},{origin_geo['lat']};{destination_geo['lng']},{destination_geo['lat']}"
    for profile in ["driving", "walking"]:
        response = HTTP_SESSION.get(
            f"https://api.mapbox.com/directions/v5/mapbox/{profile}/{coords}",
            params={
                "access_token": MAPBOX_API_KEY,
                "alternatives": "true",
                "overview": "full",
                "steps": "true",
                "geometries": "polyline",
                "language": "zh",
            },
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json() or {}
        if (data.get("code") == "Ok") and data.get("routes"):
            routes: list[dict[str, Any]] = []
            for idx, route in enumerate(data.get("routes", [])[:5], start=1):
                legs = route.get("legs") or []
                steps: list[dict[str, Any]] = []
                if legs:
                    for step in (legs[0].get("steps") or []):
                        steps.append(
                            {
                                "mode": profile.upper(),
                                "instruction": (step.get("maneuver") or {}).get("instruction") or "",
                                "distance_text": _format_distance_text(step.get("distance")),
                                "duration_text": _format_duration_text(step.get("duration")),
                                "polyline": step.get("geometry"),
                                "transit": None,
                            }
                        )

                routes.append(
                    {
                        "route_index": idx,
                        "summary": f"mapbox-{profile} · 方案 {idx}",
                        "distance_text": _format_distance_text(route.get("distance")),
                        "duration_text": _format_duration_text(route.get("duration")),
                        "departure_time": None,
                        "arrival_time": None,
                        "start_address": origin_geo.get("place_name"),
                        "end_address": destination_geo.get("place_name"),
                        "fare": None,
                        "overview_polyline": route.get("geometry"),
                        "steps": steps,
                    }
                )

            return {
                "origin": origin,
                "destination": destination,
                "routes": routes,
                "mode_used": profile,
                "notice": "Google 公交换乘不可用，已切换为 Mapbox 路径探索。",
                "provider": "mapbox",
                "transit_available": False,
            }

    return None


def _parse_routes(data: dict[str, Any], origin: str, destination: str, mode: str) -> list[dict[str, Any]]:
    routes: list[dict[str, Any]] = []
    for idx, route in enumerate(data.get("routes", [])[:5], start=1):
        legs = route.get("legs", [])
        if not legs:
            continue

        leg = legs[0]
        steps = [_normalize_transit_step(step) for step in leg.get("steps", [])]
        summary = route.get("summary") or f"方案 {idx}"
        if mode != "transit":
            summary = f"{mode} · {summary}"

        route_info = {
            "route_index": idx,
            "summary": summary,
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

    return routes


def _build_zero_results_message(data: dict[str, Any]) -> str:
    waypoints = data.get("geocoded_waypoints") or []
    if waypoints and all(wp.get("geocoder_status") == "OK" for wp in waypoints):
        return "Google 地图当前无法提供该区域路线数据（中国大陆地区较常见），建议更换境外地点或接入高德/百度地图。"
    return "未找到可用的公交/地铁换乘路线（请检查起点与终点名称）"


def get_transit_routes(origin: str, destination: str) -> dict[str, Any]:
    mode_used = "transit"
    data = _request_directions(origin, destination, mode_used)
    status = data.get("status")

    if status == "ZERO_RESULTS":
        # Prefer Mapbox fallback when Google transit has no results.
        mapbox_plan = _mapbox_directions(origin, destination)
        if mapbox_plan:
            return mapbox_plan

        # If Mapbox is not configured/unavailable, degrade with Google modes.
        for fallback_mode in ["driving", "walking"]:
            fallback_data = _request_directions(origin, destination, fallback_mode)
            if fallback_data.get("status") == "OK":
                mode_used = fallback_mode
                data = fallback_data
                status = "OK"
                break

    if status != "OK":
        if status in {"ZERO_RESULTS", "NOT_FOUND"}:
            raise ValueError(_build_zero_results_message(data))
        if status == "INVALID_REQUEST":
            raise ValueError("请求参数不完整，请检查起点和终点")
        error_msg = data.get("error_message") or status
        raise RuntimeError(f"Google Maps Directions 请求失败: {error_msg}")

    routes = _parse_routes(data, origin, destination, mode_used)
    if not routes:
        raise ValueError("未找到可用路线")

    plan: dict[str, Any] = {
        "origin": origin,
        "destination": destination,
        "routes": routes,
    }
    if mode_used != "transit":
        plan["mode_used"] = mode_used
        plan["notice"] = "当前区域公交数据不可用，已切换为其他出行方式。"
        plan["transit_available"] = False

    return plan


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
        response = _create_chat_completion_with_model_fallback(messages, tools)
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


def _is_quota_exhausted_error(exc: Exception) -> bool:
    text = str(exc).lower()
    keywords = [
        "429",
        "resource_exhausted",
        "quota",
        "rate limit",
        "rate-limit",
    ]
    return any(key in text for key in keywords)


def _is_model_unavailable_error(exc: Exception) -> bool:
    text = str(exc).lower()
    markers = [
        "no longer available",
        "is not found",
        "not supported",
        "error code: 404",
    ]
    return any(marker in text for marker in markers)


def _create_chat_completion_with_model_fallback(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]],
):
    tried: set[str] = set()
    candidate_models = [GEMINI_MODEL, *GEMINI_MODEL_FALLBACKS]
    last_exc: Exception | None = None

    for model in candidate_models:
        if model in tried:
            continue
        tried.add(model)
        try:
            return client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
            )
        except Exception as exc:
            last_exc = exc
            if _is_model_unavailable_error(exc):
                continue
            raise

    if last_exc:
        raise last_exc
    raise RuntimeError("Gemini 模型调用失败")


def _build_fallback_reply(plan: dict[str, Any]) -> str:
    routes = plan.get("routes", [])
    if not routes:
        return "已获取路线数据，但暂无可展示方案。"

    top = routes[0]
    transit_steps = [
        step
        for step in top.get("steps", [])
        if step.get("mode") == "TRANSIT" and step.get("transit")
    ]
    line_names = []
    for step in transit_steps:
        transit = step.get("transit") or {}
        line_name = transit.get("line_name")
        if line_name:
            line_names.append(line_name)

    line_text = " -> ".join(line_names[:4]) if line_names else "请查看下方路线明细"

    mode_used = plan.get("mode_used")
    provider = plan.get("provider")
    mode_hint = ""
    if mode_used and mode_used != "transit":
        mode_hint = f"当前公交数据不可用，已切换为{mode_used}路线。"
    if provider == "mapbox":
        mode_hint = "当前公交数据不可用；Mapbox 暂不提供公交换乘，仅返回驾车/步行探索路线。"

    return (
        "当前 Gemini 配额不足，已自动切换为基础路线建议。"
        f"{mode_hint}"
        f"优先参考方案1：预计{top.get('duration_text') or '-'}，"
        f"距离{top.get('distance_text') or '-'}，"
        f"涉及线路：{line_text}。"
    )


def _build_llm_unavailable_reply(plan: dict[str, Any]) -> str:
    base = _build_fallback_reply(plan)
    return base.replace("当前 Gemini 配额不足", "当前 Gemini 服务不可用")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "google_maps_api_key": GOOGLE_MAPS_API_KEY,
            "mapbox_api_key": MAPBOX_API_KEY,
            "mapillary_api_key": MAPILLARY_API_KEY,
        },
    )


@app.post("/api/transit-agent")
def transit_agent(payload: RouteRequest):
    origin = payload.origin.strip()
    destination = payload.destination.strip()
    try:
        result = run_transfer_agent(origin, destination)
        return {"ok": True, **result}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"路线服务请求失败: {exc}") from exc
    except Exception as exc:
        try:
            plan = get_transit_routes(origin, destination)
            fallback_reply = _build_fallback_reply(plan)
            if not _is_quota_exhausted_error(exc):
                fallback_reply = _build_llm_unavailable_reply(plan)

            return {
                "ok": True,
                "degraded": True,
                "reply": fallback_reply,
                "plan": plan,
            }
        except ValueError as route_exc:
            raise HTTPException(status_code=404, detail=str(route_exc)) from route_exc
        except requests.RequestException as route_exc:
            raise HTTPException(status_code=502, detail=f"路线服务请求失败: {route_exc}") from route_exc
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {exc}") from exc
