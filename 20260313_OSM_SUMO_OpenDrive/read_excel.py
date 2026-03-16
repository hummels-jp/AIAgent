import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
import sys
import io

# 设置输出编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 读取现有文件
file_path = '2026_03_16_コンテンツ比較表.xlsx'
xl = pd.ExcelFile(file_path)
print('Sheet names:', xl.sheet_names)

# 读取所有工作表数据
all_sheets = pd.read_excel(file_path, sheet_name=None)

# 显示现有数据结构
for sheet_name, df in all_sheets.items():
    print(f'\n=== {sheet_name} ===')
    print(f'Dimensions: {df.shape}')
    print(f'Columns: {list(df.columns)}')
    print(df.head(20).to_string())
