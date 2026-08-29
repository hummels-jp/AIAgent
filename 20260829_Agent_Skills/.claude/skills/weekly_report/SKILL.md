# 周报自动生成器

## 描述
根据用户在 GitHub 上的提交日志（commit history），自动拉取指定时间范围内的提交记录，并生成结构化的每周工作周报。适用于个人工作汇报、团队进度同步、项目里程碑总结等场景。

## 使用方式
用户提供 GitHub 仓库地址和时间范围，模型调用脚本拉取提交日志，整理为周报格式输出。

## 输入参数
用户提供以下任意字段，字段缺失时由模型自行补全合理设定：

| 字段 | 说明 | 示例 |
|------|------|------|
| `仓库地址` | GitHub 仓库 URL 或 `owner/repo` 格式 | `https://github.com/user/repo` 或 `user/repo` |
| `分支` | 要统计的分支 | `main`、`develop`、`feature/xxx` |
| `时间范围` | 统计的起止时间 | `本周`、`上周`、`2026-08-25 ~ 2026-08-31` |
| `作者` | 只统计指定提交者 | `zhangsan`、`user@email.com` |
| `输出格式` | 周报输出格式 | `markdown`（默认）、`plain` |
| `输出路径` | 周报保存路径 | `./reports/weekly_20260830.md` |

## 输出格式
生成的周报包含以下结构化内容：

1. **报告标题**：周期 + 仓库名称。
2. **概览统计**：提交次数、涉及文件数、新增/删除行数、活跃天数。
3. **本周工作摘要**：按功能模块/主题归类的提交要点。
4. **详细提交记录**：按日期分组的提交列表，包含提交信息、作者、时间、变更文件数。
5. **工作亮点**：自动识别的重要提交（如功能上线、重大修复）。
6. **下周计划建议**：基于本周未完成事项或提交趋势的合理建议。

## 示例

### 输入
```
仓库地址：https://github.com/zhangsan/my-project
分支：main
时间范围：本周
作者：zhangsan
```

### 输出
```markdown
# 每周工作周报

**仓库**：my-project  
**周期**：2026-08-25 ~ 2026-08-31  
**作者**：zhangsan  
**生成时间**：2026-08-30 08:30

---

## 一、概览统计

| 指标 | 数值 |
|------|------|
| 提交次数 | 23 |
| 涉及文件 | 45 |
| 新增行数 | +1,250 |
| 删除行数 | -380 |
| 活跃天数 | 5 天 |

---

## 二、本周工作摘要

### 功能开发
- 实现用户登录/注册模块，支持 JWT 鉴权
- 完成订单列表页面前后端联调
- 新增数据导出 Excel 功能

### Bug 修复
- 修复支付回调重复通知问题
- 解决移动端页面布局错乱

### 优化与重构
- 重构用户权限校验逻辑，减少 30% 冗余代码
- 优化数据库查询，接口响应时间降低 40%

---

## 三、详细提交记录

### 2026-08-25（周一）
- `feat: 添加用户登录接口` — zhangsan, 10:23, 8 files changed
- `fix: 修复登录参数校验缺失` — zhangsan, 14:15, 2 files changed
- `refactor: 提取公共鉴权中间件` — zhangsan, 17:40, 5 files changed

### 2026-08-26（周二）
- `feat: 完成注册页面 UI` — zhangsan, 09:10, 6 files changed
- `feat: 注册接口联调` — zhangsan, 11:30, 4 files changed
- `fix: 修复注册重复提交` — zhangsan, 15:20, 1 file changed

### 2026-08-27（周三）
- `feat: 订单列表接口开发` — zhangsan, 09:45, 7 files changed
- `feat: 订单列表前端页面` — zhangsan, 14:00, 5 files changed
- `style: 调整订单卡片样式` — zhangsan, 16:30, 2 files changed

### 2026-08-28（周四）
- `feat: 数据导出 Excel 功能` — zhangsan, 10:00, 6 files changed
- `fix: 修复支付回调重复通知` — zhangsan, 13:45, 3 files changed
- `perf: 优化订单查询 SQL` — zhangsan, 16:20, 2 files changed

### 2026-08-29（周五）
- `refactor: 重构权限校验逻辑` — zhangsan, 09:30, 8 files changed
- `docs: 更新 API 文档` — zhangsan, 11:00, 1 file changed
- `chore: 清理无用依赖` — zhangsan, 15:00, 3 files changed

---

## 四、工作亮点

1. **用户认证体系完整落地**：从登录、注册到 JWT 鉴权，本周完成了完整的用户认证链路。
2. **支付稳定性提升**：修复了支付回调重复通知的线上问题，避免了重复发货风险。
3. **性能优化显著**：通过 SQL 优化和代码重构，核心接口响应时间降低 40%。

---

## 五、下周计划建议

1. 继续完善订单模块，开发订单详情和状态流转功能。
2. 补充单元测试，提升核心模块测试覆盖率。
3. 跟进用户反馈，优化注册/登录流程体验。
```

---

## 周报生成工作流

每完成参数解析后，必须立即调用周报生成脚本，拉取 GitHub 提交日志并生成周报。

### 步骤

1. **解析参数**：从用户输入中提取仓库地址、分支、时间范围、作者等。
2. **构建输出文件名**：使用当前日期命名，格式为 `weekly_report_<YYYYMMDD>.md`，例如 `weekly_report_20260830.md`。
3. **调用生成脚本**：执行

   ```bash
   python .claude/skills/weekly_report/scripts/generate_weekly_report.py \
       --repo "<仓库地址>" \
       --branch "<分支>" \
       --since "<开始日期>" \
       --until "<结束日期>" \
       --author "<作者>" \
       -o ./reports/weekly_report_<YYYYMMDD>.md
   ```

   如果用户未指定输出路径，默认保存到 `./reports/` 目录。
4. **输出结果**：向用户展示生成的周报内容，并报告文件保存路径。

### 示例调用

```bash
python .claude/skills/weekly_report/scripts/generate_weekly_report.py \
    --repo "zhangsan/my-project" \
    --branch "main" \
    --since "2026-08-25" \
    --until "2026-08-31" \
    --author "zhangsan" \
    -o ./reports/weekly_report_20260830.md
```

### 注意

- `./reports` 目录不存在时，脚本会自动创建。
- 脚本通过 GitHub API 拉取提交日志，公开仓库无需认证；私有仓库需在 `config.json` 中配置 `GITHUB_TOKEN`。
- 若用户未指定时间范围，默认统计本周（周一至周日）。
- 若用户未指定作者，统计所有提交者。
- 若用户明确说"不要保存文件"，则仅输出周报内容到终端，不写入文件。

## 约束与风格
- 周报语言应简洁专业，突出工作成果和价值。
- 提交信息按类型自动分类（feat/fix/refactor/docs/style/perf/test/chore）。
- 自动识别 `BREAKING CHANGE`、`fix #issue` 等关键信息标记为工作亮点。
- 保持客观中立，不夸大不虚构工作内容。
- 若本周无提交记录，如实说明并建议检查时间范围或分支是否正确。

## 示例调用
```
/weekly_report
仓库地址：https://github.com/zhangsan/my-project
分支：main
时间范围：本周
作者：zhangsan
```
