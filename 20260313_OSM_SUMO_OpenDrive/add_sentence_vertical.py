#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为HTML文件中的中文句子添加中日英三语显示
三句上下排列,使用不同颜色
"""

import re
from pathlib import Path

# 完整的句子级翻译对照表
SENTENCE_TRANSLATIONS = {
    # 文件差异比较报告相关
    "文件差异比较报告": ("ファイル差分比較報告", "File Difference Comparison Report"),
    "格式转换分析": ("フォーマット変換分析", "Format Conversion Analysis"),
    "数据转换流程": ("データ変換フロー", "Data Conversion Flow"),
    "SUMO网络": ("SUMOネットワーク", "SUMO Network"),
    "转换工具": ("変換ツール", "Conversion Tool"),
    "生成时间": ("生成時間", "Generation Time"),
    "文件大小": ("ファイルサイズ", "File Size"),
    "行数": ("行数", "Line Count"),
    "格式": ("フォーマット", "Format"),
    "主要特点": ("主な特徴", "Main Features"),
    "原始地理数据,包含完整地图信息": ("生の地理データ、完全な地図情報を含む", "Raw geographic data with complete map information"),
    "使用WGS84坐标系 (lat/lon)": ("WGS84座標系を使用", "Uses WGS84 coordinate system"),
    "包含node、way、relation元素": ("node、way、relation要素を含む", "Contains node, way, relation elements"),
    "丰富的元数据:版本、时间戳、用户信息": ("豊富なメタデータ:バージョン、タイムスタンプ、ユーザー情報", "Rich metadata: version, timestamp, user info"),
    "标签系统: highway、name等属性": ("タグシステム: highway、nameなどの属性", "Tag system: highway, name, etc."),
    "用于地图编辑和数据存储": ("地図編集とデータストレージに使用", "Used for map editing and data storage"),
    "由SUMO netconvert工具转换而来": ("SUMO netconvertツールで変換", "Converted from SUMO netconvert"),
    "使用UTM Zone 54投影坐标系": ("UTM Zone 54投影座標系を使用", "Uses UTM Zone 54 projected coordinate system"),
    "交通仿真信息:车道、速度、车辆限制": ("交通シミュレーション情報:車線、速度、車両制限", "Traffic simulation info: lanes, speed, vehicle restrictions"),
    "左侧行驶配置(lefthand=\"true\")": ("左側通行設定 (lefthand=\"true\")", "Left-hand traffic configuration"),
    "用于交通流模拟和管理": ("交通流シミュレーションと管理に使用", "Used for traffic flow simulation and management"),
    "符合OpenDRIVE 1.4国际标准": ("OpenDRIVE 1.4国際標準に準拠", "Complies with OpenDRIVE 1.4 international standard"),
    "最高精度的道路几何信息": ("最高精度の道路幾何情報", "Highest precision road geometry"),
    "包含道路长度、形状、高程剖面": ("道路長さ、形状、縦断プロファイルを含む", "Contains road length, shape, elevation profile"),
    "详细的车道配置和标线信息": ("詳細な車線構成とマーキング情報", "Detailed lane configuration and marking info"),
    "复杂的道路连接和路口表示": ("複雑な道路接続と交差点表現", "Complex road connections and junction representation"),
    "用于ADAS和自动驾驶测试": ("ADASと自動運転テストに使用", "Used for ADAS and autonomous driving testing"),
    "详细对比表": ("詳細比較表", "Detailed Comparison Table"),
    "主要用途": ("主要用途", "Main Purpose"),
    "真实地理数据存储": ("実地理データストレージ", "Real geographic data storage"),
    "交通流仿真": ("交通流シミュレーション", "Traffic flow simulation"),
    "驾驶仿真(ADAS测试)": ("運転シミュレーション (ADASテスト)", "Driving simulation (ADAS testing)"),
    "坐标系": ("座標系", "Coordinate System"),
    "几何精度": ("幾何精度", "Geometry Precision"),
    "节点坐标": ("ノード座標", "Node coordinates"),
    "车道形状": ("車線形状", "Lane shape"),
    "高精度道路几何": ("高精度道路幾何", "High-precision road geometry"),
    "数据标准化": ("データ標準化", "Data Standardization"),
    "OSM规范": ("OSM仕様", "OSM specification"),
    "SUMO规范": ("SUMO仕様", "SUMO specification"),
    "OpenDRIVE标准": ("OpenDRIVE標準", "OpenDRIVE standard"),
    "应用场景": ("適用シナリオ", "Application Scenario"),
    "地图编辑": ("地図編集", "Map editing"),
    "交通管理": ("交通管理", "Traffic management"),
    "自动驾驶测试": ("自動運転テスト", "Autonomous driving testing"),
    "主要元素": ("主要要素", "Main Elements"),
    "元数据丰富度": ("メタデータ充実度", "Metadata richness"),
    "仿真精度": ("シミュレーション精度", "Simulation precision"),
    "地图要素分类比较": ("地図要素分類比較", "Map Elements Classification Comparison"),
    "道路中心线": ("道路中心線", "Road Centerline"),
    "使用 way 元素表示道路,通过 nd 引用节点序列来定义道路几何形状": ("way要素で道路を表現し、ndでノードシーケンスを参照して道路形状を定義", "Uses way element to represent roads, defining geometry via node sequences"),
    "关键属性": ("キー属性", "Key Attributes"),
    "highway 标签: 道路类型 (primary, residential, tertiary等)": ("highwayタグ: 道路タイプ (primary, residential, tertiary等)", "highway tag: road type (primary, residential, tertiary, etc.)"),
    "name 标签: 道路名称(多语言支持)": ("nameタグ: 道路名称(多言語サポート)", "name tag: road name (multilingual)"),
    "oneway 标签: 单向通行标识": ("onewayタグ: 一方通行識別子", "oneway tag: one-way indicator"),
    "maxspeed 标签: 限速信息": ("maxspeedタグ: 速度制限情報", "maxspeed tag: speed limit info"),
    "lanes 标签: 车道数量": ("lanesタグ: 車線数", "lanes tag: lane count"),
    "使用 edge 元素表示道路边,包含几何形状和连接信息": ("edge要素で道路辺を表現し、幾何形状と接続情報を含む", "Uses edge element representing road edges with geometry and connection info"),
    "id: 边的标识符": ("id: 辺の識別子", "id: edge identifier"),
    "from/to: 起止节点ID": ("from/to: 始終ノードID", "from/to: start/end node IDs"),
    "shape: 几何形状坐标序列": ("shape: 幾何形状座標シーケンス", "shape: geometry coordinate sequence"),
    "length: 道路长度(米)": ("length: 道路長さ(メートル)", "length: road length (meters)"),
    "priority: 道路优先级": ("priority: 道路優先度", "priority: road priority"),
    "numLanes: 车道数量": ("numLanes: 車線数", "numLanes: number of lanes"),
    "使用 road 元素表示道路,包含高精度的几何和拓扑信息": ("road要素で道路を表現し、高精度の幾何とトポロジ情報を含む", "Uses road element with high-precision geometry and topology"),
    "junction: 所属路口ID": ("junction: 所属交差点ID", "junction: junction ID"),
    "planView/geometry: 道路几何(支持直线、曲线、螺旋线)": ("planView/geometry: 道路幾何(直線、曲線、スパイラルをサポート)", "planView/geometry: road geometry (supports line, curve, spiral)"),
    "link: 道路连接关系 (predecessor/successor)": ("link: 道路接続関係 (predecessor/successor)", "link: road connection (predecessor/successor)"),
    "elevationProfile: 高程剖面": ("elevationProfile: 縦断プロファイル", "elevationProfile: elevation profile"),
    "车道": ("車線", "Lanes"),
    "通过 lanes 标签简单表示车道数量,没有详细的车道几何信息": ("lanesタグで車線数を簡単に表現、詳細な車線幾何情報なし", "Uses lanes tag for simple lane count, no detailed lane geometry"),
    "特点": ("特徴", "Features"),
    "仅记录车道总数,不区分具体车道": ("車線総数のみ記録、具体的な車線を区別しない", "Records only total lane count, no specific lanes"),
    "无法表示车道宽度变化": ("車線幅の変化を表現できない", "Cannot represent lane width changes"),
    "不包含车道连接信息": ("車線接続情報を含まない", "No lane connection info"),
    "无法表示特殊车道(如公交专用道)": ("特殊車線(バス専用道など)を表現できない", "Cannot represent special lanes (e.g., bus-only lanes)"),
    "使用 lane 元素详细描述每条车道,包含车道级别信息": ("lane要素で各車線を詳細に記述、車道レベル情報を含む", "Uses lane element for detailed lane description with lane-level info"),
    "index: 车道索引号": ("index: 車線インデックス番号", "index: lane index"),
    "speed: 车道限速(m/s)": ("speed: 車線速度制限(m/s)", "speed: lane speed limit (m/s)"),
    "length: 车道长度": ("length: 車線長さ", "length: lane length"),
    "width: 车道宽度": ("width: 車線幅", "width: lane width"),
    "allow/disallow: 允许/禁止的车辆类型": ("allow/disallow: 許可/禁止される車両タイプ", "allow/disallow: allowed/prohibited vehicle types"),
    "shape: 车道几何形状": ("shape: 車線幾何形状", "shape: lane geometry"),
    "车道信息嵌套在 laneSection 中,支持最复杂的车道配置": ("車線情報はlaneSectionにネスト、最も複雑な車線構成をサポート", "Lane info nested in laneSection, supports most complex lane config"),
    "left/center/right: 左/中/右车道分组": ("left/center/right: 左/中/右車線グループ", "left/center/right: left/center/right lane groups"),
    "width: 沿道路的宽度变化函数": ("width: 道路に沿った幅変化関数", "width: width variation function along road"),
    "roadMark: 标线类型 (实线、虚线、颜色)": ("roadMark: マーキングタイプ (実線、破線、色)", "roadMark: marking type (solid, broken, color)"),
    "speed: 速度限制曲线": ("speed: 速度制限曲線", "speed: speed limit curve"),
    "link: 车道链接关系 (laneLink)": ("link: 車線リンク関係 (laneLink)", "link: lane link relation (laneLink)"),
    "交通灯": ("信号機", "Traffic Signals"),
    "使用 node 元素配合 highway=traffic_signals 标签标记交通灯位置": ("node要素とhighway=traffic_signalsタグで信号機位置をマーク", "Uses node element with highway=traffic_signals tag to mark traffic light position"),
    "仅标记位置,无相位信息": ("位置のみマーク、位相情報なし", "Marks only position, no phase info"),
    "支持名称(name标签)": ("名称サポート(nameタグ)", "Supports name (name tag)"),
    "不包含信号控制逻辑": ("信号制御ロジックを含まない", "No signal control logic"),
    "示例": ("例", "Example"),
    "使用 tlLogic 元素定义交通灯逻辑,包含完整的相位信息": ("tlLogic要素で信号機ロジックを定義、完全な位相情報を含む", "Uses tlLogic element to define traffic light logic with complete phase info"),
    "id: 交通灯ID": ("id: 信号機ID", "id: traffic light ID"),
    "programID: 信号程序ID": ("programID: 信号プログラムID", "programID: signal program ID"),
    "phase: 相位定义(红/黄/绿状态)": ("phase: 位相定義(赤/黄/緑状態)", "phase: phase definition (red/yellow/green states)"),
    "duration: 相位持续时间": ("duration: 位相継続時間", "duration: phase duration"),
    "offset: 时间偏移": ("offset: 時間オフセット", "offset: time offset"),
    "使用 signals 元素定义信号,通常位于 junction 中": ("signals要素で信号を定義、通常はjunction内", "Uses signals element to define signals, usually within junction"),
    "s: 沿道路的纵向位置": ("s: 道路に沿った縦方向位置", "s: longitudinal position along road"),
    "t: 横向偏移": ("t: 横方向オフセット", "t: lateral offset"),
    "dynamic: 是否动态信号": ("dynamic: 動的信号か", "dynamic: dynamic signal or not"),
    "country: 国家代码": ("country: 国コード", "country: country code"),
    "type: 信号类型": ("type: 信号タイプ", "type: signal type"),
    "路口": ("交差点", "Intersections/Junctions"),
    "通过多个 way 相交的节点隐式表示路口,没有专门的路口元素": ("複数のwayが交差するノードで暗黙的に交差点を表現、専用の交差点要素なし", "Implicitly represents junction via intersecting way nodes, no dedicated junction element"),
    "通过道路汇聚表示路口": ("道路の集約で交差点を表現", "Represents junction via road convergence"),
    "可能使用 junction 标签标记路口类型": ("junctionタグで交差点タイプをマークする可能性", "May use junction tag to mark junction type"),
    "不包含转弯连接信息": ("ターン接続情報を含まない", "No turn connection info"),
    "不定义转弯限制": ("ターン制限を定義しない", "No turn restrictions defined"),
    "使用 junction 元素明确定义路口,包含完整的连接和转向信息": ("junction要素で明示的に交差点を定義、完全な接続とターン情報を含む", "Explicitly defines junction using junction element with complete connection and turn info"),
    "type: 路口类型 (priority, traffic_light等)": ("type: 交差点タイプ (priority, traffic_light等)", "type: junction type (priority, traffic_light, etc.)"),
    "incLanes: 进入车道列表": ("incLanes: 進入車線リスト", "incLanes: incoming lane list"),
    "intLanes: 内部车道列表": ("intLanes: 内部車線リスト", "intLanes: internal lane list"),
    "shape: 路口形状": ("shape: 交差点形状", "shape: junction shape"),
    "logic: 逻辑连接(connection元素)": ("logic: ロジック接続(connection要素)", "logic: logic connection (connection elements)"),
    "connection: 道路连接(incomingRoad, connectingRoad)": ("connection: 道路接続(incomingRoad, connectingRoad)", "connection: road connection (incomingRoad, connectingRoad)"),
    "laneLink: 车道级链接": ("laneLink: 車道レベルリンク", "laneLink: lane-level link"),
    "controller: 信号控制器": ("controller: 信号コントローラー", "controller: signal controller"),
    "junctionGroup: 路口分组": ("junctionGroup: 交差点グループ", "junctionGroup: junction group"),
    "行人设施": ("歩行者施設", "Pedestrian Facilities"),
    "使用 highway=footway 等标签表示人行道、步道等": ("highway=footway等のタグで歩道、小径などを表現", "Uses highway=footway tags to represent sidewalks, paths, etc."),
    "footway: 人行道": ("footway: 歩道", "footway: sidewalk"),
    "path: 小径": ("path: 小径", "path: path"),
    "crossing: 人行横道": ("crossing: 横断歩道", "crossing: crosswalk"),
    "sidewalk: 人行道(作为道路属性)": ("sidewalk: 歩道(道路属性として)", "sidewalk: sidewalk (as road attribute)"),
    "可能包含表面类型、宽度等信息": ("表面タイプ、幅などの情報を含む可能性", "May include surface type, width, etc."),
    "支持 pedestrian 元素类型,定义行人专用区域": ("pedestrian要素タイプをサポート、歩行者専用エリアを定義", "Supports pedestrian element type, defines pedestrian-only areas"),
    "allow: 允许pedestrian通行": ("allow: pedestrian通行を許可", "allow: allow pedestrian"),
    "width: 人行道宽度": ("width: 歩道幅", "width: sidewalk width"),
    "speed: 行人速度": ("speed: 歩行者速度", "speed: pedestrian speed"),
    "walkingareas: 行人区域(可选)": ("walkingareas: 歩行者エリア(オプション)", "walkingareas: pedestrian area (optional)"),
    "通过 lane type=\"sidewalk\" 或 type=\"walking\" 表示行人设施": ("lane type=\"sidewalk\"またはtype=\"walking\"で歩行者施設を表現", "Represents pedestrian facilities via lane type=\"sidewalk\" or type=\"walking\""),
    "objects: 行人相关设施(长椅、路灯等)": ("objects: 歩行者関連施設(ベンチ、街灯など)", "objects: pedestrian-related facilities (benches, streetlights, etc.)"),
    "支持障碍物表示": ("障害物表現をサポート", "Supports obstacle representation"),
    "道路标线": ("道路マーキング", "Road Markings"),
    "标线信息有限,主要通过道路类型和车道数量推断": ("マーキング情報は限定的、主に道路タイプと車線数から推測", "Marking info is limited, mainly inferred from road type and lane count"),
    "通常不直接表示标线": ("通常はマーキングを直接表現しない", "Usually doesn't directly represent markings"),
    "可能使用特定标签标记特殊标线": ("特定のタグで特殊マーキングをマークする可能性", "May use specific tags to mark special markings"),
    "依赖道路类型和车道数": ("道路タイプと車線数に依存", "Depends on road type and lane count"),
    "无标线颜色和样式信息": ("マーキングの色とスタイル情報なし", "No marking color and style info"),
    "标线信息较少,主要通过车道配置表示": ("マーキング情報は少なく、主に車線構成で表現", "Marking info is scarce, mainly represented via lane configuration"),
    "不直接定义标线": ("マーキングを直接定義しない", "Doesn't directly define markings"),
    "通过车道边界隐式表示": ("車線境界で暗黙的に表現", "Implicitly represented via lane boundaries"),
    "依赖仿真引擎渲染标线": ("シミュレーションエンジンがマーキングをレンダリング", "Simulation engine renders markings"),
    "无法自定义标线样式": ("マーキングスタイルをカスタマイズできない", "Cannot customize marking style"),
    "使用 roadMark 元素详细定义道路标线": ("roadMark要素で道路マーキングを詳細に定義", "Uses roadMark element to define road markings in detail"),
    "sOffset: 沿道路的起始位置": ("sOffset: 道路に沿った開始位置", "sOffset: start position along road"),
    "type: 标线类型 (none, solid, broken等)": ("type: マーキングタイプ (none, solid, broken等)", "type: marking type (none, solid, broken, etc.)"),
    "weight: 线条粗细(standard, bold)": ("weight: 線の太さ(standard, bold)", "weight: line weight (standard, bold)"),
    "color: 标线颜色(standard, white, yellow等)": ("color: マーキング色(standard, white, yellow等)", "color: marking color (standard, white, yellow, etc.)"),
    "width: 标线宽度": ("width: マーキング幅", "width: marking width"),
    "laneChange: 是否允许变道 (increase, decrease, both, none)": ("laneChange: 車線変更を許可か (increase, decrease, both, none)", "laneChange: lane change allowed (increase, decrease, both, none)"),
    "地图要素支持度对比矩阵": ("地図要素サポート度比較マトリックス", "Map Element Support Comparison Matrix"),
    "地图要素": ("地図要素", "Map Element"),
    "说明": ("説明", "Description"),
    "车道级别信息": ("車道レベル情報", "Lane-level Info"),
    "OSM仅记录车道数,net和xodr支持车道几何": ("OSMは車線数のみ記録、netとxodrは車道幾何をサポート", "OSM only records lane count, net and xodr support lane geometry"),
    "车道宽度变化": ("車道幅の変化", "Lane Width Variation"),
    "xodr支持沿道路的宽度变化函数": ("xodrは道路に沿った幅変化関数をサポート", "xodr supports width variation function along road"),
    "交通灯相位": ("信号機位相", "Traffic Signal Phase"),
    "net支持完整相位逻辑,xodr支持位置和类型": ("netは完全な位相ロジックをサポート、xodrは位置とタイプをサポート", "net supports complete phase logic, xodr supports position and type"),
    "路口拓扑": ("交差点トポロジ", "Junction Topology"),
    "net和xodr明确定义路口连接": ("netとxodrは交差点接続を明確に定義", "net and xodr explicitly define junction connections"),
    "转弯限制": ("ターン制限", "Turn Restriction"),
    "OSM通过标签间接表示,net和xodr明确定义": ("OSMはタグで間接的に表現、netとxodrは明確に定義", "OSM indirectly via tags, net and xodr explicitly define"),
    "高程信息": ("縦断情報", "Elevation Info"),
    "仅xodr支持elevationProfile": ("xodrのみがelevationProfileをサポート", "Only xodr supports elevationProfile"),
    "道路几何曲线": ("道路幾何曲線", "Road Geometry Curves"),
    "xodr支持arc、spiral等精确曲线": ("xodrはarc、spiral等の精密曲線をサポート", "xodr supports precise curves like arc, spiral"),
    "速度限制": ("速度制限", "Speed Limit"),
    "OSM用标签,net用属性,xodr用曲线": ("OSMはタグ、netは属性、xodrは曲線を使用", "OSM uses tags, net uses attributes, xodr uses curves"),
    "元数据丰富度": ("メタデータ充実度", "Metadata Richness"),
    "OSM有最丰富的编辑历史和属性": ("OSMは最も豊富な編集履歴と属性を持つ", "OSM has richest editing history and attributes"),
    "net适用于交通流,xodr适用于驾驶仿真": ("netは交通流に、xodrは運転シミュレーションに適用", "net适用于交通流,xodr适用于驾驶仿真"),
    "图例": ("凡例", "Legend"),
    "完全支持": ("完全サポート", "Full Support"),
    "良好支持": ("良好サポート", "Good Support"),
    "最佳": ("ベスト", "Best"),
    "部分支持": ("部分サポート", "Partial Support"),
    "不支持": ("サポート外", "Not Supported"),
    "不适用": ("該当なし", "Not Applicable"),
    "报告生成时间": ("レポート生成時間", "Report Generation Time"),
    "数据来源: 日本川崎地区": ("データソース: 日本川崎地区", "Data Source: Kawasaki Area, Japan"),
    
    # 道路中心线详细属性相关
    "返回总览": ("概要に戻る", "Back to Overview"),
    "详细属性对比": ("詳細属性比較", "Detailed Attribute Comparison"),
    "三种格式道路中心线特点概览": ("3つのフォーマット道路中心線特徴概要", "Overview of Three Format Road Centerline Features"),
    "OSM (OpenStreetMap)": ("OSM (OpenStreetMap)", "OSM (OpenStreetMap)"),
    "使用 way 元素表示道路": ("way要素で道路を表現", "Uses way element for roads"),
    "WGS84 地理坐标系": ("WGS84 地理座標系", "WGS84 geographic coordinate system"),
    "丰富的元数据和标签": ("豊富なメタデータとタグ", "Rich metadata and tags"),
    "适合地图编辑和显示": ("地図編集と表示に適切", "Suitable for map editing and display"),
    "节点序列定义道路形状": ("ノードシーケンスで道路形状を定義", "Node sequence defines road shape"),
    "SUMO (kawasaki.net.xml)": ("SUMO (kawasaki.net.xml)", "SUMO (kawasaki.net.xml)"),
    "使用 edge 元素表示道路": ("edge要素で道路を表現", "Uses edge element for roads"),
    "UTM 投影坐标系": ("UTM 投影座標系", "UTM projected coordinate system"),
    "包含车道和速度信息": ("車線と速度情報を含む", "Contains lane and speed info"),
    "适合交通流仿真": ("交通流シミュレーションに適切", "Suitable for traffic simulation"),
    "明确的起止节点连接": ("明確な始終ノード接続", "Clear start/end node connections"),
    "OpenDRIVE (kawasaki.xodr)": ("OpenDRIVE (kawasaki.xodr)", "OpenDRIVE (kawasaki.xodr)"),
    "高精度几何曲线": ("高精度幾何曲線", "High-precision geometry curves"),
    "支持复杂道路几何": ("複雑な道路幾何をサポート", "Supports complex road geometry"),
    "适合驾驶仿真": ("運転シミュレーションに適切", "Suitable for driving simulation"),
    "支持道路连接关系": ("道路接続関係をサポート", "Supports road connections"),
    "OSM 格式 - way 要素": ("OSM フォーマット - way要素", "OSM Format - way Element"),
    "在 OpenStreetMap 中,道路中心线使用 way 元素表示,通过引用一系列节点 (nd) 来定义道路的几何形状。": ("OpenStreetMapでは、道路中心線はway要素で表現され、一連のノード(nd)を参照して道路の幾何形状を定義します。", "In OpenStreetMap, road centerlines are represented using way elements, defining road geometry by referencing a sequence of nodes (nd)."),
    "way 要素本身不存储坐标,坐标存储在被引用的 node 要素中。": ("way要素自体は座標を保存せず、座標は参照されるnode要素に保存されます。", "The way element itself does not store coordinates; coordinates are stored in the referenced node elements."),
    "way 要素属性": ("way要素属性", "way Element Attributes"),
    "类型": ("タイプ", "Type"),
    "唯一的道路标识符,在整个 OSM 数据集中必须唯一": ("道路の唯一識別子、OSMデータセット全体で一意である必要あり", "Unique road identifier, must be unique throughout the OSM dataset"),
    "是否可见,值为 \"true\" 或 \"false\"。通常为 \"true\"": ("表示されるかどうか、値は\"true\"または\"false\"。通常は\"true\"", "Visibility, value is \"true\" or \"false\". Usually \"true\""),
    "版本号,每次编辑后递增": ("バージョン番号、編集ごとに増加", "Version number, increments with each edit"),
    "最后一次编辑的变更集ID": ("最後の編集の変更セットID", "Changeset ID of last edit"),
    "时间戳 (ISO 8601 格式)": ("タイムスタンプ (ISO 8601形式)", "Timestamp (ISO 8601 format)"),
    "最后一次编辑的用户名": ("最後の編集のユーザー名", "Username of last edit"),
    "用户的唯一标识符": ("ユーザーの唯一識別子", "Unique user identifier"),
    "道路相关标签 (Tags)": ("道路関連タグ (Tags)", "Road-related Tags"),
    "标签键": ("タグキー", "Tag Key"),
    "标签值示例": ("タグ値例", "Tag Value Example"),
    "道路类型,定义道路的等级和用途": ("道路タイプ、道路の等級と用途を定義", "Road type, defines road class and purpose"),
    "道路名称": ("道路名称", "Road name"),
    "英文名称": ("英語名称", "English name"),
    "日文名称": ("日本語名称", "Japanese name"),
    "日文罗马音": ("日本語ローマ字", "Japanese romaji"),
    "日文拉丁化名称": ("日本語ラテン文字名", "Japanese latinized name"),
    "车道数量": ("車道数", "Lane count"),
    "最高限速,单位 km/h (如: 40)": ("最高速度制限、単位 km/h (例: 40)", "Max speed, unit km/h (e.g., 40)"),
    "是否为单向道路": ("一方通行かどうか", "Whether it's a one-way road"),
    "道路编号或参考号": ("道路番号または参照番号", "Road reference number"),
    "路面类型": ("路面タイプ", "Surface type"),
    "自行车道类型": ("自転車道タイプ", "Cycleway type"),
    "数据来源 (如: Bing 2012)": ("データソース (例: Bing 2012)", "Data source (e.g., Bing 2012)"),
    "原始数据示例": ("生データ例", "Raw Data Example"),
    "以下是从 kawasaki.osm 文件中提取的道路中心线示例:": ("以下はkawasaki.osmファイルから抽出された道路中心線の例です:", "The following is an example of a road centerline extracted from the kawasaki.osm file:"),
    "道路 ID: 328724319 - 主要道路": ("道路ID: 328724319 - 主要道路", "Road ID: 328724319 - Main road"),
    "示例说明:": ("例の説明:", "Example Description:"),
    "这是一条名为\"尻手黒川道路\"的主要道路,编号为14,双向2车道,限速40km/h,铺装路面,带有自行车道。": ("これは「尻手黒川道路」という名前の主要道路で、番号は14、双方向2車線、速度制限40km/h、舗装路面、自転車道付きです。", "This is a main road named \"Shittekurokawa Road\" with number 14, two-way 2 lanes, speed limit 40km/h, paved surface, and includes bicycle lanes."),
    "SUMO 格式 - edge 要素": ("SUMO フォーマット - edge要素", "SUMO Format - edge Element"),
    "在 SUMO 中,道路中心线使用 edge 元素表示。": ("SUMOでは、道路中心線はedge要素で表現されます。", "In SUMO, road centerlines are represented using edge elements."),
    "edge 表示有向的连接,从起始节点到终止节点。": ("edgeは有向接続を表し、始点ノードから終点ノードへ向かいます。", "Edge represents a directed connection from start node to end node."),
    "双向道路用两个相反方向的 edge 表示(正ID和负ID)。": ("双方向道路は2つの逆方向のedgeで表されます(正IDと負ID)。", "Bidirectional roads are represented by two edges in opposite directions (positive ID and negative ID)."),
    "edge 要素属性": ("edge要素属性", "Edge Element Attributes"),
    "边的唯一标识符。负号表示相反方向(如: 124964556#0 / -124964556#0)": ("辺の唯一識別子。負号は逆方向を示す (例: 124964556#0 / -124964556#0)", "Unique edge identifier. Negative sign indicates opposite direction (e.g., 124964556#0 / -124964556#0)"),
    "起始节点的ID": ("始点ノードのID", "Start node ID"),
    "终止节点的ID": ("終点ノードのID", "End node ID"),
    "道路优先级,值越大优先级越高(1-15)": ("道路優先度、値が大きいほど優先度が高い (1-15)", "Road priority, higher value means higher priority (1-15)"),
    "道路类型,引用 type 定义(如: highway.unclassified, highway.primary)": ("道路タイプ、type定義を参照 (例: highway.unclassified, highway.primary)", "Road type, references type definition (e.g., highway.unclassified, highway.primary)"),
    "道路中心线的几何形状,用空格分隔的坐标点(x,y)序列": ("道路中心線の幾何形状、スペース区切りの座標点(x,y)シーケンス", "Road centerline geometry, sequence of coordinate points (x,y) separated by spaces"),
    "边的功能:normal(普通) 或 internal(路口内部连接)": ("辺の機能: normal(通常)またはinternal(交差点内部接続)", "Edge function: normal(regular) or internal(junction internal connection)"),
    "lane 子元素属性": ("lane子要素属性", "Lane Sub-element Attributes"),
    "车道的唯一标识符,格式为 \"edgeID_laneIndex\"": ("車道の唯一識別子、形式は\"edgeID_laneIndex\"", "Unique lane identifier, format is \"edgeID_laneIndex\""),
    "车道索引号,从0开始": ("車道インデックス番号、0から開始", "Lane index number, starts from 0"),
    "车道限速,单位 m/s (如: 13.89 = 50km/h)": ("車道速度制限、単位 m/s (例: 13.89 = 50km/h)", "Lane speed limit, unit m/s (e.g., 13.89 = 50km/h)"),
    "车道长度,单位米": ("車道長さ、単位メートル", "Lane length, unit meters"),
    "车道宽度,单位米(可选)": ("車道幅、単位メートル(オプション)", "Lane width, unit meters (optional)"),
    "车道中心线的几何形状坐标": ("車道中心線の幾何形状座標", "Lane centerline geometry coordinates"),
    "允许通行的车辆类型,用空格分隔(如: pedestrian delivery bicycle)": ("許可される車両タイプ、スペース区切り (例: pedestrian delivery bicycle)", "Allowed vehicle types, separated by spaces (e.g., pedestrian delivery bicycle)"),
    "禁止通行的车辆类型,用空格分隔": ("禁止される車両タイプ、スペース区切り", "Prohibited vehicle types, separated by spaces"),
    "以下是从 kawasaki.net.xml 文件中提取的道路中心线示例:": ("以下はkawasaki.net.xmlファイルから抽出された道路中心線の例です:", "The following is an example of a road centerline extracted from the kawasaki.net.xml file:"),
    "道路 ID: 124964556#0 - 未分类道路": ("道路ID: 124964556#0 - 未分類道路", "Road ID: 124964556#0 - Unclassified road"),
    "相反方向的道路": ("逆方向の道路", "Opposite direction road"),
    "服务道路": ("サービス道路", "Service road"),
    "展示了双向道路的表示方式,正ID和负ID分别表示相反方向。": ("双方向道路の表現方法を示しています、正IDと負IDでそれぞれ逆方向を表します。", "Shows how bidirectional roads are represented, positive ID and negative ID represent opposite directions respectively."),
    "服务道路仅允许行人、配送车辆和自行车通行,限速较低(5.56m/s ≈ 20km/h)。": ("サービス道路は歩行者、配送車、自転車のみ通行可能、速度制限が低い (5.56m/s ≈ 20km/h)。", "Service roads only allow pedestrians, delivery vehicles, and bicycles, with lower speed limits (5.56m/s ≈ 20km/h)."),
    "OpenDRIVE 格式 - road 元素": ("OpenDRIVE フォーマット - road要素", "OpenDRIVE Format - road Element"),
    "在 OpenDRIVE 中,道路中心线使用 road 元素表示。": ("OpenDRIVEでは、道路中心線はroad要素で表現されます。", "In OpenDRIVE, road centerlines are represented using road elements."),
    "OpenDRIVE 提供最高精度的道路几何描述,支持直线、圆弧、螺旋线等复杂曲线,符合驾驶仿真需求。": ("OpenDRIVEは最高精度の道路幾何記述を提供し、直線、円弧、スパイラル等の複雑な曲線をサポート、運転シミュレーションの要件に合致します。", "OpenDRIVE provides the highest precision road geometry description, supporting complex curves such as lines, arcs, and spirals, meeting driving simulation requirements."),
    "road 要素属性": ("road要素属性", "Road Element Attributes"),
    "道路名称": ("道路名称", "Road name"),
    "道路的总长度,单位米": ("道路の全長、単位メートル", "Total road length, unit meters"),
    "道路的唯一标识符": ("道路の唯一識別子", "Unique road identifier"),
    "所属路口的ID。-1表示不属于任何路口": ("所属交差点のID。-1は交差点に属さないことを示す", "Junction ID that the road belongs to. -1 means not belonging to any junction"),
    "road 子元素": ("road子要素", "Road Sub-elements"),
    "子元素": ("子要素", "Sub-element"),
    "定义道路连接关系 (predecessor/successor)": ("道路接続関係を定義 (predecessor/successor)", "Defines road connection relationships (predecessor/successor)"),
    "道路类型 (town, motorway, rural等)": ("道路タイプ (town, motorway, rural等)", "Road type (town, motorway, rural, etc.)"),
    "平面视图,包含道路的几何曲线": ("平面ビュー、道路の幾何曲線を含む", "Plan view, contains road geometry curves"),
    "高程剖面,描述道路的高度变化": ("縦断プロファイル、道路の高さ変化を記述", "Elevation profile, describes road elevation changes"),
    "横向剖面,描述道路的横坡": ("横断プロファイル、道路の横断勾配を記述", "Lateral profile, describes road crossfall"),
    "车道配置,包含车道定义和标线": ("車道構成、車道定義とマーキングを含む", "Lane configuration, includes lane definitions and markings"),
    "道路上的对象(如标志牌、障碍物等)": ("道路上のオブジェクト (標識、障害物等)", "Objects on road (e.g., signs, obstacles)"),
    "交通信号": ("交通信号", "Traffic signals"),
    "geometry 要素属性 (planView 子要素)": ("geometry要素属性 (planView子要素)", "geometry Element Attributes (planView sub-element)"),
    "该几何段的起始位置,单位米": ("その幾何セグメントの開始位置、単位メートル", "Start position of that geometry segment, unit meters"),
    "起始点的X坐标(UTM)": ("始点のX座標(UTM)", "X coordinate of start point (UTM)"),
    "起始点的Y坐标(UTM)": ("始点のY座標(UTM)", "Y coordinate of start point (UTM)"),
    "起始航向角(heading),弧度制": ("始点の航向角(heading)、ラジアン", "Starting heading angle, radians"),
    "该几何段的长度,单位米": ("その幾何セグメントの長さ、単位メートル", "Length of that geometry segment, unit meters"),
    "以下是从 kawasaki.xodr 文件中提取的道路中心线示例:": ("以下はkawasaki.xodrファイルから抽出された道路中心線の例です:", "The following is an example of a road centerline extracted from the kawasaki.xodr file:"),
    "道路 ID: 2873 - 城市道路": ("道路ID: 2873 - 都市道路", "Road ID: 2873 - Urban road"),
    "第一段: 直线": ("第一セグメント: 直線", "First segment: straight line"),
    "第二段: 三次多项式曲线 (paramPoly3)": ("第二セグメント: 三次多項式曲線 (paramPoly3)", "Second segment: cubic polynomial curve (paramPoly3)"),
    "第三段: 直线": ("第三セグメント: 直線", "Third segment: straight line"),
    "高程剖面": ("縦断プロファイル", "Elevation profile"),
    "车道配置": ("車道構成", "Lane configuration"),
    "展示了OpenDRIVE的高精度道路表示,包含三段几何(直线-曲线-直线),高程剖面,车道配置和标线信息。": ("OpenDRIVEの高精度道路表現を示しています、3つの幾何セグメント(直線-曲線-直線)、縦断プロファイル、車道構成、マーキング情報を含みます。", "Shows OpenDRIVE's high-precision road representation, including three geometry segments (straight-curve-straight), elevation profile, lane configuration, and marking information."),
    "支持paramPoly3三次多项式曲线,可精确描述道路转弯。": ("paramPoly3三次多項式曲線をサポートし、道路のターンを正確に記述できます。", "Supports paramPoly3 cubic polynomial curves, can accurately describe road turns."),
    "关键差异总结": ("重要な相違のまとめ", "Key Differences Summary"),
    "对比维度": ("比較ディメンション", "Comparison Dimension"),
    "元素类型": ("エレメントタイプ", "Element Type"),
    "几何精度": ("幾何精度", "Geometry Precision"),
    "车道信息": ("車道情報", "Lane Info"),
    "速度限制": ("速度制限", "Speed Limit"),
    "连接关系": ("接続関係", "Connection Relations"),
    "高程信息": ("縦断情報", "Elevation Info"),
    "元数据": ("メタデータ", "Metadata"),
    "编辑历史最丰富": ("編集履歴が最も豊富", "Richest editing history"),
    "仿真属性多": ("シミュレーション属性が多い", "Many simulation attributes"),
    "几何描述最详细": ("幾何記述が最も詳細", "Most detailed geometry description"),
}


def create_multilang_block(chinese, japanese, english):
    """创建三语上下排列的HTML块"""
    return f'''<div class="multilang-sentence">
    <div class="zh-sentence">{chinese}</div>
    <div class="ja-sentence">{japanese}</div>
    <div class="en-sentence">{english}</div>
</div>'''


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
            new_str = create_multilang_block(chinese, japanese, english)
            content = content.replace(chinese, new_str)
            replacements += 1

    # 写入文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  完成! 替换了 {replacements} 个句子\n")


def add_css_styles(filepath):
    """添加CSS样式到HTML文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 检查是否已经添加了样式
    if '.multilang-sentence' in content:
        print(f"  样式已存在,跳过")
        return

    # 找到style标签的结束位置
    style_end = content.find('</style>')
    if style_end == -1:
        print("  警告: 未找到style标签")
        return

    # 添加新的CSS样式
    css_to_add = '''
    /* 多语言句子样式 */
    .multilang-sentence {
        margin: 8px 0;
        line-height: 1.4;
    }
    
    .zh-sentence {
        color: #2c3e50;
        font-weight: 500;
        margin-bottom: 2px;
    }
    
    .ja-sentence {
        color: #e91e63;
        font-weight: 400;
        margin-bottom: 2px;
    }
    
    .en-sentence {
        color: #1e88e5;
        font-weight: 400;
        margin-bottom: 2px;
    }
'''

    # 在</style>之前插入CSS
    content = content[:style_end] + css_to_add + content[style_end:]

    # 写回文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  已添加CSS样式")


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
            add_css_styles(filepath)
        else:
            print(f"警告: 文件不存在 - {filepath}")

    print(f"\n所有文件处理完成! 总共替换了 {total_replacements} 个句子")


if __name__ == "__main__":
    main()
