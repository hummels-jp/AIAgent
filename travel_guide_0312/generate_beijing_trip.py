from __future__ import annotations

import html
import json
import os
from pathlib import Path
from textwrap import dedent
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "beijing_trip"

FALLBACK_SUBWAY_SEGMENTS = [
    {
        "title": "天安门东 -> 颐和园",
        "summary": "建议乘坐地铁 1 号线转 4 号线大兴线，到北宫门站下车后步行进入颐和园北侧，整体换乘清晰、步行压力较小。",
        "steps": [
            "从天安门东站乘坐地铁 1 号线八通线，往古城或苹果园方向，乘坐 3 站到西单站。",
            "在西单站换乘地铁 4 号线大兴线，往安河桥北方向，乘坐 10 站到北宫门站。",
            "从北宫门站出站后步行约 10 至 15 分钟可达颐和园北宫门入口；如必须前往东宫门，可在西苑一带接驳短途公交或打车。",
        ],
        "duration": "约 45 至 60 分钟",
        "note": "由于当前高德 MCP / REST key 返回 USERKEY_PLAT_NOMATCH，本段为基于公开地铁线路整理的兜底方案。",
    },
    {
        "title": "颐和园 -> 南锣鼓巷",
        "summary": "建议从北宫门站上车，乘坐地铁 4 号线至平安里换乘 6 号线，在南锣鼓巷站下车。",
        "steps": [
            "从颐和园北宫门入口附近步行返回北宫门站。",
            "乘坐地铁 4 号线大兴线，往天宫院方向，乘坐 8 站到平安里站。",
            "在平安里站换乘地铁 6 号线，往潞城方向，乘坐 2 站到南锣鼓巷站。",
            "从南锣鼓巷站出站后可直接步行进入胡同核心游览区。",
        ],
        "duration": "约 35 至 45 分钟",
        "note": "该段同样使用公开线路信息作为兜底内容，等待有效高德 key 后可替换为实时规划结果。",
    },
]

FALLBACK_FOODS = {
    "颐和园": [
        {
            "name": "听鹂馆",
            "type": "中式宫廷风味",
            "address": "颐和园景区万寿山昆明湖区域内",
            "reason": "景区内辨识度最高的老牌餐厅之一，适合安排午餐或休息。",
            "source": "公开地图数据与常见景区信息整理",
        },
        {
            "name": "北华涮肉小院(西苑店)",
            "type": "北京铜锅涮肉",
            "address": "西苑交通枢纽周边",
            "reason": "靠近颐和园 / 西苑片区，适合游览后吃一顿偏北京风味的正餐。",
            "source": "OpenStreetMap 周边餐饮 POI",
        },
        {
            "name": "云海肴",
            "type": "云南菜",
            "address": "西苑商圈周边",
            "reason": "口味相对轻松，适合不想吃过重口味的游客。",
            "source": "OpenStreetMap 周边餐饮 POI",
        },
    ],
    "南锣鼓巷": [
        {
            "name": "马沙拉之香印度餐厅",
            "type": "印度菜",
            "address": "南锣鼓巷周边胡同片区",
            "reason": "辨识度高，适合作为胡同片区的异国风味选择。",
            "source": "OpenStreetMap 周边餐饮 POI",
        },
        {
            "name": "馅老满",
            "type": "北方饺子 / 家常菜",
            "address": "安定门内大街",
            "reason": "距离南锣鼓巷不远，适合希望吃到更稳妥北方口味的游客。",
            "source": "OpenStreetMap 周边餐饮 POI",
        },
        {
            "name": "Cafe Zarah",
            "type": "咖啡简餐",
            "address": "鼓楼东大街",
            "reason": "适合下午茶、拍照和短暂停留。",
            "source": "OpenStreetMap 周边餐饮 POI",
        },
    ],
}

DAY_PLAN = [
    ("08:30", "天安门东集合", "先逛天安门广场和周边中轴线区域，控制步行节奏，避免上午体力消耗过快。"),
    ("10:30", "前往颐和园", "按地铁换乘方案出发，中午前后进入颐和园，优先浏览长廊、昆明湖和佛香阁视角。"),
    ("13:00", "颐和园午餐", "可优先考虑听鹂馆或西苑片区餐厅，用餐后继续补充体力。"),
    ("15:30", "前往南锣鼓巷", "从北宫门方向返回地铁，转线去南锣鼓巷，减少路面交通不确定性。"),
    ("16:30", "胡同漫游与小吃", "在南锣鼓巷、帽儿胡同、鼓楼东大街一带慢逛，补充咖啡或小吃。"),
    ("19:00", "晚餐与返程", "根据现场排队情况在胡同周边用餐，随后从南锣鼓巷站返程。"),
]


def try_amap_probe() -> dict[str, str]:
    key = os.environ.get("AMAP_MAPS_API_KEY", "").strip()
    if not key:
        return {"status": "missing", "message": "环境变量 AMAP_MAPS_API_KEY 未设置。"}

    url = (
        "https://restapi.amap.com/v3/place/text?keywords="
        + quote("天安门 地铁站")
        + "&city="
        + quote("北京")
        + "&offset=1&page=1&key="
        + key
    )

    try:
        with urlopen(url, timeout=12) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except URLError as exc:
        return {"status": "error", "message": f"调用高德 REST 失败: {exc}"}

    if payload.get("status") == "1":
        return {"status": "ok", "message": "高德 REST 可用，可继续替换为实时规划结果。"}

    return {
        "status": "blocked",
        "message": (
            "高德 REST 当前不可用: "
            f"{payload.get('info', 'unknown')}"
            f" ({payload.get('infocode', 'n/a')})"
        ),
    }


def render_subway_text(amap_status: dict[str, str]) -> str:
    lines = [
        "北京一日游地铁方案",
        "=",
        f"高德接口状态: {amap_status['message']}",
        "",
    ]
    for segment in FALLBACK_SUBWAY_SEGMENTS:
        lines.append(segment["title"])
        lines.append("-" * len(segment["title"]))
        lines.append(f"概述: {segment['summary']}")
        lines.append(f"预计耗时: {segment['duration']}")
        for index, step in enumerate(segment["steps"], start=1):
            lines.append(f"{index}. {step}")
        lines.append(f"备注: {segment['note']}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def render_food_text() -> str:
    lines = ["景点周边美食", "="]
    for location, items in FALLBACK_FOODS.items():
        lines.append("")
        lines.append(location)
        lines.append("-" * len(location))
        for index, item in enumerate(items, start=1):
            lines.append(f"{index}. {item['name']} | {item['type']}")
            lines.append(f"   地址: {item['address']}")
            lines.append(f"   推荐理由: {item['reason']}")
            lines.append(f"   数据来源: {item['source']}")
    return "\n".join(lines).strip() + "\n"


def render_overview_text() -> str:
    lines = [
        "北京一日游总览",
        "=",
        "路线主线: 天安门东 -> 颐和园 -> 南锣鼓巷",
        "适合人群: 第一次到北京、希望兼顾地标与胡同体验的游客",
        "出行建议: 全程以地铁为主，必要时在颐和园东宫门段补充短途地面接驳",
        "",
        "时间安排",
        "-",
    ]
    for time_label, title, detail in DAY_PLAN:
        lines.append(f"{time_label} {title}: {detail}")
    return "\n".join(lines).strip() + "\n"


def render_html(amap_status: dict[str, str]) -> str:
    status_class = "ok" if amap_status["status"] == "ok" else "warn"
    subway_cards = []
    for segment in FALLBACK_SUBWAY_SEGMENTS:
        steps = "".join(f"<li>{html.escape(step)}</li>" for step in segment["steps"])
        subway_cards.append(
            f"""
            <section class=\"card route-card\">
              <p class=\"eyebrow\">地铁路线</p>
              <h3>{html.escape(segment['title'])}</h3>
              <p>{html.escape(segment['summary'])}</p>
              <p class=\"meta\">预计耗时: {html.escape(segment['duration'])}</p>
              <ol>{steps}</ol>
              <p class=\"note\">{html.escape(segment['note'])}</p>
            </section>
            """.strip()
        )

    food_sections = []
    for location, items in FALLBACK_FOODS.items():
        food_cards = []
        for item in items:
            food_cards.append(
                f"""
                <article class=\"food-card\">
                  <h4>{html.escape(item['name'])}</h4>
                  <p class=\"meta\">{html.escape(item['type'])}</p>
                  <p>{html.escape(item['reason'])}</p>
                  <p class=\"small\">地址: {html.escape(item['address'])}</p>
                  <p class=\"small\">来源: {html.escape(item['source'])}</p>
                </article>
                """.strip()
            )
        food_sections.append(
            f"""
            <section class=\"card\">
              <p class=\"eyebrow\">周边美食</p>
              <h3>{html.escape(location)}</h3>
              <div class=\"food-grid\">{''.join(food_cards)}</div>
            </section>
            """.strip()
        )

    timeline_items = []
    for time_label, title, detail in DAY_PLAN:
        timeline_items.append(
            f"""
            <div class=\"timeline-item\">
              <div class=\"timeline-time\">{html.escape(time_label)}</div>
              <div class=\"timeline-body\">
                <h4>{html.escape(title)}</h4>
                <p>{html.escape(detail)}</p>
              </div>
            </div>
            """.strip()
        )

    return dedent(
        f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
          <meta charset="UTF-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1.0" />
          <title>北京一日游攻略</title>
          <style>
            :root {{
              --bg: #f2ecdf;
              --paper: rgba(255, 251, 245, 0.86);
              --ink: #1d1b18;
              --muted: #6a6258;
              --accent: #a33a2b;
              --accent-2: #2f5d50;
              --line: rgba(29, 27, 24, 0.1);
              --shadow: 0 22px 60px rgba(60, 34, 20, 0.12);
            }}
            * {{ box-sizing: border-box; }}
            body {{
              margin: 0;
              font-family: "Noto Serif SC", "Source Han Serif SC", serif;
              color: var(--ink);
              background:
                radial-gradient(circle at top left, rgba(163, 58, 43, 0.20), transparent 36%),
                radial-gradient(circle at bottom right, rgba(47, 93, 80, 0.18), transparent 30%),
                linear-gradient(135deg, #efe5d2, #f7f3ea 45%, #e8ddcc);
              min-height: 100vh;
            }}
            .shell {{
              max-width: 1180px;
              margin: 0 auto;
              padding: 40px 20px 72px;
            }}
            .hero {{
              position: relative;
              overflow: hidden;
              padding: 36px;
              border: 1px solid rgba(255,255,255,0.55);
              border-radius: 28px;
              background: linear-gradient(140deg, rgba(255,251,245,0.95), rgba(250,243,230,0.82));
              box-shadow: var(--shadow);
            }}
            .hero::after {{
              content: "";
              position: absolute;
              inset: 16px;
              border: 1px solid rgba(163, 58, 43, 0.12);
              border-radius: 20px;
              pointer-events: none;
            }}
            .eyebrow {{
              margin: 0 0 10px;
              font-size: 13px;
              letter-spacing: 0.24em;
              text-transform: uppercase;
              color: var(--accent);
            }}
            h1, h2, h3, h4, p {{ margin-top: 0; }}
            h1 {{
              max-width: 10ch;
              margin-bottom: 16px;
              font-size: clamp(38px, 7vw, 74px);
              line-height: 0.98;
            }}
            .lead {{
              max-width: 700px;
              font-size: 18px;
              line-height: 1.75;
              color: var(--muted);
            }}
            .status {{
              display: inline-flex;
              align-items: center;
              gap: 10px;
              margin-top: 10px;
              padding: 10px 14px;
              border-radius: 999px;
              font-size: 14px;
              background: rgba(255,255,255,0.72);
              border: 1px solid rgba(29,27,24,0.08);
            }}
            .status.ok {{ color: var(--accent-2); }}
            .status.warn {{ color: var(--accent); }}
            .grid {{
              display: grid;
              grid-template-columns: repeat(12, minmax(0, 1fr));
              gap: 18px;
              margin-top: 24px;
            }}
            .card {{
              grid-column: span 12;
              padding: 24px;
              border-radius: 24px;
              background: var(--paper);
              border: 1px solid rgba(255,255,255,0.56);
              box-shadow: var(--shadow);
              backdrop-filter: blur(10px);
            }}
            .route-card {{ grid-column: span 6; }}
            .timeline {{
              display: grid;
              gap: 16px;
            }}
            .timeline-item {{
              display: grid;
              grid-template-columns: 92px 1fr;
              gap: 16px;
              padding: 16px 0;
              border-top: 1px solid var(--line);
            }}
            .timeline-item:first-child {{ border-top: 0; padding-top: 0; }}
            .timeline-time {{
              font-size: 24px;
              color: var(--accent);
            }}
            .food-grid {{
              display: grid;
              grid-template-columns: repeat(3, minmax(0, 1fr));
              gap: 14px;
            }}
            .food-card {{
              min-height: 100%;
              padding: 18px;
              border-radius: 18px;
              background: rgba(255,255,255,0.62);
              border: 1px solid rgba(29,27,24,0.06);
            }}
            .meta, .small, .note {{ color: var(--muted); }}
            ol {{ padding-left: 22px; line-height: 1.8; }}
            @media (max-width: 900px) {{
              .route-card {{ grid-column: span 12; }}
              .food-grid {{ grid-template-columns: 1fr; }}
              .timeline-item {{ grid-template-columns: 1fr; gap: 8px; }}
            }}
          </style>
        </head>
        <body>
          <main class="shell">
            <section class="hero">
              <p class="eyebrow">Beijing One Day Trip</p>
              <h1>北京一日游 出行攻略</h1>
              <p class="lead">以天安门东、颐和园、南锣鼓巷为主线，优先使用地铁串联城市地标、皇家园林与胡同街区，兼顾换乘效率和游玩节奏。</p>
              <div class="status {status_class}">{html.escape(amap_status['message'])}</div>
            </section>
            <section class="grid">
              <section class="card">
                <p class="eyebrow">全天安排</p>
                <h2>时间轴</h2>
                <div class="timeline">{''.join(timeline_items)}</div>
              </section>
              {''.join(subway_cards)}
              {''.join(food_sections)}
            </section>
          </main>
        </body>
        </html>
        """
    ).strip() + "\n"


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    amap_status = try_amap_probe()

    subway_text = render_subway_text(amap_status)
    foods_text = render_food_text()
    overview_text = render_overview_text()
    html_text = render_html(amap_status)

    write_file(OUTPUT_DIR / "subtask_try.txt", subway_text)
    write_file(OUTPUT_DIR / "subway_trip.txt", subway_text)
    write_file(OUTPUT_DIR / "location_foods.txt", foods_text)
    write_file(OUTPUT_DIR / "01_trip_overview.txt", overview_text)
    write_file(OUTPUT_DIR / "02_subway_routes.txt", subway_text)
    write_file(OUTPUT_DIR / "03_food_recommendations.txt", foods_text)
    write_file(OUTPUT_DIR / "index.html", html_text)


if __name__ == "__main__":
    main()