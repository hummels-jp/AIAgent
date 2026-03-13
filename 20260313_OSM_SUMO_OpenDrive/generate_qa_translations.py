#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QA.html 简化翻译脚本
生成英文版和日文版的基本结构
"""

from pathlib import Path

def main():
    base_dir = Path(__file__).parent

    # 读取原始文件
    with open(base_dir / 'QA.html', 'r', encoding='utf-8') as f:
        content = f.read()

    # 生成英文版
    en_content = content
    en_content = en_content.replace('lang="zh-CN"', 'lang="en"')
    en_content = en_content.replace('QA - 常见问题解答', 'QA - Frequently Asked Questions')
    en_content = en_content.replace('OSM/SUMO/OpenDRIVE - 常见问题解答', 'OSM/SUMO/OpenDRIVE - Frequently Asked Questions')
    en_content = en_content.replace('Microsoft YaHei', 'Segoe UI')

    with open(base_dir / 'QA_en.html', 'w', encoding='utf-8') as f:
        f.write(en_content)
    print('[OK] Generated: QA_en.html')

    # 生成日文版
    ja_content = content
    ja_content = ja_content.replace('lang="zh-CN"', 'lang="ja"')
    ja_content = ja_content.replace('QA - 常见问题解答', 'QA - よくある質問')
    ja_content = ja_content.replace('OSM/SUMO/OpenDRIVE - 常见问题解答', 'OSM/SUMO/OpenDRIVE - よくある質問')
    ja_content = ja_content.replace('Microsoft YaHei', 'Hiragino Sans, Meiryo')

    with open(base_dir / 'QA_ja.html', 'w', encoding='utf-8') as f:
        f.write(ja_content)
    print('[OK] Generated: QA_ja.html')

    print('\n[OK] All translated files generated successfully!')
    print('\nNote: This is a basic translation with only titles changed.')
    print('For full content translation, please use professional translation services.')

if __name__ == '__main__':
    main()
