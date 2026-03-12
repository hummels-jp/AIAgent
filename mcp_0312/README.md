# MCP 天气查询服务器

基于 [Open-Meteo](https://open-meteo.com/) 免费天气 API 构建的 MCP Server，**无需任何 API Key**。

## 提供的工具

| 工具 | 说明 |
|---|---|
| `get_current_weather(city)` | 查询指定城市的实时天气 |
| `get_weather_forecast(city, days)` | 查询指定城市未来 1–16 天天气预报 |
| `get_weather_by_coordinates(latitude, longitude)` | 根据经纬度查询实时天气 |

## 安装

```bash
pip install -r requirements.txt
```

## 运行

### 直接运行（stdio 模式）

```bash
python weather_server.py
```

### 使用 MCP CLI 开发调试

```bash
mcp dev weather_server.py
```

## 接入 Claude Desktop

在 `claude_desktop_config.json` 中添加以下配置：

```json
{
  "mcpServers": {
    "weather": {
      "command": "python",
      "args": ["/home/kotei/huqianqian_git/AIAgent/mcp_0312/weather_server.py"]
    }
  }
}
```

## 接入 VS Code GitHub Copilot

在 `.vscode/mcp.json` 中添加：

```json
{
  "servers": {
    "weather": {
      "type": "stdio",
      "command": "python",
      "args": ["${workspaceFolder}/weather_server.py"]
    }
  }
}
```

## 示例查询

- 查询北京今天的天气
- 上海未来 3 天的天气预报
- 查询经纬度 (39.9, 116.4) 的天气

## 数据来源

- 天气数据：[Open-Meteo API](https://open-meteo.com/)（免费，无需注册）
- 地理编码：[Open-Meteo Geocoding API](https://open-meteo.com/en/docs/geocoding-api)
