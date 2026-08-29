#!/usr/bin/env python3
"""
周报自动生成脚本
根据 GitHub 提交日志生成结构化周报
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import requests


def load_config():
    """加载配置文件"""
    config_path = Path(__file__).parent / "config.json"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def parse_repo(repo: str) -> tuple:
    """解析仓库地址，返回 (owner, repo_name)"""
    # 支持 https://github.com/owner/repo 或 owner/repo
    patterns = [
        r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$",
        r"^([^/]+)/([^/]+)$",
    ]
    for pattern in patterns:
        match = re.search(pattern, repo)
        if match:
            return match.group(1), match.group(2)
    raise ValueError(f"无法解析仓库地址: {repo}")


def get_date_range(time_range: str) -> tuple:
    """解析时间范围，返回 (since, until) 日期字符串"""
    today = datetime.now()

    if time_range in ("本周", "this week"):
        # 本周一到周日
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)
        return monday.strftime("%Y-%m-%d"), sunday.strftime("%Y-%m-%d")

    if time_range in ("上周", "last week"):
        # 上周一到周日
        monday = today - timedelta(days=today.weekday() + 7)
        sunday = monday + timedelta(days=6)
        return monday.strftime("%Y-%m-%d"), sunday.strftime("%Y-%m-%d")

    # 自定义格式: 2026-08-25 ~ 2026-08-31 或 2026-08-25~2026-08-31
    match = re.match(r"(\d{4}-\d{2}-\d{2})\s*~\s*(\d{4}-\d{2}-\d{2})", time_range)
    if match:
        return match.group(1), match.group(2)

    # 单个日期，表示那一周
    match = re.match(r"(\d{4}-\d{2}-\d{2})", time_range)
    if match:
        d = datetime.strptime(match.group(1), "%Y-%m-%d")
        monday = d - timedelta(days=d.weekday())
        sunday = monday + timedelta(days=6)
        return monday.strftime("%Y-%m-%d"), sunday.strftime("%Y-%m-%d")

    # 默认本周
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return monday.strftime("%Y-%m-%d"), sunday.strftime("%Y-%m-%d")


def fetch_commits(owner: str, repo: str, branch: str, since: str, until: str,
                  author: str = None, token: str = None) -> list:
    """通过 GitHub API 拉取提交记录"""
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    params = {
        "sha": branch,
        "since": f"{since}T00:00:00Z",
        "until": f"{until}T23:59:59Z",
        "per_page": 100,
    }
    if author:
        params["author"] = author

    all_commits = []
    page = 1
    while True:
        params["page"] = page
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        commits = response.json()
        if not commits:
            break
        all_commits.extend(commits)
        if len(commits) < 100:
            break
        page += 1

    return all_commits


def classify_commit(message: str) -> str:
    """根据提交信息分类"""
    message_lower = message.lower()
    if message_lower.startswith(("feat", "feature")):
        return "功能开发"
    if message_lower.startswith("fix"):
        return "Bug 修复"
    if message_lower.startswith("refactor"):
        return "优化与重构"
    if message_lower.startswith("perf"):
        return "性能优化"
    if message_lower.startswith("docs"):
        return "文档更新"
    if message_lower.startswith("style"):
        return "样式调整"
    if message_lower.startswith("test"):
        return "测试相关"
    if message_lower.startswith("chore"):
        return "构建/工具"
    return "其他"


def is_highlight(message: str) -> bool:
    """判断是否为重要提交"""
    keywords = ["breaking change", "fix #", "close #", "resolve #",
                "major", "release", "security", "critical"]
    message_lower = message.lower()
    return any(kw in message_lower for kw in keywords)


def generate_report(commits: list, repo_name: str, since: str, until: str,
                    author: str = None) -> str:
    """生成周报 Markdown 内容"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 统计
    total_commits = len(commits)
    total_files = 0
    total_additions = 0
    total_deletions = 0
    active_days = set()
    classified = defaultdict(list)
    highlights = []
    daily_commits = defaultdict(list)

    for commit in commits:
        commit_data = commit.get("commit", {})
        message = commit_data.get("message", "").split("\n")[0]
        author_name = commit_data.get("author", {}).get("name", "unknown")
        date_str = commit_data.get("author", {}).get("date", "")
        stats = commit.get("stats", {})

        files_changed = stats.get("total", 0)
        additions = stats.get("additions", 0)
        deletions = stats.get("deletions", 0)

        total_files += files_changed
        total_additions += additions
        total_deletions += deletions

        if date_str:
            date_obj = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
            active_days.add(date_obj.strftime("%Y-%m-%d"))
            daily_commits[date_obj.strftime("%Y-%m-%d")].append({
                "message": message,
                "author": author_name,
                "time": date_obj.strftime("%H:%M"),
                "files": files_changed,
            })

        category = classify_commit(message)
        classified[category].append(message)

        if is_highlight(message):
            highlights.append(message)

    # 构建 Markdown
    lines = [
        "# 每周工作周报",
        "",
        f"**仓库**：{repo_name}  ",
        f"**周期**：{since} ~ {until}  ",
    ]
    if author:
        lines.append(f"**作者**：{author}  ")
    lines.extend([
        f"**生成时间**：{now}",
        "",
        "---",
        "",
        "## 一、概览统计",
        "",
        "| 指标 | 数值 |",
        "|------|------|",
        f"| 提交次数 | {total_commits} |",
        f"| 涉及文件 | {total_files} |",
        f"| 新增行数 | +{total_additions:,} |",
        f"| 删除行数 | -{total_deletions:,} |",
        f"| 活跃天数 | {len(active_days)} 天 |",
        "",
        "---",
        "",
        "## 二、本周工作摘要",
        "",
    ])

    # 按类别输出
    category_order = ["功能开发", "Bug 修复", "优化与重构", "性能优化",
                      "文档更新", "样式调整", "测试相关", "构建/工具", "其他"]
    for category in category_order:
        if category in classified:
            lines.append(f"### {category}")
            for msg in classified[category][:10]:  # 每类最多10条
                lines.append(f"- {msg}")
            if len(classified[category]) > 10:
                lines.append(f"- ... 等 {len(classified[category])} 条")
            lines.append("")

    lines.extend([
        "---",
        "",
        "## 三、详细提交记录",
        "",
    ])

    # 按日期输出
    week_days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    for date in sorted(daily_commits.keys()):
        d = datetime.strptime(date, "%Y-%m-%d")
        weekday = week_days[d.weekday()]
        lines.append(f"### {date}（{weekday}）")
        for c in daily_commits[date]:
            lines.append(f"- `{c['message']}` — {c['author']}, {c['time']}, {c['files']} files changed")
        lines.append("")

    lines.extend([
        "---",
        "",
        "## 四、工作亮点",
        "",
    ])

    if highlights:
        for i, h in enumerate(highlights[:5], 1):
            lines.append(f"{i}. {h}")
    else:
        lines.append("本周无特别标记的重要提交。")
    lines.append("")

    lines.extend([
        "---",
        "",
        "## 五、下周计划建议",
        "",
        "1. 继续推进本周未完成的功能开发。",
        "2. 关注代码质量和测试覆盖率。",
        "3. 及时响应和处理线上问题反馈。",
        "",
    ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="根据 GitHub 提交日志生成周报")
    parser.add_argument("--repo", required=True, help="GitHub 仓库地址或 owner/repo")
    parser.add_argument("--branch", default="main", help="分支名称，默认 main")
    parser.add_argument("--since", help="开始日期，格式 YYYY-MM-DD")
    parser.add_argument("--until", help="结束日期，格式 YYYY-MM-DD")
    parser.add_argument("--time-range", default="本周", help="时间范围：本周/上周/YYYY-MM-DD ~ YYYY-MM-DD")
    parser.add_argument("--author", help="只统计指定作者")
    parser.add_argument("-o", "--output", help="输出文件路径")
    parser.add_argument("--no-save", action="store_true", help="不保存文件，仅输出到终端")

    args = parser.parse_args()

    # 解析时间范围
    if args.since and args.until:
        since, until = args.since, args.until
    else:
        since, until = get_date_range(args.time_range)

    # 解析仓库
    try:
        owner, repo_name = parse_repo(args.repo)
    except ValueError as e:
        print(f"[错误] {e}", file=sys.stderr)
        sys.exit(1)

    # 加载配置
    config = load_config()
    token = config.get("GITHUB_TOKEN") or os.environ.get("GITHUB_TOKEN")

    print(f"[信息] 正在拉取 {owner}/{repo_name} ({args.branch}) 的提交记录...")
    print(f"[信息] 时间范围: {since} ~ {until}")
    if args.author:
        print(f"[信息] 作者过滤: {args.author}")

    try:
        commits = fetch_commits(owner, repo_name, args.branch, since, until,
                                args.author, token)
    except requests.exceptions.HTTPError as e:
        print(f"[API 错误] {e}", file=sys.stderr)
        if e.response.status_code == 404:
            print("[提示] 仓库不存在或分支名称错误，私有仓库请配置 GITHUB_TOKEN", file=sys.stderr)
        elif e.response.status_code == 403:
            print("[提示] API 速率限制，请配置 GITHUB_TOKEN 或稍后重试", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"[网络错误] {e}", file=sys.stderr)
        sys.exit(1)

    print(f"[信息] 共拉取到 {len(commits)} 条提交记录")

    if not commits:
        print("[警告] 本周无提交记录，请检查时间范围或分支是否正确")
        report = f"# 每周工作周报\n\n**仓库**：{repo_name}\n**周期**：{since} ~ {until}\n\n本周无提交记录。\n"
    else:
        report = generate_report(commits, repo_name, since, until, args.author)

    # 输出
    print("\n" + "=" * 60)
    print(report)
    print("=" * 60 + "\n")

    # 保存文件
    if not args.no_save:
        if args.output:
            output_path = Path(args.output)
        else:
            today = datetime.now().strftime("%Y%m%d")
            output_path = Path(f"./reports/weekly_report_{today}.md")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"[已保存] {output_path.absolute()}")


if __name__ == "__main__":
    main()
