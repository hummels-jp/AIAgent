# CNN 恐慌指数展示网页

## Concept & Vision
一个专业、直观的金融市场恐慌指数可视化工具，帮助投资者实时了解市场情绪（恐慌/贪婪），并获得基于市场情绪的投资建议。界面设计现代专业，给人以金融终端的感觉。

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
- 单页应用，居中布局
- 顶部：标题和刷新按钮
- 中央：大型恐慌指数仪表盘（半圆形）
- 中部：详细数据卡片（数值、等级、变化趋势）
- 底部：操作建议面板（根据不同恐慌等级显示不同建议）

## Features & Interactions
1. **实时数据获取**：从 Alternative.me API 获取恐惧贪婪指数
2. **仪表盘可视化**：半圆形仪表盘显示当前指数（0-100）
3. **等级显示**：显示当前市场情绪等级（极度恐慌到极度贪婪）
4. **操作建议**：根据不同等级显示买入/持有/卖出建议
5. **自动刷新**：每60秒自动更新数据
6. **手动刷新**：支持手动点击刷新
7. **加载状态**：数据加载中显示loading动画
8. **错误处理**：API请求失败时显示友好错误提示

## Component Inventory
1. **Header**: 标题 + 刷新按钮
2. **GaugeDashboard**: 半圆形仪表盘组件
   - 背景弧（灰度）
   - 彩色弧（根据数值着色）
   - 中心数值显示
   - 等级标签
3. **DataCards**: 数据卡片组
   - 最后更新时间
   - 数据来源说明
4. **AdvicePanel**: 操作建议面板
   - 根据等级显示不同颜色背景
   - 包含标题、描述、操作建议列表

## Technical Approach
- 纯HTML/CSS/JavaScript，无框架依赖
- 使用 Fetch API 调用 Alternative.me Fear & Greed Index API
- CSS变量管理主题颜色
- CSS动画实现仪表盘效果
