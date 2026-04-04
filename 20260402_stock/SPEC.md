# CNN 恐慌指数展示网页

## Concept & Vision
一个专业、直观的金融市场恐慌指数可视化工具，帮助投资者实时了解市场情绪（恐慌/贪婪），并获得基于市场情绪的投资建议。界面采用时钟仪表盘设计，给人以经典金融终端的感觉，同时具有现代科技感。

## Design Language
- **Aesthetic**: 深色金融终端风格，专业且富有科技感
- **Color Palette**:
  - Background: #0a0e17 (深蓝黑)
  - Card Background: #111827 (深灰蓝)
  - Primary: #00d4aa (青绿 - 代表贪婪)
  - Danger: #ff4757 (红色 - 代表恐慌)
  - Accent: #ffa502 (橙色 - 代表中性)
  - Text Primary: #ffffff
  - Text Secondary: #94a3b8
- **Typography**: Inter (Google Fonts), system-ui fallback
- **Motion**: 数值变化时有平滑过渡动画，仪表盘指针有弹性动画

## Layout & Structure
- 单页应用，双列布局（响应式）
- 顶部：标题和刷新按钮
- 左侧：时钟式仪表盘（核心可视化）
  - 圆形时钟设计，刻度0-100
  - 彩色环形区域表示恐慌/中性/贪婪区间
  - 中央显示当前数值和情绪等级
  - 指针动态指向当前恐慌指数位置
- 右侧：操作建议面板
  - 根据不同恐慌等级显示不同建议
  - 包含标题、描述、操作建议列表
- 底部：实时监控状态和倒计时刷新提示
- 下方：美股热门板块展示区域
  - 5个近一周上涨热门板块（美股市场）
  - 每个板块显示：板块名称、周涨幅、1个ETF链接、3支龙头股链接
  - 支持近一天(1D)/近一周(1W)/近一月(1M)/近三月(3M)标签切换
  - 链接指向Yahoo Finance查看K线图

## Features & Interactions
1. **实时数据获取**：从 Alternative.me API 获取恐惧贪婪指数
2. **热门板块真实数据**：从富途 OpenD API 获取美股实时涨跌幅数据
   - 通过 TCP Socket 连接富途 OpenD
   - 支持 1D/1W/1M/3M 四个时间段
   - 数据包含板块ETF和龙头股涨跌幅
3. **仪表盘可视化**：半圆形仪表盘显示当前指数（0-100）
4. **等级显示**：显示当前市场情绪等级（极度恐慌到极度贪婪）
5. **操作建议**：根据不同等级显示买入/持有/卖出建议
6. **自动刷新**：每60秒自动更新数据
7. **手动刷新**：支持手动点击刷新
8. **加载状态**：数据加载中显示loading动画
9. **错误处理**：API请求失败时显示友好错误提示

## Component Inventory
1. **Header**: 标题 + 刷新按钮
2. **ClockDashboard**: 时钟式仪表盘组件
   - 时钟表盘：圆形设计，带刻度（0-100）
   - 彩色区域：红色（恐慌）→ 黄色（中性）→ 绿色（贪婪）
   - 时钟指针：根据数值动态旋转
   - 中央显示：当前数值和情绪等级
   - 状态栏：实时监控指示灯 + 刷新倒计时
   - 图例：恐慌/中性/贪婪颜色说明
3. **AdvicePanel**: 操作建议面板
   - 根据等级显示不同颜色背景
   - 包含标题、描述、操作建议列表

## Technical Approach
- 纯HTML/CSS/JavaScript，无框架依赖
- 使用 Fetch API 调用 Alternative.me Fear & Greed Index API
- CSS变量管理主题颜色
- CSS动画实现仪表盘效果

---

# 富途交易记录展示网页

## Concept & Vision
一个简洁直观的功能模块，帮助用户查看其在富途证券账户的历史交易记录。通过连接富途 OpenD，获取用户的成交历史，并以清晰易懂的表格形式展示。

## Design Language
- **Aesthetic**: 与主页面保持一致的深色金融终端风格
- **Color Palette**: 与恐慌指数页面保持一致
- **Typography**: Inter (Google Fonts), system-ui fallback
- **Motion**: 表格行hover有平滑过渡动画

## Layout & Structure
- 交易记录面板位于热门板块下方
- 显示交易表格，包含：时间、股票代码、股票名称、方向（买入/卖出）、成交数量、成交价格、成交金额
- 支持按时间段筛选（今日、近一周、近一月）
- 显示连接状态和数据来源

## Features & Interactions
1. **富途账户连接状态检测**
   - 自动检测 OpenD 连接状态
   - 显示连接/断开状态指示器
2. **历史成交记录获取**
   - 从富途 OpenD API 获取历史成交数据
   - proto_id: 2222 (Trd_GetHistoryOrderFillList)
   - 支持日期范围筛选
3. **交易表格展示**
   - 交易时间
   - 股票代码和名称
   - 交易方向（买入/卖出，带颜色区分）
   - 成交数量
   - 成交价格
   - 成交金额
4. **时间段筛选**
   - 今日成交
   - 近一周
   - 近一月
5. **加载状态**
   - 数据加载中显示loading动画
6. **错误处理**
   - 连接失败时显示友好提示

## Component Inventory
1. **TradeHistoryPanel**: 交易记录面板容器
2. **TradeTable**: 交易记录表格
   - 表头：时间、股票、方向、数量、价格、金额
   - 表格行：hover高亮效果
   - 空状态：无交易记录时显示提示
3. **TradeFilter**: 时间段筛选器
4. **ConnectionStatus**: 连接状态指示器

## Technical Approach
- 通过富途 OpenD API 获取交易数据
- 使用 TCP Socket 通信协议
- 后端 Express 服务器代理 API 请求
- 前端通过 fetch 调用后端 API
