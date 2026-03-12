# Gemini Weather Agent WebUI

基于 Gemini（OpenAI 兼容接口）与 OpenWeather 的天气 Agent 示例：
- 用户在网页输入城市名
- Agent 调用函数工具查询实时天气
- 返回中文天气摘要

## 1. 准备环境

- Python 3.10+
- Gemini API Key
- OpenWeather API Key

## 2. 安装依赖

```bash
cd openai_weather_webui
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. 配置环境变量

先在运行服务的系统环境中设置 API Key（必须）：

- 如果服务在 **WSL** 中运行：请在 WSL 终端设置。
- 如果服务在 **Windows** 中运行：请在 PowerShell/CMD 设置。

### WSL / Linux

```bash
export OPENWEATHER_API_KEY="你的OpenWeatherKey"
export GEMINI_API_KEY="你的GeminiKey"
```

### Windows PowerShell

```powershell
$env:GEMINI_API_KEY="你的GeminiKey"
$env:OPENWEATHER_API_KEY="你的OpenWeatherKey"
```

### Windows CMD

```cmd
set GEMINI_API_KEY=你的GeminiKey
set OPENWEATHER_API_KEY=你的OpenWeatherKey
```

```bash
cp .env.example .env
```

编辑 `.env`：

```env
GEMINI_MODEL=gemini-2.0-flash
HOST=127.0.0.1
PORT=8000
```

## 4. 启动服务

如果你用 conda 环境 `ai_agent`（推荐）：

```bash
conda activate ai_agent
python -m uvicorn app.main:app --host ${HOST:-127.0.0.1} --port ${PORT:-8000} --reload
```

或直接使用原命令：

```bash
uvicorn app.main:app --host ${HOST:-127.0.0.1} --port ${PORT:-8000} --reload
```

打开浏览器访问：

- http://127.0.0.1:8000

> 在 Windows + WSL 场景下，通常可以直接在 Windows 浏览器访问 `http://127.0.0.1:8000`（端口由 WSL 转发到 Windows）。

## 5. 接口说明

### POST `/api/weather-agent`

请求体：

```json
{
  "city": "Beijing"
}
```

返回：

```json
{
  "ok": true,
  "reply": "北京当前天气...",
  "weather": {
    "city": "Beijing",
    "resolved_name": "北京",
    "country": "China",
    "temperature_c": 22.1,
    "humidity_percent": 40,
    "wind_speed_kmh": 12.5,
    "weather_text": "晴朗",
    "observation_time": "2026-03-10T10:00"
  }
}
```

## 6. 目录结构

```text
openai_weather_webui/
├── app/main.py
├── templates/index.html
├── static/app.js
├── static/style.css
├── requirements.txt
└── .env.example
```
