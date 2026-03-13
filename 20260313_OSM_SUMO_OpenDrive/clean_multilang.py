#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理HTML文件中的日文和英文翻译,只保留中文
"""

import re
from pathlib import Path


def clean_multilang(content):
    """清理三语格式,只保留中文"""
    # 方法1: 使用正则表达式直接提取中文span内容
    # 匹配模式: <span class="zh-lang">中文</span> <span class="lang-separator">|</span> ...
    
    # 先处理标准的三语格式
    pattern1 = r'<span class="zh-lang">([^<]+)</span>\s*<span class="lang-separator">\|</span>\s*<span class="ja-lang">[^<]*</span>\s*<span class="lang-separator">\|</span>\s*<span class="en-lang">[^<]*</span>'
    
    def replacer1(match):
        return match.group(1)  # 只返回中文内容
    
    content = re.sub(pattern1, replacer1, content)
    
    # 方法2: 清理可能残留的其他语言span
    # 移除日文span
    content = re.sub(r'<span class="ja-lang">[^<]*</span>', '', content)
    # 移除英文span
    content = re.sub(r'<span class="en-lang">[^<]*</span>', '', content)
    # 移除分隔符
    content = re.sub(r'<span class="lang-separator">\|</span>', '', content)
    
    # 清理多余空格
    content = re.sub(r'\s+', ' ', content)
    
    return content


def process_file(filepath):
    """处理单个HTML文件"""
    print(f"处理文件: {filepath}")

    # 读取文件
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 清理三语格式
    cleaned_content = clean_multilang(content)

    # 备份原文件
    backup_path = filepath.with_suffix('.html.clean_backup')
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  已备份到: {backup_path}")

    # 写入清理后的文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(cleaned_content)

    # 统计清理数量
    original_count = content.count('<span class="zh-lang">')
    cleaned_count = cleaned_content.count('<span class="zh-lang">')
    print(f"  完成! 清理了 {original_count - cleaned_count} 处三语标记\n")


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

    for html_file in html_files:
        filepath = base_dir / html_file
        if filepath.exists():
            process_file(filepath)
        else:
            print(f"警告: 文件不存在 - {filepath}")

    print("\n所有文件清理完成! 只保留了中文内容")


if __name__ == "__main__":
    main()
