import re
from pathlib import Path

# 额外的翻译
extra_translations = {
    'SUMO网络XML': 'SUMO Network XML',
    'SUMO网络': 'SUMO Network',
    '左侧驶配置(lefthand="true")': 'Left-hand traffic configuration (lefthand="true")',
    'OpenDRIVE (SUMO)': 'OpenDRIVE (SUMO)',
    'OpenDRIVE (DGM/VIRES)': 'OpenDRIVE (DGM/VIRES)',
}

# 日文额外翻译
ja_extra = {
    'SUMO网络XML': 'SUMOネットワークXML',
    'SUMO网络': 'SUMOネットワーク',
    '左侧驶配置(lefthand="true")': '左側通行設定（lefthand="true"）',
    'OpenDRIVE (SUMO)': 'OpenDRIVE (SUMO)',
    'OpenDRIVE (DGM/VIRES)': 'OpenDRIVE (DGM/VIRES)',
}

# 读取英文版文件并修复
en_file = Path('compare_result_en.html')
with open(en_file, 'r', encoding='utf-8') as f:
    content = f.read()

for zh, en in extra_translations.items():
    content = content.replace(zh, en)

with open(en_file, 'w', encoding='utf-8') as f:
    f.write(content)
print('[OK] Fixed compare_result_en.html')

# 同样处理其他英文文件
for file in ['road_centerline_detail_en.html', 'lane_detail_en.html', 'traffic_signal_detail_en.html', 'junction_detail_en.html', 'pedestrian_detail_en.html', 'road_marking_detail_en.html']:
    fpath = Path(file)
    if fpath.exists():
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        for zh, en in extra_translations.items():
            content = content.replace(zh, en)
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'[OK] Fixed {file}')

# 日文额外翻译
for file in ['compare_result_ja.html', 'road_centerline_detail_ja.html', 'lane_detail_ja.html', 'traffic_signal_detail_ja.html', 'junction_detail_ja.html', 'pedestrian_detail_ja.html', 'road_marking_detail_ja.html']:
    fpath = Path(file)
    if fpath.exists():
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        for zh, ja in ja_extra.items():
            content = content.replace(zh, ja)
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'[OK] Fixed {file}')

print('\n[OK] All files fixed!')
