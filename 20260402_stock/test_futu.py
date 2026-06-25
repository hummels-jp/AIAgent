# -*- coding: utf-8 -*-
"""
富途 OpenD 测试脚本
测试连接 OpenD 并获取交易记录
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from futu import OpenSecTradeContext, TrdMarket, RET_OK
import pandas as pd

# 配置
HOST = '127.0.0.1'
PORT = 11111

print("=" * 50)
print("富途 OpenD 连接测试")
print("=" * 50)

# 创建交易上下文
print(f"\n[1] 尝试连接 OpenD ({HOST}:{PORT})...")
try:
    trade_ctx = OpenSecTradeContext(filter_trdmarket=TrdMarket.HK, host=HOST, port=PORT)
    print("✓ 连接成功！")
except Exception as e:
    print(f"✗ 连接失败: {e}")
    sys.exit(1)

# 测试获取当日成交
print("\n[2] 获取当日成交记录...")
ret, data = trade_ctx.deal_list_query()
if ret == RET_OK:
    print(f"✓ 获取成功！共 {len(data)} 条记录")
    if len(data) > 0:
        print("\n当日成交记录：")
        print(data.to_string())
else:
    print(f"✗ 获取失败: {data}")

# 测试获取历史成交
print("\n[3] 获取历史成交记录（最近30天）...")
ret, data = trade_ctx.history_deal_list_query()
if ret == RET_OK:
    print(f"✓ 获取成功！共 {len(data)} 条记录")
    if len(data) > 0:
        print("\n历史成交记录：")
        print(data.to_string())
else:
    print(f"✗ 获取失败: {data}")

# 关闭连接
print("\n[4] 关闭连接...")
trade_ctx.close()
print("✓ 连接已关闭")

print("\n" + "=" * 50)
print("测试完成！")
print("=" * 50)
