import os
from pathlib import Path

# 定义中英文和日文翻译字典
translations = {
    'compare_result.html': {
        'en': {
            'title': 'File Difference Comparison Report - OSM / SUMO / OpenDRIVE',
            'h1': 'File Difference Comparison Report',
            'subtitle': 'OSM / SUMO / OpenDRIVE / DGM Format Conversion Analysis',
            'flow_title': 'Data Conversion Flow',
            'or': '— or —',
            'tool': 'Conversion Tools: SUMO netconvert 1.26.0 | DGM VIRES | Generated: 2026-03-04',
            'summary': {
                'osm': 'Original geographic data, contains complete map information',
                'net': 'Converted by SUMO netconvert tool',
                'xodr_sumo': 'Compliant with OpenDRIVE 1.4 international standard',
                'xodr_dgm': 'Compliant with OpenDRIVE 1.5 latest standard',
                'feature_title': 'Key Features',
                'coords_osm': 'WGS84 coordinate system (lat/lon)',
                'coords_net': 'UTM Zone 54 projected coordinate system',
                'coords_xodr': 'Direct geographic coordinates (large range)',
            },
            'elements': [
                {'name': 'Road Centerlines', 'icon': '🛣️', 'href': 'road_centerline_detail_en.html'},
                {'name': 'Lanes', 'icon': '🚗', 'href': 'lane_detail_en.html'},
                {'name': 'Traffic Lights', 'icon': '🚦', 'href': 'traffic_signal_detail_en.html'},
                {'name': 'Junctions', 'icon': '🔀', 'href': 'junction_detail_en.html'},
                {'name': 'Pedestrian Facilities', 'icon': '🚸', 'href': 'pedestrian_detail_en.html'},
                {'name': 'Road Markings', 'icon': '🛑', 'href': 'road_marking_detail_en.html'},
            ],
            'detail_btn': 'View Details →',
            'note_dgm': 'Note: dgm_kawasaki.xodr file covers a different geographic range than other files, so the file size and line count differences are normal. This file uses a larger geographic coordinate system and more detailed element definitions.',
            'note_dgm2': 'Note: dgm_kawasaki.xodr file covers a broader geographic area and contains more road and junction elements, so the file size and line count are significantly different. Additionally, this file uses the newer OpenDRIVE 1.5 standard, providing richer extended attributes.',
            'comparison_title': 'OpenDRIVE Files Detailed Comparison: SUMO vs DGM',
            'pros': 'Pros',
            'cons': 'Cons',
            'diff_summary': 'Key Differences Summary',
            'footer': 'Report Generated: 2026-03-13 | Data Source: Kawasaki Area, Japan',
        },
        'ja': {
            'title': 'ファイル差異比較レポート - OSM / SUMO / OpenDRIVE',
            'h1': 'ファイル差異比較レポート',
            'subtitle': 'OSM / SUMO / OpenDRIVE / DGM フォーマット変換解析',
            'flow_title': 'データ変換フロー',
            'or': '— または —',
            'tool': '変換ツール: SUMO netconvert 1.26.0 | DGM VIRES | 生成日時: 2026-03-04',
            'summary': {
                'osm': 'オリジナル地理データ、完全な地図情報を含む',
                'net': 'SUMO netconvertツールで変換',
                'xodr_sumo': 'OpenDRIVE 1.4国際規格に準拠',
                'xodr_dgm': 'OpenDRIVE 1.5最新規格に準拠',
                'feature_title': '主な特徴',
                'coords_osm': 'WGS84座標系 (lat/lon)',
                'coords_net': 'UTM Zone 54投影座標系',
                'coords_xodr': '直接地理座標（広範囲）',
            },
            'elements': [
                {'name': '道路中心線', 'icon': '🛣️', 'href': 'road_centerline_detail_ja.html'},
                {'name': '車線', 'icon': '🚗', 'href': 'lane_detail_ja.html'},
                {'name': '交通信号', 'icon': '🚦', 'href': 'traffic_signal_detail_ja.html'},
                {'name': '交差点', 'icon': '🔀', 'href': 'junction_detail_ja.html'},
                {'name': '歩行者施設', 'icon': '🚸', 'href': 'pedestrian_detail_ja.html'},
                {'name': '道路標識', 'icon': '🛑', 'href': 'road_marking_detail_ja.html'},
            ],
            'detail_btn': '詳細を表示 →',
            'note_dgm': '注意: dgm_kawasaki.xodrファイルは他のファイルとは異なる地理的範囲をカバーしているため、ファイルサイズと行数の違いは正常です。このファイルはより大きな地理座標系とより詳細な要素定義を使用しています。',
            'note_dgm2': '注意: dgm_kawasaki.xodrファイルはより広い地理的範囲をカバーし、より多くの道路と交差点要素を含んでいるため、ファイルサイズと行数が大幅に異なります。また、このファイルは新しいOpenDRIVE 1.5規格を使用しており、より豊富な拡張属性を提供します。',
            'comparison_title': 'OpenDRIVEファイル詳細比較: SUMO vs DGM',
            'pros': '長所',
            'cons': '短所',
            'diff_summary': '主な違いの要約',
            'footer': 'レポート生成日: 2026-03-13 | データソース: 日本川崎地区',
        }
    }
}

def translate_html_content(html_content, lang):
    """翻译HTML内容"""
    # 基本翻译
    translations_map = {
        '文件差异比较报告': 'File Difference Comparison Report' if lang == 'en' else 'ファイル差異比較レポート',
        'OSM / SUMO / OpenDRIVE / DGM 格式转换分析': 'OSM / SUMO / OpenDRIVE / DGM Format Conversion Analysis' if lang == 'en' else 'OSM / SUMO / OpenDRIVE / DGM フォーマット変換解析',
        '🔄 数据转换流程': '🔄 Data Conversion Flow' if lang == 'en' else '🔄 データ変換フロー',
        '转换工具': 'Conversion Tools' if lang == 'en' else '変換ツール',
        '生成时间': 'Generated' if lang == 'en' else '生成日時',
        '文件大小': 'File Size',
        '行数': 'Lines',
        '格式': 'Format',
        '主要特点': 'Key Features' if lang == 'en' else '主な特徴',
        '原始地理数据,包含完整地图信息': 'Original geographic data, contains complete map information' if lang == 'en' else 'オリジナル地理データ、完全な地図情報を含む',
        '由SUMO netconvert工具转换而来': 'Converted by SUMO netconvert tool' if lang == 'en' else 'SUMO netconvertツールで変換',
        '符合OpenDRIVE 1.4国际标准': 'Compliant with OpenDRIVE 1.4 international standard' if lang == 'en' else 'OpenDRIVE 1.4国際規格に準拠',
        '符合OpenDRIVE 1.5最新标准': 'Compliant with OpenDRIVE 1.5 latest standard' if lang == 'en' else 'OpenDRIVE 1.5最新規格に準拠',
        '详细对比表': 'Detailed Comparison Table' if lang == 'en' else '詳細比較テーブル',
        '特征': 'Feature',
        '主要用途': 'Primary Use',
        '坐标系': 'Coordinate System',
        '几何精度': 'Geometric Precision',
        '数据标准化': 'Data Standardization',
        '应用场景': 'Application Scenario',
        '道路数量': 'Number of Roads',
        '路口数量': 'Number of Junctions',
        '速度限制': 'Speed Limit',
        'surface元素': 'surface Element',
        'userData扩展': 'userData Extension',
        '元数据丰富度': 'Metadata Richness',
        '仿真精度': 'Simulation Precision',
        '真实地理数据存储': 'Real geographic data storage' if lang == 'en' else '実地理データ保存',
        '交通流仿真': 'Traffic flow simulation' if lang == 'en' else '交通流シミュレーション',
        '驾驶仿真 (ADAS测试)': 'Driving simulation (ADAS testing)' if lang == 'en' else '運転シミュレーション（ADASテスト）',
        '高精度地图/可视化': 'High-precision map/visualization' if lang == 'en' else '高精度地図/可視化',
        'WGS84 (lat/lon)': 'WGS84 (lat/lon)',
        'UTM Zone 54': 'UTM Zone 54',
        'UTM + offset': 'UTM + offset',
        '直接地理坐标 (大范围)': 'Direct geographic coordinates (large range)' if lang == 'en' else '直接地理座標（広範囲）',
        '节点坐标': 'Node coordinates' if lang == 'en' else 'ノード座標',
        '车道形状': 'Lane shape' if lang == 'en' else '車線形状',
        '高精度道路几何': 'High-precision road geometry' if lang == 'en' else '高精度道路幾何',
        '超高精度 (16位小数)': 'Ultra-high precision (16 decimal places)' if lang == 'en' else '超高精度（16桁小数）',
        'OSM规范': 'OSM Specification' if lang == 'en' else 'OSM仕様',
        'SUMO规范': 'SUMO Specification' if lang == 'en' else 'SUMO仕様',
        'OpenDRIVE 1.4标准': 'OpenDRIVE 1.4 Standard' if lang == 'en' else 'OpenDRIVE 1.4標準',
        'OpenDRIVE 1.5标准': 'OpenDRIVE 1.5 Standard' if lang == 'en' else 'OpenDRIVE 1.5標準',
        '地图编辑': 'Map editing' if lang == 'en' else '地図編集',
        '交通管理': 'Traffic management' if lang == 'en' else '交通管理',
        '自动驾驶测试': 'Autonomous driving testing' if lang == 'en' else '自動運転テスト',
        '高精度仿真/可视化': 'High-precision simulation/visualization' if lang == 'en' else '高精度シミュレーション/可視化',
        '有 (标签)': 'Yes (tag)',
        '有 (属性)': 'Yes (attribute)',
        '有 (曲线)': 'Yes (curve)',
        '无': 'No',
        '地图要素分类比较': 'Map Element Classification Comparison' if lang == 'en' else '地図要素分類比較',
        '查看详细属性': 'View Details' if lang == 'en' else '詳細を表示',
        'OpenDRIVE 文件详细对比: SUMO vs DGM': 'OpenDRIVE Files Detailed Comparison: SUMO vs DGM' if lang == 'en' else 'OpenDRIVEファイル詳細比較: SUMO vs DGM',
        'OpenDRIVE版本': 'OpenDRIVE Version',
        '优点': 'Pros' if lang == 'en' else '長所',
        '缺点': 'Cons' if lang == 'en' else '短所',
        '关键差异总结': 'Key Differences Summary' if lang == 'en' else '主な違いの要約',
        '差异项': 'Difference',
        '影响': 'Impact',
        '报告生成时间': 'Report Generated' if lang == 'en' else 'レポート生成日',
        '数据来源': 'Data Source',
        '日本川崎地区': 'Kawasaki Area, Japan' if lang == 'en' else '日本川崎地区',
    }
    
    # 替换文本
    for chinese, replacement in translations_map.items():
        html_content = html_content.replace(chinese, replacement)
    
    # 替换lang属性
    if lang == 'en':
        html_content = html_content.replace('lang="zh-CN"', 'lang="en"')
    elif lang == 'ja':
        html_content = html_content.replace('lang="zh-CN"', 'lang="ja"')
    
    return html_content

def generate_translated_files():
    """生成翻译文件"""
    base_dir = Path(__file__).parent
    
    # 处理主对比页面
    main_file = base_dir / 'compare_result.html'
    if main_file.exists():
        with open(main_file, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # 生成英文版
        en_content = translate_html_content(original_content, 'en')
        en_file = base_dir / 'compare_result_en.html'
        with open(en_file, 'w', encoding='utf-8') as f:
            f.write(en_content)
        print(f"[OK] Generated: {en_file.name}")
        
        # 生成日文版
        ja_content = translate_html_content(original_content, 'ja')
        ja_file = base_dir / 'compare_result_ja.html'
        with open(ja_file, 'w', encoding='utf-8') as f:
            f.write(ja_content)
        print(f"[OK] Generated: {ja_file.name}")
    
    # 处理详细页面
    detail_pages = [
        'road_centerline_detail.html',
        'lane_detail.html',
        'traffic_signal_detail.html',
        'junction_detail.html',
        'pedestrian_detail.html',
        'road_marking_detail.html'
    ]
    
    for page in detail_pages:
        page_file = base_dir / page
        if page_file.exists():
            with open(page_file, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # 生成英文版
            en_content = translate_html_content(original_content, 'en')
            # 替换链接
            en_content = en_content.replace('compare_result.html', 'compare_result_en.html')
            en_file = base_dir / page.replace('.html', '_en.html')
            with open(en_file, 'w', encoding='utf-8') as f:
                f.write(en_content)
            print(f"[OK] Generated: {en_file.name}")
            
            # 生成日文版
            ja_content = translate_html_content(original_content, 'ja')
            # 替换链接
            ja_content = ja_content.replace('compare_result.html', 'compare_result_ja.html')
            ja_file = base_dir / page.replace('.html', '_ja.html')
            with open(ja_file, 'w', encoding='utf-8') as f:
                f.write(ja_content)
            print(f"[OK] Generated: {ja_file.name}")

if __name__ == '__main__':
    generate_translated_files()
    print("\n[OK] All translated files generated successfully!")
