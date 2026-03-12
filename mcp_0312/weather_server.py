"""
MCP Weather Server
使用 Open-Meteo 免费天气 API（无需 API Key）提供天气查询服务
"""

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("weather-server")

# ─── 常量 ────────────────────────────────────────────────────────────────────
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

WMO_CODES: dict[int, str] = {
    0: "晴天",
    1: "基本晴朗", 2: "局部多云", 3: "阴天",
    45: "有雾", 48: "冻雾",
    51: "小毛毛雨", 53: "中毛毛雨", 55: "大毛毛雨",
    61: "小雨", 63: "中雨", 65: "大雨",
    71: "小雪", 73: "中雪", 75: "大雪",
    77: "冰粒",
    80: "小阵雨", 81: "中阵雨", 82: "大阵雨",
    85: "小阵雪", 86: "大阵雪",
    95: "雷暴", 96: "轻微冰雹雷暴", 99: "大冰雹雷暴",
}


# ─── 工具函数 ─────────────────────────────────────────────────────────────────
async def _geocode(city: str) -> tuple[float, float, str]:
    """将城市名称转换为经纬度，返回 (latitude, longitude, display_name)"""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            GEOCODING_URL,
            params={"name": city, "count": 1, "language": "zh", "format": "json"},
        )
        resp.raise_for_status()
        data = resp.json()

    results = data.get("results")
    if not results:
        raise ValueError(f"找不到城市：{city}")

    r = results[0]
    display = r.get("name", city)
    if r.get("country"):
        display = f"{display}, {r['country']}"
    return r["latitude"], r["longitude"], display


def _wmo(code: int) -> str:
    return WMO_CODES.get(code, f"未知天气 (WMO {code})")


# ─── MCP 工具 ─────────────────────────────────────────────────────────────────
@mcp.tool()
async def get_current_weather(city: str) -> str:
    """
    查询指定城市的当前天气。

    参数:
        city: 城市名称，支持中文或英文，例如 "北京"、"Shanghai"、"Tokyo"
    返回:
        包含温度、体感温度、湿度、风速、天气状况的文字描述
    """
    lat, lon, display = await _geocode(city)

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            WEATHER_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "current": [
                    "temperature_2m",
                    "apparent_temperature",
                    "relative_humidity_2m",
                    "wind_speed_10m",
                    "wind_direction_10m",
                    "weather_code",
                    "precipitation",
                ],
                "timezone": "auto",
                "forecast_days": 1,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    cur = data["current"]
    return (
        f"📍 {display} 当前天气\n"
        f"🌤  天气状况：{_wmo(cur['weather_code'])}\n"
        f"🌡  温度：{cur['temperature_2m']}°C"
        f"（体感 {cur['apparent_temperature']}°C）\n"
        f"💧 相对湿度：{cur['relative_humidity_2m']}%\n"
        f"💨 风速：{cur['wind_speed_10m']} km/h，"
        f"风向：{cur['wind_direction_10m']}°\n"
        f"🌧  降水量：{cur['precipitation']} mm"
    )


@mcp.tool()
async def get_weather_forecast(city: str, days: int = 7) -> str:
    """
    查询指定城市未来多天的天气预报。

    参数:
        city: 城市名称，支持中文或英文，例如 "北京"、"Shanghai"
        days: 预报天数，1–16，默认 7 天
    返回:
        每日最高/最低气温、天气状况、降水概率的文字预报
    """
    days = max(1, min(days, 16))
    lat, lon, display = await _geocode(city)

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            WEATHER_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": [
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "weather_code",
                    "precipitation_sum",
                    "precipitation_probability_max",
                    "wind_speed_10m_max",
                ],
                "timezone": "auto",
                "forecast_days": days,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    daily = data["daily"]
    lines = [f"📍 {display} 未来 {days} 天天气预报\n"]
    for i in range(len(daily["time"])):
        lines.append(
            f"📅 {daily['time'][i]}\n"
            f"   天气：{_wmo(daily['weather_code'][i])}\n"
            f"   气温：{daily['temperature_2m_min'][i]}°C ~ "
            f"{daily['temperature_2m_max'][i]}°C\n"
            f"   降水：{daily['precipitation_sum'][i]} mm"
            f"（概率 {daily['precipitation_probability_max'][i]}%）\n"
            f"   最大风速：{daily['wind_speed_10m_max'][i]} km/h\n"
        )
    return "\n".join(lines)


@mcp.tool()
async def get_weather_by_coordinates(
    latitude: float, longitude: float
) -> str:
    """
    根据经纬度查询当前天气。

    参数:
        latitude:  纬度，范围 -90 ~ 90
        longitude: 经度，范围 -180 ~ 180
    返回:
        包含温度、湿度、风速、天气状况的文字描述
    """
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            WEATHER_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": [
                    "temperature_2m",
                    "apparent_temperature",
                    "relative_humidity_2m",
                    "wind_speed_10m",
                    "wind_direction_10m",
                    "weather_code",
                    "precipitation",
                ],
                "timezone": "auto",
                "forecast_days": 1,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    cur = data["current"]
    return (
        f"📍 坐标 ({latitude}, {longitude}) 当前天气\n"
        f"🌤  天气状况：{_wmo(cur['weather_code'])}\n"
        f"🌡  温度：{cur['temperature_2m']}°C"
        f"（体感 {cur['apparent_temperature']}°C）\n"
        f"💧 相对湿度：{cur['relative_humidity_2m']}%\n"
        f"💨 风速：{cur['wind_speed_10m']} km/h，"
        f"风向：{cur['wind_direction_10m']}°\n"
        f"🌧  降水量：{cur['precipitation']} mm"
    )


# ─── 入口 ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run(transport="stdio")
