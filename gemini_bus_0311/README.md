# Gemini Bus & Metro Transfer Agent

基于 Gemini（OpenAI 兼容接口）+ Google Maps Directions API 的公交地铁换乘 Agent：
- 支持 Mapbox 路径探索回退（Google 无结果时）
- 输入：起点站、终点站
- 输出：多条公交/地铁换乘路线（Agent 总结 + 结构化路线）
- WebUI：地图多线路展示 + 备选路线列表

## 1. 环境要求

- Python 3.10+
- `GEMINI_API_KEY`
- `GOOGLE_MAPS_API_KEY`
- `MAPBOX_API_KEY`（可选，建议配置）
- `MAPILLARY_API_KEY`（可选，用于详情页街景预览）

## 2. 安装依赖

```bash
cd gemini_bus_0311
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

如果使用 conda：

```bash
conda run -n ai_agent python -m pip install -r requirements.txt
```

## 3. 配置环境变量

WSL / Linux:

```bash
export GEMINI_API_KEY="你的GeminiKey"
export GOOGLE_MAPS_API_KEY="你的GoogleMapsKey"
export MAPBOX_API_KEY="你的MapboxKey"
export MAPILLARY_API_KEY="你的MapillaryKey"
```

可选：复制 `.env.example`，设置模型和端口：

```bash
cp .env.example .env
```

`.env` 内容示例：

```env
GEMINI_MODEL=gemini-2.0-flash
HOST=127.0.0.1
PORT=8001
```

## 4. 启动服务

```bash
python -m uvicorn app.main:app --host ${HOST:-127.0.0.1} --port ${PORT:-8001} --reload
```

或 conda：

```bash
conda run -n ai_agent python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

浏览器访问：

- http://127.0.0.1:8001

## 5. 接口说明

### POST `/api/transit-agent`

请求体：

```json
{
  "origin": "北京南站",
  "destination": "国家图书馆"
}
```

响应（示例）：

```json
{
  "ok": true,
  "reply": "推荐优先选择方案1...",
  "plan": {
    "origin": "北京南站",
    "destination": "国家图书馆",
    "routes": [
      {
        "route_index": 1,
        "summary": "...",
        "duration_text": "45分钟",
        "distance_text": "15公里",
        "overview_polyline": "...",
        "steps": []
      }
    ]
  }
}
```
