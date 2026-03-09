import json
import os
from datetime import datetime, timezone
from typing import Any, Dict

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
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY in system environment variables.")

if not OPENWEATHER_API_KEY:
    raise RuntimeError("Missing OPENWEATHER_API_KEY in system environment variables.")

client = OpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

app = FastAPI(title="Gemini Weather Agent WebUI")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


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
REQUEST_TIMEOUT = (8, 25)


class WeatherRequest(BaseModel):
    city: str = Field(min_length=1, max_length=80)


def _is_llm_quota_error(exc: Exception) -> bool:
    message = str(exc).lower()
    quota_keywords = [
        "insufficient_quota",
        "resource_exhausted",
        "quota exceeded",
        "rate limit",
        "error code: 429",
    ]
    return any(keyword in message for keyword in quota_keywords)


def get_current_weather_by_city(city: str) -> Dict[str, Any]:
    geo_resp = HTTP_SESSION.get(
        "https://api.openweathermap.org/geo/1.0/direct",
        params={"q": city, "limit": 1, "appid": OPENWEATHER_API_KEY},
        timeout=REQUEST_TIMEOUT,
    )
    geo_resp.raise_for_status()
    geo_data = geo_resp.json()

    if not geo_data:
        raise ValueError(f"未找到城市：{city}")

    location = geo_data[0]
    lat = location["lat"]
    lon = location["lon"]

    weather_resp = HTTP_SESSION.get(
        "https://api.openweathermap.org/data/2.5/weather",
        params={
            "lat": lat,
            "lon": lon,
            "appid": OPENWEATHER_API_KEY,
            "units": "metric",
            "lang": "zh_cn",
        },
        timeout=REQUEST_TIMEOUT,
    )
    weather_resp.raise_for_status()
    weather_data = weather_resp.json()

    main_data = weather_data.get("main", {})
    wind_data = weather_data.get("wind", {})
    weather_items = weather_data.get("weather", [])
    weather_item = weather_items[0] if weather_items else {}
    weather_text = weather_item.get("description") or "未知天气"
    weather_code = int(weather_item.get("id", -1))

    dt_timestamp = weather_data.get("dt")
    observation_time = None
    if isinstance(dt_timestamp, (int, float)):
        observation_time = datetime.fromtimestamp(dt_timestamp, tz=timezone.utc).isoformat()

    wind_speed_ms = wind_data.get("speed")
    wind_speed_kmh = round(float(wind_speed_ms) * 3.6, 1) if wind_speed_ms is not None else None

    return {
        "city": city,
        "resolved_name": location.get("local_names", {}).get("zh") or location.get("name"),
        "country": location.get("country") or weather_data.get("sys", {}).get("country"),
        "latitude": lat,
        "longitude": lon,
        "temperature_c": main_data.get("temp"),
        "humidity_percent": main_data.get("humidity"),
        "wind_speed_kmh": wind_speed_kmh,
        "weather_code": weather_code,
        "weather_text": weather_text,
        "observation_time": observation_time,
    }


def run_weather_agent(city: str) -> Dict[str, Any]:
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_current_weather_by_city",
                "description": "根据城市名查询当前天气信息",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "城市名，例如 Beijing、Shanghai、London",
                        }
                    },
                    "required": ["city"],
                    "additionalProperties": False,
                },
            },
        }
    ]

    system_prompt = (
        "你是一个天气助手。"
        "当用户提供城市名时，你必须优先调用工具获取实时天气数据，"
        "再用简洁中文返回天气摘要。"
    )

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"请查询{city}当前天气"},
    ]

    latest_weather: Dict[str, Any] | None = None

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
                return {"reply": message.content, "weather": latest_weather}
            raise RuntimeError("Gemini 返回为空")

        messages.append(message.model_dump(exclude_none=True))

        for call in tool_calls:
            if call.function.name != "get_current_weather_by_city":
                continue
            args = json.loads(call.function.arguments or "{}")
            call_city = args.get("city", city)
            tool_result = get_current_weather_by_city(call_city)
            latest_weather = tool_result
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(tool_result, ensure_ascii=False),
                }
            )

    raise RuntimeError("Gemini 工具调用轮次超限")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/weather-agent")
def weather_agent(payload: WeatherRequest):
    city = payload.city.strip()
    try:
        result = run_weather_agent(city)
        return {"ok": True, **result}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"天气服务请求失败: {exc}") from exc
    except Exception as exc:
        if _is_llm_quota_error(exc):
            try:
                weather = get_current_weather_by_city(city)
                return {
                    "ok": True,
                    "fallback": True,
                    "reply": "Gemini 当前额度或速率受限，已自动降级为 OpenWeather 直连结果。",
                    "weather": weather,
                }
            except ValueError as fallback_exc:
                raise HTTPException(status_code=404, detail=str(fallback_exc)) from fallback_exc
            except requests.RequestException as fallback_exc:
                raise HTTPException(
                    status_code=502,
                    detail=f"天气服务请求失败: {fallback_exc}",
                ) from fallback_exc

        raise HTTPException(status_code=500, detail=f"服务器内部错误: {exc}") from exc
