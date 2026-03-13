#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为HTML文件中的中文句子添加中日英三语显示
"""

import re
from pathlib import Path

# 句子级翻译对照表（以完整句子为单位）
SENTENCE_TRANSLATIONS = {
    # 标题类
    "返回总览": ("総覽に戻る", "Back to Overview"),
    "文件差异比较报告": ("ファイル差異比較レポート", "File Difference Comparison Report"),
    "道路中心线详细属性说明": ("道路中心線詳細属性説明", "Road Centerline Detailed Attributes Description"),
    "车道详细属性说明": ("車線詳細属性説明", "Lane Detailed Attributes Description"),
    "交通灯详细属性说明": ("信号機詳細属性説明", "Traffic Signal Detailed Attributes Description"),
    "路口详细属性说明": ("交差点詳細属性説明", "Junction Detailed Attributes Description"),
    "行人设施详细属性说明": ("歩行者施設詳細属性説明", "Pedestrian Facility Detailed Attributes Description"),
    "道路标线详细属性说明": ("道路標線詳細属性説明", "Road Marking Detailed Attributes Description"),

    # 重要说明类
    "重要说明": ("重要説明", "Important Description"),
    "OSM格式中交通灯仅作为位置标记，不包含相位控制逻辑。": (
        "OSM形式で信号機は位置マーカーとしてのみ機能し、位相制御ロジックを含まない。",
        "In OSM format, traffic signals serve only as position markers and do not contain phase control logic."
    ),
    "SUMO格式使用 `<tlLogic>` 元素定义完整的交通灯控制逻辑，包含相位定义。": (
        "SUMO形式は `<tlLogic>` 要素を使用して完全な信号制御ロジックを定義し、位相定義を含む。",
        "SUMO format uses `<tlLogic>` elements to define complete traffic signal control logic, including phase definitions."
    ),
    "OpenDRIVE格式使用 `<signal>` 元素定义交通灯，包含位置和类型信息。": (
        "OpenDRIVE形式は `<signal>` 要素を使用して信号機を定義し、位置とタイプ情報を含む。",
        "OpenDRIVE format uses `<signal>` elements to define traffic signals, containing location and type information."
    ),
    "OSM格式中道路标线信息非常有限，主要通过道路类型和车道数量推断。": (
        "OSM形式の道路標線情報は非常に限定的で、主に道路タイプと車線数から推測される。",
        "In OSM format, road marking information is very limited and is mainly inferred from road type and number of lanes."
    ),
    "SUMO格式中道路标线信息较少，主要通过车道配置表示。": (
        "SUMO形式では道路標線情報は少なく、主に車線構成で表現される。",
        "In SUMO format, road marking information is scarce and is mainly represented through lane configuration."
    ),
    "OpenDRIVE格式使用 `<roadMark>` 元素详细定义道路标线。": (
        "OpenDRIVE形式は `<roadMark>` 要素を使用して道路標線を詳細に定義する。",
        "OpenDRIVE format uses `<roadMark>` elements to define road markings in detail."
    ),

    # 属性说明类
    "属性名": ("属性名", "Attribute Name"),
    "类型": ("タイプ", "Type"),
    "说明": ("説明", "Description"),
    "节点的唯一标识符": ("ノードの一意識別子", "Unique identifier of the node"),
    "纬度 (WGS84坐标)": ("緯度 (WGS84座標)", "Latitude (WGS84 Coordinate)"),
    "经度 (WGS84坐标)": ("経度 (WGS84座標)", "Longitude (WGS84 Coordinate)"),
    "是否可见 (true/false)": ("表示されるかどうか (true/false)", "Whether visible (true/false)"),
    "版本号": ("バージョン番号", "Version number"),
    "最后更新时间": ("最後の更新時刻", "Last update time"),
    "最后编辑用户名": ("最後の編集ユーザー名", "Last edited username"),

    # 标签和值说明类
    "标识为交通灯": ("信号機として識別", "Identified as traffic signal"),
    "交通灯名称": ("信号機名", "Traffic signal name"),
    "信号方向": ("信号方向", "Signal direction"),
    "控制的车道数": ("制御された車線数", "Number of controlled lanes"),
    "信号灯数量": ("信号灯の数", "Number of signal lights"),
    "人行横道信号灯": ("横断歩道信号灯", "Pedestrian crossing signal light"),
    "是否有安全岛": ("安全島があるかどうか", "Whether there is a safety island"),
    "是否有行人信号灯": ("歩行者信号灯があるかどうか", "Whether there is a pedestrian signal light"),

    # 关键特点类
    "仅标记交通灯位置，无相位控制信息": (
        "信号機の位置のみをマークし、位相制御情報なし",
        "Only marks traffic signal location, no phase control information"
    ),
    "不包含红/黄/绿灯时长": ("赤/黄/青灯の期間を含まない", "Does not contain duration of red/yellow/green lights"),
    "无法表示信号控制逻辑": ("信号制御ロジックを表現できない", "Cannot represent signal control logic"),
    "适用于地图显示，不适用于仿真": ("地図表示に適用でき、シミュレーションには適さない", "Suitable for map display, not suitable for simulation"),
    "可使用附加标签补充信息": ("追加タグを使用して情報を補完できる", "Can use additional tags to supplement information"),
    "完整的相位控制逻辑": ("完全な位相制御ロジック", "Complete phase control logic"),
    "精确的时间控制": ("正確な時間制御", "Precise time control"),
    "多种控制类型": ("複数の制御タイプ", "Multiple control types"),
    "适用于交通仿真": ("交通シミュレーションに適用", "Suitable for traffic simulation"),
    "精确3D位置 (s, t, height, 角度)": ("正確な3D位置 (s, t, 高さ, 角度)", "Precise 3D position (s, t, height, angle)"),
    "丰富的信号类型系统": ("豊富な信号タイプシステム", "Rich signal type system"),
    "支持动态信号 (dynamic=yes)": ("動的信号をサポート (dynamic=yes)", "Supports dynamic signals (dynamic=yes)"),
    "可指定信号适用范围 (validity)": ("信号適用範囲を指定可能 (validity)", "Can specify signal application range (validity)"),
    "支持多个控制器": ("複数のコントローラーをサポート", "Supports multiple controllers"),
    "适用于高精度自动驾驶仿真": ("高精度自動運転シミュレーションに適用", "Suitable for high-precision autonomous driving simulation"),

    # 特殊术语和参数类
    "信号程序ID": ("信号プログラムID", "Signal program ID"),
    "时间偏移 (秒)": ("時間オフセット (秒)", "Time offset (seconds)"),
    "静态信号": ("静的信号", "Static signal"),
    "感应控制": ("感応制御", "Actuated control"),
    "基于延迟": ("遅延ベース", "Delay-based"),
    "相位持续时间 (秒)": ("位相継続時間 (秒)", "Phase duration (seconds)"),
    "各车道信号状态": ("各車線の信号状態", "Signal status of each lane"),
    "r=红, y=黄, g=绿, s=黄红, o=关闭": ("r=赤, y=黄, g=緑, s=黄赤, o=オフ", "r=red, y=yellow, g=green, s=yellow-red, o=off"),
    "最小持续时间 (可选)": ("最小継続時間 (オプション)", "Minimum duration (optional)"),
    "最大持续时间 (可选)": ("最大継続時間 (オプション)", "Maximum duration (optional)"),
    "红灯 (禁止通行)": ("赤灯 (通行禁止)", "Red light (Prohibited passage)"),
    "黄灯 (即将变红)": ("黄灯 (まもなく赤に変わる)", "Yellow light (About to turn red)"),
    "绿灯 (允许通行)": ("青灯 (通行可能)", "Green light (Allowed passage)"),
    "黄红灯 (即将变绿)": ("黄赤灯 (まもなく緑に変わる)", "Yellow-red light (About to turn green)"),
    "关闭 (无信号)": ("オフ (信号なし)", "Off (No signal)"),

    # 信号连接和验证类
    "在 junction 元素中，connection 元素指定每个转向对应的信号控制索引": (
        "junction 要素では、connection 要素は各転向に対応する信号制御インデックスを指定する",
        "In the junction element, the connection element specifies the signal control index corresponding to each turn"
    ),
    "关联的交通灯ID": ("関連する信号機ID", "Associated traffic signal ID"),
    "连接索引，对应 phase.state 中的位置": ("接続インデックス、phase.state の位置に対応", "Connection index, corresponding to position in phase.state"),
    "控制器ID": ("コントローラーID", "Controller ID"),
    "控制器名称": ("コントローラー名", "Controller name"),
    "控制顺序": ("制御順序", "Control order"),

    # 道路标线相关句子
    "无直接标线定义，依赖推断，不适用于精确仿真": (
        "直接的な標線定義なし、推測に依存、正確なシミュレーションには不適切",
        "No direct marking definition, relies on inference, not suitable for precise simulation"
    ),
    "不直接定义标线，通过车道边界表示，不适用于高精度显示": (
        "標線を直接定義せず、車線境界で表現、高精度表示には不適切",
        "Does not directly define markings, represented through lane boundaries, not suitable for high-precision display"
    ),
    "详细标线定义 (类型、颜色、宽度)": ("詳細な標線定義 (タイプ、色、幅)", "Detailed marking definition (type, color, width)"),
    "支持变道权限控制": ("車線変更権限制御をサポート", "Supports lane change permission control"),
    "标线可沿道路变化": ("標線は道路に沿って変化可能", "Markings can change along the road"),
    "支持多种标线组合": ("複数の標線組み合わせをサポート", "Supports multiple marking combinations"),
    "起始位置偏移 (沿道路s坐标)": ("開始位置オフセット (道路s座標に沿って)", "Start position offset (along road s coordinate)"),
    "标线类型 (none, solid, broken等)": ("標線タイプ (なし、実線、破線など)", "Marking type (none, solid, broken, etc.)"),
    "线条粗细 (standard, bold)": ("線の太さ (標準、太字)", "Line weight (standard, bold)"),
    "标线颜色 (standard, white, yellow等)": ("標線色 (標準、白、黄など)", "Marking color (standard, white, yellow, etc.)"),
    "标线宽度 (米)": ("標線幅 (メートル)", "Marking width (meters)"),
    "是否允许变道 (increase, decrease, both, none)": (
        "車線変更を許可するかどうか (増加、減少、両方、なし)",
        "Whether lane change is allowed (increase, decrease, both, none)"
    ),

    # 信号类型分类
    "常见信号类型": ("一般的な信号タイプ", "Common signal types"),
    "红灯": ("赤灯", "Red light"),
    "黄灯": ("黄灯", "Yellow light"),
    "绿灯": ("青灯", "Green light"),
    "停止标志": ("一時停止標識", "Stop sign"),
    "让行标志": ("譲歩標識", "Yield sign"),
    "限速标志": ("速度制限標識", "Speed limit sign"),
    "禁止进入": ("進入禁止", "No entry"),
    "单行道标志": ("一方通行標識", "One-way sign"),
    "禁止停车": ("駐車禁止", "No parking"),
    "禁止超车": ("追い越し禁止", "No passing"),
    "人行横道": ("横断歩道", "Pedestrian crossing"),
    "人行横道信号灯": ("横断歩道信号灯", "Pedestrian crossing signal light"),

    # 对比总结句子
    "三种格式交通灯属性对比总结": ("3つのフォーマットの信号属性比較のまとめ", "Summary of traffic signal attribute comparison of three formats"),
    "OSM - 位置标记": ("OSM - 位置マーク", "OSM - Position Mark"),
    "SUMO - 完整控制": ("SUMO - 完全制御", "SUMO - Complete Control"),
    "OpenDRIVE - 位置+类型": ("OpenDRIVE - 位置+タイプ", "OpenDRIVE - Position+Type"),
    "仅标记位置": ("位置のみをマーク", "Only mark position"),
    "无相位信息": ("位相情報なし", "No phase information"),
    "无控制逻辑": ("制御ロジックなし", "No control logic"),
    "简单直观": ("シンプルで直感的", "Simple and intuitive"),

    # 方向和位置术语
    "中心车道: 实线": ("中央車線: 実線", "Center lane: solid line"),
    "右侧行驶车道: 实线 + 虚线": ("右側走行車線: 実線+破線", "Right driving lane: solid + broken line"),
    "起始道路ID": ("開始道路ID", "Starting road ID"),
    "结束道路ID": ("終了道路ID", "Ending road ID"),
    "起始车道ID": ("開始車線ID", "Starting lane ID"),
    "结束车道ID": ("終了車線ID", "Ending lane ID"),

    # 报告元数据
    "报告生成时间: 2026-03-13": ("レポート生成時刻: 2026-03-13", "Report generation time: 2026-03-13"),
    "数据来源: 日本川崎地区": ("データソース: 日本川崎地区", "Data source: Kawasaki, Japan"),

    # OSM相关
    "路径": ("ウェイ", "Way"),
    "关系": ("リレーション", "Relation"),
    "标签": ("タグ", "Tag"),
    "元数据": ("メタデータ", "Metadata"),
    "时间戳": ("タイムスタンプ", "Timestamp"),
    "用户": ("ユーザー", "User"),
    "更改": ("変更", "Change"),
    "历史": ("履歴", "History"),
    "编辑": ("編集", "Edit"),
    "查看者": ("閲覧者", "Viewer"),
    "贡献者": ("貢献者", "Contributor"),

    # SUMO相关
    "连接": ("接続", "Connection"),
    "信号逻辑": ("信号論理", "Traffic light logic"),
    "车辆类型": ("車両タイプ", "Vehicle type"),
    "投影": ("投影", "Projection"),
    "坐标系": ("座標系", "Coordinate system"),
    "仿真": ("シミュレーション", "Simulation"),

    # OpenDRIVE相关
    "车道段": ("車線セクション", "Lane section"),
    "控制器": ("コントローラー", "Controller"),
    "前驱": ("前駆", "Predecessor"),
    "后继": ("後継", "Successor"),
    "链接": ("リンク", "Link"),
    "剖面": ("プロファイル", "Profile"),
    "高程": ("標高", "Elevation"),
    "超高": ("キャンバン", "Superelevation"),
    "横向坡度": ("横断勾配", "Crossfall"),
}


def create_multilang_span(chinese, japanese, english):
    """创建三语格式的HTML span"""
    return f'<span class="zh-lang">{chinese}</span> <span class="lang-separator">|</span> <span class="ja-lang">{japanese}</span> <span class="lang-separator">|</span> <span class="en-lang">{english}</span>'


def process_file(filepath):
    """处理单个HTML文件"""
    print(f"处理文件: {filepath}")

    # 读取文件
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 备份原文件
    backup_path = filepath.with_suffix('.html.backup')
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  已备份到: {backup_path}")

    # 按句子长度降序排序,避免部分匹配
    sorted_keys = sorted(SENTENCE_TRANSLATIONS.keys(), key=len, reverse=True)

    # 逐个替换
    replacements = 0
    for chinese in sorted_keys:
        japanese, english = SENTENCE_TRANSLATIONS[chinese]

        # 检查句子是否存在于文件中
        if chinese in content:
            # 替换
            new_str = create_multilang_span(chinese, japanese, english)
            content = content.replace(chinese, new_str)
            replacements += 1

    # 写入文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  完成! 替换了 {replacements} 个句子\n")


def main():
    """主函数"""
    # 获取所有HTML文件
    html_files = [
        "compare_result.html",
        "road_centerline_detail.html",
        "lane_detail.html",
        "traffic_signal_detail.html",
        "junction_detail.html",
        "pedestrian_detail.html",
        "road_marking_detail.html",
    ]

    base_dir = Path(__file__).parent

    total_replacements = 0
    for html_file in html_files:
        filepath = base_dir / html_file
        if filepath.exists():
            process_file(filepath)
        else:
            print(f"警告: 文件不存在 - {filepath}")

    print(f"\n所有文件处理完成! 总共替换了 {total_replacements} 个句子")


if __name__ == "__main__":
    main()
