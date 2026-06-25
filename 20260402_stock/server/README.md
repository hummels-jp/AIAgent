# 富途OpenD API 服务

## 简介

这是一个Node.js服务，用于连接富途OpenD获取美股热门板块数据。

## 前置要求

1. 安装富途OpenD软件
2. 使用富途证券账号登录OpenD
3. 确保OpenD状态为"已连接"

## 安装

```bash
cd server
npm install
```

## 启动

```bash
npm start
```

## API接口

### 获取热门板块
```
GET http://localhost:3000/api/hot-sectors
```

响应示例：
```json
{
  "success": true,
  "connected": true,
  "data": [...],
  "updateTime": 1709401234567,
  "source": "futu_api"
}
```

### 获取股票报价
```
GET http://localhost:3000/api/quote/NVDA
```

### 健康检查
```
GET http://localhost:3000/api/health
```

## 注意事项

- OpenD需要保持运行状态
- 服务器会自动缓存数据5分钟
- 如果OpenD未连接，会使用模拟数据
