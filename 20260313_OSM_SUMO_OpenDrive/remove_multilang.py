import re
import os

def remove_multilang_from_file(filepath):
    """从HTML文件中移除日文和英文翻译,只保留中文"""
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # 处理嵌套的multilang-sentence块:只保留zh-sentence,移除ja-sentence和en-sentence
    def replace_multilang_block(match):
        block_content = match.group(0)
        # 提取zh-sentence的内容
        zh_match = re.search(r'<div class="zh-sentence">([^<]*)</div>', block_content)
        if zh_match:
            return zh_match.group(1)
        return block_content
    
    # 移除ja-sentence和en-sentence
    content = re.sub(r'<div class="ja-sentence">.*?</div>', '', content, flags=re.DOTALL)
    content = re.sub(r'<div class="en-sentence">.*?</div>', '', content, flags=re.DOTALL)
    
    # 清理multilang-sentence容器,只保留中文内容
    content = re.sub(r'<div class="multilang-sentence">\s*<div class="zh-sentence">([^<]*)</div>\s*</div>', r'\1', content, flags=re.DOTALL)
    
    # 移除空的多语言容器
    content = re.sub(r'<div class="multilang-sentence">\s*</div>', '', content)
    
    # 移除多语言span标签(保留内容)
    content = re.sub(r'<span class="term-multilang zh-lang">([^<]*)</span>', r'\1', content)
    content = re.sub(r'<span class="term-multilang ja-lang">.*?</span>', '', content, flags=re.DOTALL)
    content = re.sub(r'<span class="term-multilang en-lang">.*?</span>', '', content, flags=re.DOTALL)
    
    # 移除多语言句子CSS样式
    content = re.sub(r'\s*/\*\s*多语言句子样式\s*\*/.*?\.en-sentence.*?\}', '', content, flags=re.DOTALL)
    
    # 移除独立的zh-lang, ja-lang, en-lang span标签
    content = re.sub(r'<span class="zh-lang">([^<]*)</span>', r'\1', content)
    content = re.sub(r'<span class="ja-lang">.*?</span>', '', content, flags=re.DOTALL)
    content = re.sub(r'<span class="en-lang">.*?</span>', '', content, flags=re.DOTALL)
    
    # 移除语言分隔符
    content = re.sub(r'<span class="lang-separator">.*?</span>', '', content, flags=re.DOTALL)
    
    changes = len(original_content) - len(content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return changes

def main():
    html_files = [
        'compare_result.html',
        'road_centerline_detail.html',
        'lane_detail.html',
        'traffic_signal_detail.html',
        'junction_detail.html',
        'pedestrian_detail.html',
        'road_marking_detail.html'
    ]
    
    total_changes = 0
    
    for filename in html_files:
        filepath = f'd:/huqianqian_git/AIAgent/20260313_OSM_SUMO_OpenDrive/{filename}'
        
        # 创建备份
        backup_path = filepath.replace('.html', '.backup3')
        if not os.path.exists(backup_path):
            with open(filepath, 'r', encoding='utf-8') as f:
                with open(backup_path, 'w', encoding='utf-8') as bf:
                    bf.write(f.read())
        
        changes = remove_multilang_from_file(filepath)
        total_changes += changes
        
        print(f'{filename}: 移除了 {changes} 字节的多语言标记')
    
    print(f'\n总计: {total_changes} 字节的多语言标记已移除')
    print('所有文件已恢复为只有中文的状态')

if __name__ == '__main__':
    main()
