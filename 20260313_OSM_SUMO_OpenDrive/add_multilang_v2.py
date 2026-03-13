#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为HTML文件中的所有中文字符添加中日英三语显示 - 改进版
"""

import re
from pathlib import Path

# 翻译对照表
TRANSLATIONS = {
    # 通用词汇
    "属性": ("属性", "Attributes"),
    "限制": ("限界", "Restrictions"),
    "速度": ("速度", "Speed"),
    "长度": ("長さ", "Length"),
    "宽度": ("幅", "Width"),
    "类型": ("タイプ", "Type"),
    "数量": ("数量", "Count"),
    "位置": ("位置", "Position"),
    "名称": ("名前", "Name"),
    "标识符": ("識別子", "Identifier"),
    "几何形状": ("幾何形状", "Geometry"),
    "连接": ("接続", "Connection"),
    "优先级": ("優先度", "Priority"),
    "特点": ("特徴", "Features"),
    "主要特点": ("主な特徴", "Key Features"),
    "关键属性": ("重要属性", "Key Attributes"),
    "描述": ("説明", "Description"),
    "说明": ("説明", "Description"),
    "示例": ("サンプル", "Example"),
    "示例数据": ("サンプルデータ", "Sample Data"),
    "对比": ("比較", "Comparison"),
    "总结": ("まとめ", "Summary"),
    "主要区别": ("主な違い", "Key Differences"),
    "使用": ("使用", "Use"),
    "包含": ("含む", "Contains"),
    "不包含": ("含まない", "Does not contain"),
    "支持": ("サポート", "Supports"),
    "不支持": ("サポートしない", "Does not support"),
    "详细": ("詳細", "Detailed"),
    "基础": ("基礎", "Basic"),
    "高级": ("高度な", "Advanced"),
    "精确": ("精密", "Precise"),
    "近似": ("近似", "Approximate"),
    "元素": ("要素", "Element"),
    "子元素": ("子要素", "Child Element"),
    "属性列表": ("属性リスト", "Attributes List"),
    "节点": ("ノード", "Node"),
    "边": ("エッジ", "Edge"),
    "道路": ("道路", "Road"),
    "车道": ("車線", "Lane"),
    "交叉口": ("交差点", "Intersection"),
    "路口": ("交差点", "Junction"),
    "信号": ("信号", "Signal"),
    "标线": ("標線", "Marking"),
    "标识": ("標識", "Sign"),
    "行人": ("歩行者", "Pedestrian"),
    "车辆": ("車両", "Vehicle"),
    "方向": ("方向", "Direction"),
    "单向": ("一方向", "One-way"),
    "双向": ("両方向", "Two-way"),
    "左侧": ("左側", "Left side"),
    "右侧": ("右側", "Right side"),
    "中心": ("中心", "Center"),
    "边界": ("境界", "Boundary"),
    "坐标": ("座標", "Coordinate"),
    "纬度": ("緯度", "Latitude"),
    "经度": ("経度", "Longitude"),
    "高度": ("高度", "Altitude"),
    "曲线": ("曲線", "Curve"),
    "直线": ("直線", "Straight line"),
    "螺旋线": ("スパイラル", "Spiral"),
    "起点": ("起点", "Start point"),
    "终点": ("終点", "End point"),
    "距离": ("距離", "Distance"),
    "角度": ("角度", "Angle"),
    "半径": ("半径", "Radius"),
    "曲率": ("曲率", "Curvature"),
    "面积": ("面積", "Area"),
    "容量": ("容量", "Capacity"),
    "流量": ("流量", "Flow"),
    "密度": ("密度", "Density"),
    "加速度": ("加速度", "Acceleration"),
    "减速度": ("減速度", "Deceleration"),
    "延迟": ("遅延", "Delay"),
    "等待": ("待機", "Waiting"),
    "通过": ("通過", "Pass through"),
    "进入": ("進入", "Enter"),
    "离开": ("離脱", "Exit"),
    "停止": ("停止", "Stop"),
    "移动": ("移動", "Move"),
    "转向": ("転向", "Turn"),
    "直行": ("直進", "Go straight"),
    "左转": ("左折", "Turn left"),
    "右转": ("右折", "Turn right"),
    "掉头": ("Uターン", "U-turn"),
    "禁止": ("禁止", "Prohibited"),
    "允许": ("許可", "Allowed"),
    "限制": ("制限", "Restricted"),
    "警告": ("警告", "Warning"),
    "提示": ("ヒント", "Tip"),
    "注意": ("注意", "Note"),
    "重要": ("重要", "Important"),
    "必需": ("必須", "Required"),
    "可选": ("任意", "Optional"),
    "默认": ("デフォルト", "Default"),
    "自定义": ("カスタム", "Custom"),
    "标准": ("標準", "Standard"),
    "特殊": ("特殊", "Special"),
    "常规": ("通常", "Regular"),
    "额外": ("追加", "Additional"),
    "基本": ("基本", "Basic"),
    "完整": ("完全", "Complete"),
    "部分": ("部分", "Partial"),
    "全部": ("全部", "All"),
    "无": ("無", "None"),
    "有": ("有", "Yes"),
    "是": ("はい", "Yes"),
    "否": ("いいえ", "No"),
    "真": ("真", "True"),
    "假": ("偽", "False"),
    "开": ("オン", "On"),
    "关": ("オフ", "Off"),
    "启用": ("有効化", "Enabled"),
    "禁用": ("無効化", "Disabled"),
    "状态": ("状態", "Status"),
    "模式": ("モード", "Mode"),
    "格式": ("フォーマット", "Format"),
    "版本": ("バージョン", "Version"),
    "时间": ("時間", "Time"),
    "日期": ("日付", "Date"),
    "持续时间": ("継続時間", "Duration"),
    "间隔": ("間隔", "Interval"),
    "频率": ("頻度", "Frequency"),
    "周期": ("サイクル", "Cycle"),
    "相位": ("相位", "Phase"),
    "序列": ("シーケンス", "Sequence"),
    "顺序": ("順序", "Order"),
    "随机": ("ランダム", "Random"),
    "确定": ("確定", "Deterministic"),
    "动态": ("動的", "Dynamic"),
    "静态": ("静的", "Static"),
    "实时": ("リアルタイム", "Real-time"),
    "离线": ("オフライン", "Offline"),
    "在线": ("オンライン", "Online"),
    "本地": ("ローカル", "Local"),
    "远程": ("リモート", "Remote"),
    "网络": ("ネットワーク", "Network"),
    "系统": ("システム", "System"),
    "环境": ("環境", "Environment"),
    "配置": ("設定", "Configuration"),
    "设置": ("設定", "Settings"),
    "选项": ("オプション", "Options"),
    "参数": ("パラメータ", "Parameters"),
    "变量": ("変数", "Variables"),
    "常量": ("定数", "Constants"),
    "函数": ("関数", "Functions"),
    "方法": ("メソッド", "Methods"),
    "类": ("クラス", "Classes"),
    "对象": ("オブジェクト", "Objects"),
    "数组": ("配列", "Arrays"),
    "列表": ("リスト", "Lists"),
    "字典": ("辞書", "Dictionaries"),
    "字符串": ("文字列", "Strings"),
    "数字": ("数字", "Numbers"),
    "布尔": ("ブール", "Booleans"),
    "空": ("空", "Empty"),
    "非空": ("非空", "Non-empty"),
    "存在": ("存在", "Exists"),
    "不存在": ("存在しない", "Does not exist"),
    "相等": ("等しい", "Equal"),
    "不相等": ("等しくない", "Not equal"),
    "大于": ("大きい", "Greater than"),
    "小于": ("小さい", "Less than"),
    "大于等于": ("以上", "Greater than or equal"),
    "小于等于": ("以下", "Less than or equal"),
    "匹配": ("一致", "Matches"),
    "不匹配": ("不一致", "Does not match"),
    "替换": ("置換", "Replace"),
    "插入": ("挿入", "Insert"),
    "删除": ("削除", "Delete"),
    "复制": ("コピー", "Copy"),
    "重命名": ("名前変更", "Rename"),
    "保存": ("保存", "Save"),
    "加载": ("読み込み", "Load"),
    "导入": ("インポート", "Import"),
    "导出": ("エクスポート", "Export"),
    "上传": ("アップロード", "Upload"),
    "下载": ("ダウンロード", "Download"),
    "同步": ("同期", "Synchronize"),
    "更新": ("更新", "Update"),
    "刷新": ("更新", "Refresh"),
    "重置": ("リセット", "Reset"),
    "清除": ("クリア", "Clear"),
    "清空": ("空にする", "Empty"),
    "搜索": ("検索", "Search"),
    "查找": ("検索", "Find"),
    "过滤": ("フィルター", "Filter"),
    "排序": ("並べ替え", "Sort"),
    "分组": ("グループ化", "Group"),
    "展开": ("展開", "Expand"),
    "折叠": ("折りたたみ", "Collapse"),
    "选择": ("選択", "Select"),
    "取消选择": ("選択解除", "Deselect"),
    "全选": ("すべて選択", "Select all"),
    "取消全选": ("すべて選択解除", "Deselect all"),
    "反选": ("選択反転", "Invert selection"),
    "拖拽": ("ドラッグ", "Drag"),
    "放置": ("ドロップ", "Drop"),
    "剪切": ("カット", "Cut"),
    "粘贴": ("貼り付け", "Paste"),
    "撤销": ("元に戻す", "Undo"),
    "重做": ("やり直し", "Redo"),
    "前进": ("前へ", "Forward"),
    "后退": ("戻る", "Back"),
    "上一页": ("前のページ", "Previous page"),
    "下一页": ("次のページ", "Next page"),
    "首页": ("ホーム", "Home"),
    "末页": ("最終ページ", "Last page"),
    "首项": ("先頭", "First"),
    "末项": ("最後", "Last"),
    "顶部": ("上部", "Top"),
    "底部": ("下部", "Bottom"),
    "中间": ("中央", "Center"),
    "上面": ("上", "Top"),
    "下面": ("下", "Bottom"),
    "前面": ("前", "Front"),
    "后面": ("後ろ", "Back"),
    "内部": ("内部", "Inside"),
    "外部": ("外部", "Outside"),
    "区域": ("領域", "Area"),
    "范围": ("範囲", "Range"),
    "偏移": ("オフセット", "Offset"),
    "容差": ("許容差", "Tolerance"),
    "误差": ("誤差", "Error"),
    "精度": ("精度", "Precision"),
    "准确性": ("正確性", "Accuracy"),
    "可靠性": ("信頼性", "Reliability"),
    "稳定性": ("安定性", "Stability"),
    "性能": ("性能", "Performance"),
    "效率": ("効率", "Efficiency"),
    "效果": ("効果", "Effect"),
    "影响": ("影響", "Impact"),
    "结果": ("結果", "Result"),
    "输出": ("出力", "Output"),
    "输入": ("入力", "Input"),
    "处理": ("処理", "Process"),
    "计算": ("計算", "Calculate"),
    "分析": ("分析", "Analyze"),
    "评估": ("評価", "Evaluate"),
    "验证": ("検証", "Verify"),
    "测试": ("テスト", "Test"),
    "调试": ("デバッグ", "Debug"),
    "优化": ("最適化", "Optimize"),
    "改进": ("改善", "Improve"),
    "增强": ("強化", "Enhance"),
    "扩展": ("拡張", "Extend"),
    "简化": ("簡素化", "Simplify"),
    "复杂化": ("複雑化", "Complicate"),
    "标准化": ("標準化", "Standardize"),
    "规范化": ("正規化", "Normalize"),
    "格式化": ("フォーマット", "Format"),
    "解析": ("解析", "Parse"),
    "编码": ("エンコード", "Encode"),
    "解码": ("デコード", "Decode"),
    "压缩": ("圧縮", "Compress"),
    "解压": ("解凍", "Decompress"),
    "加密": ("暗号化", "Encrypt"),
    "解密": ("復号化", "Decrypt"),
    "认证": ("認証", "Authenticate"),
    "授权": ("認可", "Authorize"),
    "拒绝": ("拒否", "Deny"),
    "接受": ("受け入れ", "Accept"),
    "等待": ("待機", "Wait"),
    "完成": ("完了", "Complete"),
    "进行中": ("進行中", "In progress"),
    "未开始": ("未開始", "Not started"),
    "已取消": ("キャンセル済み", "Cancelled"),
    "已失败": ("失敗", "Failed"),
    "已成功": ("成功", "Success"),
    "错误": ("エラー", "Error"),
    "信息": ("情報", "Information"),
    "帮助": ("ヘルプ", "Help"),
    "文档": ("ドキュメント", "Documentation"),
    "教程": ("チュートリアル", "Tutorial"),
    "常见问题": ("よくある質問", "FAQ"),
    "关于": ("について", "About"),
    "许可": ("ライセンス", "License"),
    "版权": ("著作権", "Copyright"),
    "保留所有权利": ("すべての権利を保有", "All rights reserved"),

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


def restore_from_backup(filepath):
    """从备份恢复文件"""
    backup_path = filepath.with_suffix('.html.backup')
    if backup_path.exists():
        with open(backup_path, 'r', encoding='utf-8') as f:
            return f.read()
    return None


def create_multilang_span(chinese):
    """创建三语格式的HTML span"""
    if chinese not in TRANSLATIONS:
        return chinese

    japanese, english = TRANSLATIONS[chinese]
    return f'<span class="zh-lang">{chinese}</span><span class="lang-separator">|</span><span class="ja-lang">{japanese}</span><span class="lang-separator">|</span><span class="en-lang">{english}</span>'


def process_file_v2(filepath):
    """处理单个HTML文件 - 改进版,避免嵌套"""
    print(f"处理文件: {filepath}")

    # 从备份恢复
    backup_content = restore_from_backup(filepath)
    if not backup_content:
        print(f"  警告: 备份文件不存在")
        return

    # 清除已有的三语span
    # 使用正则表达式移除嵌套的span
    import re
    backup_content = re.sub(r'<span class="(zh-lang|ja-lang|en-lang)">[^<]*</span>', lambda m: m.group(1), backup_content)
    backup_content = re.sub(r'<span class="lang-separator">\|</span>', '|', backup_content)
    backup_content = re.sub(r'<span class="term-multilang[^"]*">', '', backup_content)
    backup_content = re.sub(r'</span>', '', backup_content)

    # 按词长度降序排序
    sorted_keys = sorted(TRANSLATIONS.keys(), key=len, reverse=True)

    # 逐个替换
    content = backup_content
    replacements = 0
    for chinese in sorted_keys:
        # 只替换纯文本中的,不在HTML标签和代码块中
        old_count = content.count(chinese)
        if old_count > 0:
            # 简单的字符串替换
            new_str = create_multilang_span(chinese)
            content = content.replace(chinese, new_str)
            replacements += old_count

    # 写入文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  完成! 替换了 {replacements} 处\n")


def main():
    """主函数"""
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
            process_file_v2(filepath)
        else:
            print(f"警告: 文件不存在 - {filepath}")

    print("\n所有文件处理完成!")


if __name__ == "__main__":
    main()
