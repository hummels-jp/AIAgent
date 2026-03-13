import re

# 文件组列表
file_groups = [
    # junction_detail系列
    ("junction_detail.html", "junction_detail_en.html", "junction_detail_ja.html"),
    # lane_detail系列
    ("lane_detail.html", "lane_detail_en.html", "lane_detail_ja.html"),
    # pedestrian_detail系列
    ("pedestrian_detail.html", "pedestrian_detail_en.html", "pedestrian_detail_ja.html"),
    # road_centerline_detail系列
    ("road_centerline_detail.html", "road_centerline_detail_en.html", "road_centerline_detail_ja.html"),
    # road_marking_detail系列
    ("road_marking_detail.html", "road_marking_detail_en.html", "road_marking_detail_ja.html"),
    # traffic_signal_detail系列
    ("traffic_signal_detail.html", "traffic_signal_detail_en.html", "traffic_signal_detail_ja.html")
]

# 语言切换CSS
lang_switcher_css = """        /* 语言切换悬浮标签样式 */
        .lang-switcher {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
            display: flex;
            gap: 10px;
        }

        .lang-btn {
            padding: 8px 16px;
            border: 2px solid white;
            background: rgba(255, 255, 255, 0.9);
            color: #667eea;
            border-radius: 20px;
            cursor: pointer;
            font-weight: 600;
            font-size: 14px;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
        }

        .lang-btn:hover {
            background: white;
            color: #667eea;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        }

        .lang-btn.active {
            background: white;
            color: #667eea;
            font-weight: bold;
        }"""

def clean_and_add_language_switcher(filename, active_index, base_filename, en_filename, ja_filename):
    """清理旧的语言切换代码并添加新的"""
    try:
        # 读取文件
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()

        # 移除旧的语言切换CSS
        content = re.sub(r'/\* 语言切换悬浮标签样式 \*/.*?\.lang-btn\.active \{[^}]+\}', '', content, flags=re.DOTALL)
        
        # 移除旧的语言切换HTML
        content = re.sub(r'<!-- 语言切换悬浮标签 -->.*?</div>\s*', '', content, flags=re.DOTALL)
        
        # 移除英文版的语言切换注释
        content = re.sub(r'<!-- Language switcher floating buttons -->.*?</div>\s*', '', content, flags=re.DOTALL)
        
        # 移除日文版的语言切换注释
        content = re.sub(r'<!-- 言語切り替えフローティングボタン -->.*?</div>\s*', '', content, flags=re.DOTALL)

        # 清理多余的空行
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)

        # 构建语言切换HTML
        active_classes = ['', '', '']
        active_classes[active_index] = 'active'

        lang_html = f"""    <!-- 语言切换悬浮标签 -->
    <div class="lang-switcher">
        <a href="{base_filename}" class="lang-btn {active_classes[0]}" title="中文">中文</a>
        <a href="{en_filename}" class="lang-btn {active_classes[1]}" title="English">English</a>
        <a href="{ja_filename}" class="lang-btn {active_classes[2]}" title="日本語">日本語</a>
    </div>
"""

        # 在</style>前添加CSS
        if '</style>' in content:
            content = content.replace('</style>', lang_switcher_css + '\n    </style>')

        # 在<body>后添加HTML
        if '<body>' in content:
            content = content.replace('<body>', '<body>\n' + lang_html)

        # 写回文件
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"[OK] Processed: {filename}")
        return True

    except Exception as e:
        print(f"[FAIL] {filename}: {e}")
        return False

# 处理所有文件组
success_count = 0
total_count = 0

for group in file_groups:
    zh_file, en_file, ja_file = group

    # 处理中文版
    total_count += 1
    if clean_and_add_language_switcher(zh_file, 0, zh_file, en_file, ja_file):
        success_count += 1

    # 处理英文版
    total_count += 1
    if clean_and_add_language_switcher(en_file, 1, zh_file, en_file, ja_file):
        success_count += 1

    # 处理日文版
    total_count += 1
    if clean_and_add_language_switcher(ja_file, 2, zh_file, en_file, ja_file):
        success_count += 1

print(f"\n处理完成: {success_count}/{total_count} 个文件成功")
