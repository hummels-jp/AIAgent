# -*- coding: utf-8 -*-
"""
富途 OpenD 数据获取服务
通过 subprocess 方式调用，获取交易记录
"""
import sys
import json
import subprocess
import os
import logging

# 将 futu 的日志输出到 stderr
logging.basicConfig(level=logging.CRITICAL, stream=sys.stderr)
for logger_name in ['futu', 'open_context_base', 'ConnMng']:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.CRITICAL)
    for handler in logger.handlers:
        handler.setStream(sys.stderr)

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from futu import OpenSecTradeContext, TrdMarket, RET_OK, OpenQuoteContext
from datetime import datetime, timedelta
import argparse

def get_trade_data(action, market='HK', start_date='', end_date=''):
    """获取交易数据"""
    HOST = '127.0.0.1'
    PORT = 11111
    
    result = {
        'success': False,
        'connected': False,
        'data': [],
        'error': None,
        'action': action
    }
    
    try:
        # 创建交易上下文 - 不限制市场，获取所有交易数据
        trade_ctx = OpenSecTradeContext(host=HOST, port=PORT)
        result['connected'] = True
        
        # 处理时间范围
        today = datetime.now()
        
        if action == 'today':
            # 获取当日成交
            ret, data = trade_ctx.deal_list_query()
            if ret == RET_OK:
                result['success'] = True
                result['data'] = format_deal_list(data)
            else:
                result['error'] = str(data)
                
        elif action == 'history':
            # 获取历史成交（全部）
            ret, data = trade_ctx.history_deal_list_query(start=start_date, end=end_date)
            if ret == RET_OK:
                result['success'] = True
                result['data'] = format_deal_list(data)
            else:
                result['error'] = str(data)
                
        elif action == '1w':
            # 获取近一周成交
            week_ago = (today - timedelta(days=7)).strftime('%Y-%m-%d')
            today_str = today.strftime('%Y-%m-%d')
            ret, data = trade_ctx.history_deal_list_query(start=week_ago, end=today_str)
            if ret == RET_OK:
                result['success'] = True
                result['data'] = format_deal_list(data)
            else:
                result['error'] = str(data)
                
        elif action == '1m':
            # 获取近一月成交
            month_ago = (today - timedelta(days=30)).strftime('%Y-%m-%d')
            today_str = today.strftime('%Y-%m-%d')
            ret, data = trade_ctx.history_deal_list_query(start=month_ago, end=today_str)
            if ret == RET_OK:
                result['success'] = True
                result['data'] = format_deal_list(data)
            else:
                result['error'] = str(data)
        
        trade_ctx.close()
        
    except Exception as e:
        result['error'] = str(e)

    return result

def get_vix_data():
    """获取 VIX 恐慌指数"""
    HOST = '127.0.0.1'
    PORT = 11111

    result = {
        'success': False,
        'value': None,
        'change': None,
        'changePercent': None,
        'error': None
    }

    try:
        # 使用行情上下文获取 VIX 数据
        quote_ctx = OpenQuoteContext(host=HOST, port=PORT)

        # 富途 VIX 代码是 US.VIX
        ret, data = quote_ctx.get_market_snapshot(['US.VIX'])

        if ret == RET_OK and data is not None and len(data) > 0:
            row = data.iloc[0]
            vix_price = float(row.get('cur_price', 0))
            prev_close = float(row.get('prev_close_price', vix_price))

            result['success'] = True
            result['value'] = vix_price
            result['change'] = vix_price - prev_close
            result['changePercent'] = ((vix_price - prev_close) / prev_close * 100) if prev_close > 0 else 0
        else:
            result['error'] = f'VIX 不可用: {data}'

        quote_ctx.close()

    except Exception as e:
        result['error'] = str(e)

    return result

def get_positions():
    """获取持仓数据"""
    HOST = '127.0.0.1'
    PORT = 11111

    result = {
        'success': False,
        'connected': False,
        'data': [],
        'error': None
    }

    try:
        # 使用交易上下文获取持仓
        trade_ctx = OpenSecTradeContext(host=HOST, port=PORT)
        result['connected'] = True

        # 获取持仓列表
        ret, data = trade_ctx.position_list_query()

        if ret == RET_OK and data is not None and len(data) > 0:
            result['success'] = True
            result['data'] = format_position_list(data)
        else:
            # 可能没有持仓
            result['success'] = True
            result['data'] = []

        trade_ctx.close()

    except Exception as e:
        result['error'] = str(e)

    return result

def format_position_list(df):
    """格式化持仓列表"""
    if df is None or len(df) == 0:
        return []

    result = []
    for _, row in df.iterrows():
        # 计算盈亏
        cost = float(row.get('cost_price', 0))
        quantity = float(row.get('qty', 0))
        current_price = float(row.get('market_val', 0)) / quantity if quantity > 0 else 0
        total_cost = cost * quantity
        market_value = float(row.get('market_val', 0))
        unrealized_pl = market_value - total_cost
        unrealized_pl_percent = (unrealized_pl / total_cost * 100) if total_cost > 0 else 0

        result.append({
            'code': str(row.get('code', '')),
            'name': str(row.get('stock_name', '')),
            'quantity': quantity,
            'costPrice': cost,
            'currentPrice': current_price,
            'marketValue': market_value,
            'totalCost': total_cost,
            'unrealizedPL': unrealized_pl,
            'unrealizedPLPercent': unrealized_pl_percent,
            'direction': '多' if quantity > 0 else '空',
            'market': str(row.get('market', ''))
        })

    return result

def get_stock_prices(codes):
    """批量获取股票实时价格"""
    HOST = '127.0.0.1'
    PORT = 11111
    prices = {}

    if not codes:
        return prices

    try:
        quote_ctx = OpenQuoteContext(host=HOST, port=PORT)
        ret, data = quote_ctx.get_market_snapshot(codes)
        quote_ctx.close()

        if ret == RET_OK and data is not None and len(data) > 0:
            for _, row in data.iterrows():
                code = str(row.get('code', ''))
                cur_price = float(row.get('cur_price', 0))
                prev_close = float(row.get('prev_close_price', cur_price))
                prices[code] = {'cur_price': cur_price, 'prev_close': prev_close}
        else:
            print(f"[Price] 获取失败: {data}", file=sys.stderr)
    except Exception as e:
        print(f"[Price] 获取异常: {e}", file=sys.stderr)

    return prices

def get_stock_change_rates(codes, days=1):
    """获取股票在指定天数内的涨跌幅"""
    HOST = '127.0.0.1'
    PORT = 11111
    changes = {}

    if not codes:
        return changes

    try:
        quote_ctx = OpenQuoteContext(host=HOST, port=PORT)
        
        for code in codes:
            try:
                ret, data = quote_ctx.get_history_kline(code, start=None, end=None, ktype='KType.DAY', max_count=days + 5)
                
                if ret == RET_OK and data is not None and len(data) >= 2:
                    # 获取最近两天数据计算当日涨跌幅
                    latest = data.iloc[-1]
                    prev = data.iloc[-2]
                    
                    cur_price = float(latest.get('close', 0))
                    prev_close = float(prev.get('close', 0))
                    
                    if prev_close > 0:
                        change = (cur_price - prev_close) / prev_close * 100
                        changes[code] = round(change, 2)
            except Exception as e:
                print(f"[Change] {code} 获取失败: {e}", file=sys.stderr)
        
        quote_ctx.close()
    except Exception as e:
        print(f"[Change] 获取异常: {e}", file=sys.stderr)

    return changes

def format_deal_list(df):
    """格式化成交记录"""
    if df is None or len(df) == 0:
        return []

    # 先收集所有需要的股票代码（保持原始格式）
    codes = df['code'].unique().tolist() if 'code' in df.columns else []

    # 批量获取实时价格
    prices = get_stock_prices(codes)

    result = []
    for _, row in df.iterrows():
        code = str(row.get('code', ''))
        deal_price = float(row.get('price', 0))

        # 获取当前价格 - 尝试多种代码格式匹配
        price_info = prices.get(code, {})
        # 如果精确匹配失败，尝试模糊匹配
        if not price_info:
            for key, val in prices.items():
                if code in key or key in code:
                    price_info = val
                    break

        cur_price = price_info.get('cur_price', None) if price_info else None
        prev_close = price_info.get('prev_close', None) if price_info else None

        # 如果当前价格无效（0或None），使用昨收价格
        if not cur_price or cur_price == 0:
            cur_price = prev_close

        # 计算相对于成交价的涨跌幅
        trade_change_percent = None
        if cur_price and deal_price > 0:
            trade_change_percent = ((cur_price - deal_price) / deal_price) * 100

        result.append({
            'time': str(row.get('create_time', '')),
            'code': code,
            'name': str(row.get('stock_name', '')),
            'direction': '买入' if str(row.get('trd_side', '')) == 'BUY' else '卖出',
            'directionRaw': str(row.get('trd_side', '')),
            'quantity': float(row.get('qty', 0)),
            'price': deal_price,
            'amount': float(row.get('qty', 0)) * deal_price,
            'currentPrice': cur_price,
            'prevClose': prev_close,
            'tradeChangePercent': trade_change_percent,
            'dealID': str(row.get('deal_id', '')),
            'orderID': str(row.get('order_id', '')),
            'market': str(row.get('deal_market', '')),
            'status': str(row.get('status', ''))
        })

    return result

def get_hot_stocks(period='1M', min_market_cap=5000, top_count=10):
    """获取热门股票（涨幅最大的10只，市值5000亿以上）
    
    Args:
        period: 时间周期 1W=一周, 1M=一月, 3M=三月
        min_market_cap: 最小市值（亿美元）
        top_count: 返回数量
    """
    HOST = '127.0.0.1'
    PORT = 11111

    result = {
        'success': False,
        'connected': False,
        'data': [],
        'error': None,
        'period': period
    }

    # 预定义的大市值股票（美股，代码格式：US.XXX）
    big_cap_stocks = [
        'US.AAPL', 'US.MSFT', 'US.GOOGL', 'US.AMZN', 'US.NVDA', 'US.META', 'US.TSLA',
        'US.BRK.B', 'US.LLY', 'US.AVGO', 'US.JPM', 'US.V', 'US.XOM', 'US.UNH', 'US.MA',
        'US.PG', 'US.HD', 'US.CVX', 'US.MRK', 'US.ABBV', 'US.KO', 'US.PEP', 'US.COST',
        'US.WMT', 'US.TMO', 'US.CSCO', 'US.ACN', 'US.MCD', 'US.ABT', 'US.DHR', 'US.CRM',
        'US.ADBE', 'US.WFC', 'US.BAC', 'US.CMCSA', 'US.DIS', 'US.TXN', 'US.VZ', 'US.NKE',
        'US.NEE', 'US.PM', 'US.ORCL', 'US.BMY', 'US.RTX', 'US.HON', 'US.INTC', 'US.AMD',
        'US.QCOM', 'US.IBM', 'US.SBUX', 'US.ISRG', 'US.MDT', 'US.BDX', 'US.TGT', 'US.LOW',
        'US.INTU', 'US.GILD', 'US.AMGN', 'US.ADP', 'US.EBAY', 'US.FB', 'US.NFLX', 'US.ADI'
    ]

    # 转换周期为获取K线数量
    period_map = {'1W': 7, '1M': 30, '3M': 90, '1D': 2}
    days = period_map.get(period, 30)

    try:
        quote_ctx = OpenQuoteContext(host=HOST, port=PORT)
        result['connected'] = True

        stocks_data = []

        for code in big_cap_stocks:
            try:
                # 获取K线数据
                ret, data = quote_ctx.get_history_kline(
                    code, 
                    start=None, 
                    end=None, 
                    ktype='KType.DAY', 
                    max_count=days + 5
                )

                if ret == RET_OK and data is not None and len(data) >= 2:
                    # 计算周期涨跌幅
                    start_price = float(data.iloc[0].get('close', 0))
                    end_price = float(data.iloc[-1].get('close', 0))

                    if start_price > 0:
                        period_change = ((end_price - start_price) / start_price) * 100

                        # 获取实时行情（用于市值）
                        ret2, snapshot = quote_ctx.get_market_snapshot([code])
                        market_cap = 0
                        if ret2 == RET_OK and snapshot is not None and len(snapshot) > 0:
                            market_cap = float(snapshot.iloc[0].get('market_val', 0)) / 1e8  # 转为亿美元

                        # 获取股票名称
                        name = str(data.iloc[0].get('code', code))
                        # 移除市场前缀
                        if '.' in name:
                            name = name.split('.')[1]

                        stocks_data.append({
                            'symbol': code.replace('US.', ''),  # 返回简洁代码
                            'code': code,
                            'name': name,
                            'price': end_price,
                            'periodChange': round(period_change, 2),
                            'marketCap': round(market_cap, 0),
                            'changeText': f'+{period_change:.2f}%' if period_change >= 0 else f'{period_change:.2f}%'
                        })

            except Exception as e:
                print(f"[HotStocks] {code} 获取失败: {e}", file=sys.stderr)
                continue

        quote_ctx.close()

        # 筛选市值5000亿美元以上
        filtered = [s for s in stocks_data if s['marketCap'] >= min_market_cap]

        # 按涨跌幅排序
        filtered.sort(key=lambda x: x['periodChange'], reverse=True)

        # 取前10只
        result['data'] = filtered[:top_count]
        result['success'] = True

        print(f"[HotStocks] 返回 {len(result['data'])} 只热门股票（市值≥{min_market_cap}亿）", file=sys.stderr)

    except Exception as e:
        result['error'] = str(e)
        print(f"[HotStocks] 获取异常: {e}", file=sys.stderr)

    return result

def get_watchlist(min_market_cap=1000, group_name=None, page=1, page_size=20, custom_codes=None):
    """获取自选股票列表，按分组显示
    
    Args:
        min_market_cap: 最小市值（亿美元）
        group_name: 指定分组名称，不指定则获取所有分组
        page: 页码（从1开始）
        page_size: 每页数量
        custom_codes: 自定义股票代码列表（用于手动输入）
    """
    HOST = '127.0.0.1'
    PORT = 11111

    result = {
        'success': False,
        'connected': False,
        'data': [],
        'groups': [],
        'error': None,
        'page': page,
        'pageSize': page_size,
        'total': 0
    }

    # 预定义的大市值股票列表（按分组）
    default_groups = {
        '科技': ['US.AAPL', 'US.MSFT', 'US.GOOGL', 'US.AMZN', 'US.NVDA', 'US.META', 'US.TSLA', 'US.AMD', 'US.INTC', 'US.QCOM', 'US.AVGO', 'US.CSCO', 'US.ORCL', 'US.ADBE', 'US.CRM'],
        '金融': ['US.JPM', 'US.BAC', 'US.WFC', 'US.GS', 'US.MS', 'US.C', 'US.BX', 'US.BLK', 'US.V', 'US.MA'],
        '消费': ['US.PG', 'US.KO', 'US.PEP', 'US.MCD', 'US.SBUX', 'US.NKE', 'US.COST', 'US.WMT', 'US.HD', 'US.LVS'],
        '医疗': ['US.UNH', 'US.JNJ', 'US.PFE', 'US.ABBV', 'US.MRK', 'US.LLY', 'US.AMGN', 'US.TMO', 'US.ABT'],
        '新能源': ['US.ENPH', 'US.FSLR', 'US.SEDG', 'US.CLNE', 'US.PLUG', 'US.ICLN'],
        'ETF': ['US.QQQ', 'US.SPY', 'US.SMH', 'US.XLF', 'US.XLV', 'US.ARKK', 'US.VOO', 'US.VTI'],
        '港股': ['HK.00700', 'HK.09988', 'HK.09999', 'HK.09618', 'HK.09888', 'HK.02331', 'HK.01299'],
        'A股': ['SH.600519', 'SH.601318', 'SZ.000858', 'SZ.000333', 'SH.600036']
    }

    # 如果有自定义代码，优先使用
    if custom_codes and len(custom_codes) > 0:
        codes_to_fetch = []
        for code in custom_codes:
            code = code.strip().upper()
            if not code:
                continue
            # 标准化代码格式
            if not ('.' in code):
                if code.isdigit() and len(code) == 5:
                    code = f'SH.{code}' if code.startswith(('6', '5')) else f'SZ.{code}'
                elif code.isdigit() and len(code) == 6:
                    code = f'SH.{code}' if code.startswith(('6', '5')) else f'SZ.{code}'
                else:
                    code = f'US.{code}'
            codes_to_fetch.append(code)
        
        return get_custom_stocks(codes_to_fetch)

    try:
        quote_ctx = OpenQuoteContext(host=HOST, port=PORT)
        result['connected'] = True

        # 获取自选股分组列表
        try:
            # 尝试使用富途API获取用户自选股分组
            ret, group_list = quote_ctx.get_user_security_group_list()
            if ret == RET_OK and group_list is not None and len(group_list) > 0:
                groups_data = []
                for _, row in group_list.iterrows():
                    group_info = {
                        'name': str(row.get('group_name', row.get('name', '默认分组'))),
                        'stock_count': int(row.get('stock_count', 0))
                    }
                    groups_data.append(group_info)
                result['groups'] = groups_data
                print(f"[Watchlist] 获取到 {len(groups_data)} 个自选股分组", file=sys.stderr)
        except Exception as e:
            print(f"[Watchlist] 获取自选股分组失败，使用默认分组: {e}", file=sys.stderr)
            # 使用默认分组
            result['groups'] = [{'name': name, 'stock_count': len(codes)} for name, codes in default_groups.items()]

        # 根据选择的分组获取股票
        stocks_data = []
        codes_to_fetch = []

        if group_name and group_name in default_groups:
            codes_to_fetch = default_groups[group_name]
        else:
            # 获取所有分组的股票
            for codes in default_groups.values():
                codes_to_fetch.extend(codes)

        # 去重
        codes_to_fetch = list(set(codes_to_fetch))

        # 分批获取行情数据
        batch_size = 10
        for i in range(0, len(codes_to_fetch), batch_size):
            batch = codes_to_fetch[i:i + batch_size]
            try:
                ret, snapshot = quote_ctx.get_market_snapshot(batch)
                
                if ret == RET_OK and snapshot is not None and len(snapshot) > 0:
                    for _, row in snapshot.iterrows():
                        code = str(row.get('code', ''))
                        price = float(row.get('cur_price', 0))
                        prev_close = float(row.get('prev_close_price', price))
                        market_cap = float(row.get('market_val', 0)) / 1e8  # 转为亿美元
                        name = str(row.get('name', code.split('.')[-1] if '.' in code else code))

                        # 筛选市值超过指定值
                        if market_cap >= min_market_cap and price > 0:
                            change = ((price - prev_close) / prev_close * 100) if prev_close > 0 else 0
                            
                            stocks_data.append({
                                'symbol': code.split('.')[-1] if '.' in code else code,
                                'code': code,
                                'name': name,
                                'price': round(price, 2),
                                'change': round(change, 2),
                                'changeText': f'+{change:.2f}%' if change >= 0 else f'{change:.2f}%',
                                'marketCap': round(market_cap, 0)
                            })

            except Exception as e:
                print(f"[Watchlist] 批量获取行情失败: {e}", file=sys.stderr)
                continue

        quote_ctx.close()

        # 按市值排序
        stocks_data.sort(key=lambda x: x['marketCap'], reverse=True)
        result['total'] = len(stocks_data)

        # 分页
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        result['data'] = stocks_data[start_idx:end_idx]
        result['success'] = True
        
        print(f"[Watchlist] 返回 {len(result['data'])} 只自选股（第{page}页/共{result['total']}只，市值≥{min_market_cap}亿）", file=sys.stderr)

    except Exception as e:
        result['error'] = str(e)
        print(f"[Watchlist] 获取异常: {e}", file=sys.stderr)

    return result


def get_custom_stocks(codes):
    """获取自定义股票列表的数据
    
    Args:
        codes: 股票代码列表
    """
    HOST = '127.0.0.1'
    PORT = 11111

    result = {
        'success': False,
        'connected': False,
        'data': [],
        'error': None
    }

    if not codes or len(codes) == 0:
        result['error'] = '股票代码列表为空'
        return result

    try:
        quote_ctx = OpenQuoteContext(host=HOST, port=PORT)
        result['connected'] = True

        stocks_data = []

        # 分批获取
        batch_size = 10
        for i in range(0, len(codes), batch_size):
            batch = codes[i:i + batch_size]
            try:
                ret, snapshot = quote_ctx.get_market_snapshot(batch)
                
                if ret == RET_OK and snapshot is not None and len(snapshot) > 0:
                    for _, row in snapshot.iterrows():
                        code = str(row.get('code', ''))
                        price = float(row.get('cur_price', 0))
                        prev_close = float(row.get('prev_close_price', price))
                        market_cap = float(row.get('market_val', 0)) / 1e8  # 转为亿美元
                        name = str(row.get('name', code.split('.')[-1] if '.' in code else code))

                        if price > 0:
                            change = ((price - prev_close) / prev_close * 100) if prev_close > 0 else 0
                            
                            stocks_data.append({
                                'symbol': code.split('.')[-1] if '.' in code else code,
                                'code': code,
                                'name': name,
                                'price': round(price, 2),
                                'change': round(change, 2),
                                'changeText': f'+{change:.2f}%' if change >= 0 else f'{change:.2f}%',
                                'marketCap': round(market_cap, 0)
                            })

            except Exception as e:
                print(f"[CustomStock] 批量获取失败: {e}", file=sys.stderr)
                continue

        quote_ctx.close()

        result['data'] = stocks_data
        result['success'] = True
        print(f"[CustomStock] 返回 {len(result['data'])} 只股票: {codes}", file=sys.stderr)

    except Exception as e:
        result['error'] = str(e)
        print(f"[CustomStock] 获取异常: {e}", file=sys.stderr)

    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='富途 OpenD 数据获取')
    parser.add_argument('--action', default='today', choices=['today', 'history', '1w', '1m', 'vix', 'positions', 'stock-changes', 'hot-stocks', 'watchlist', 'watchlist-custom'])
    parser.add_argument('--start', default='')
    parser.add_argument('--end', default='')
    parser.add_argument('--market', default='HK')
    parser.add_argument('--days', type=int, default=1)
    parser.add_argument('--period', default='1M', choices=['1W', '1M', '3M', '1D'])
    parser.add_argument('--min-cap', type=int, default=1000)
    parser.add_argument('--top', type=int, default=10)
    parser.add_argument('--group', default=None)
    parser.add_argument('--page', type=int, default=1)
    parser.add_argument('--page-size', type=int, default=20)
    parser.add_argument('--codes', default='')

    args = parser.parse_args()

    # 处理 VIX 请求
    if args.action == 'vix':
        result = get_vix_data()
    elif args.action == 'positions':
        result = get_positions()
    elif args.action == 'hot-stocks':
        # 获取热门股票
        period = args.period if hasattr(args, 'period') and args.period else '1M'
        min_cap = args.min_cap if hasattr(args, 'min_cap') else 5000
        top = args.top if hasattr(args, 'top') else 10
        result = get_hot_stocks(period=period, min_market_cap=min_cap, top_count=top)
    elif args.action == 'watchlist':
        # 获取自选股列表
        min_cap = args.min_cap if hasattr(args, 'min_cap') else 1000
        group_name = args.group if hasattr(args, 'group') and args.group else None
        page = args.page if hasattr(args, 'page') else 1
        page_size = args.page_size if hasattr(args, 'page_size') else 20
        result = get_watchlist(min_market_cap=min_cap, group_name=group_name, page=page, page_size=page_size)
    elif args.action == 'watchlist-custom':
        # 获取自定义股票列表
        codes_str = args.codes if hasattr(args, 'codes') and args.codes else ''
        codes = [c.strip() for c in codes_str.split(',') if c.strip()]
        result = get_watchlist(custom_codes=codes)
    elif args.action == 'stock-changes':
        # 获取股票涨跌幅
        result = {
            'success': False,
            'connected': False,
            'data': {},
            'error': None
        }
        HOST = '127.0.0.1'
        PORT = 11111
        
        # 需要查询的股票代码
        stock_codes = [
            'HK.00700', 'HK.09988',  # 港股
            'US.QQQ', 'US.NVDA', 'US.MSFT', 'US.GOOGL',  # AI & Tech
            'US.SMH', 'US.AMD', 'US.INTC', 'US.ASML',    # Semiconductor
            'US.ICLN', 'US.TSLA', 'US.ENPH', 'US.FSLR',  # EV & Energy
            'US.XLV', 'US.JNJ', 'US.UNH', 'US.LLY',       # Healthcare
            'US.XLF', 'US.JPM', 'US.BAC', 'US.GS',        # Finance
            'US.AMZN', 'US.WMT', 'US.TGT', 'US.COST',     # E-Commerce
            'US.CRM', 'US.NOW', 'US.SNOW', 'US.WDAY',     # Cloud
            'US.PANW', 'US.CRWD', 'US.ZS', 'US.OKTA',     # Cybersecurity
            'US.XBI', 'US.MRNA', 'US.REGN', 'US.VRTX',    # Biotech
            'US.VNQ', 'US.PLD', 'US.AMT', 'US.EQIX'      # Real Estate
        ]
        
        try:
            quote_ctx = OpenQuoteContext(host=HOST, port=PORT)
            result['connected'] = True
            
            for code in stock_codes:
                try:
                    ret, data = quote_ctx.get_history_kline(code, start=None, end=None, ktype='KType.DAY', max_count=args.days + 5)
                    
                    if ret == RET_OK and data is not None and len(data) >= 2:
                        # 获取最近两天数据计算涨跌幅
                        latest = data.iloc[-1]
                        prev = data.iloc[-2]
                        
                        cur_price = float(latest.get('close', 0))
                        prev_price = float(prev.get('close', 0))
                        
                        if prev_price > 0:
                            change = (cur_price - prev_price) / prev_price * 100
                            result['data'][code] = round(change, 2)
                except Exception as e:
                    print(f"[StockChange] {code} 获取失败: {e}", file=sys.stderr)
            
            quote_ctx.close()
            result['success'] = True
        except Exception as e:
            result['error'] = str(e)
    else:
        result = get_trade_data(args.action, args.market, args.start, args.end)
    
    # 输出 JSON 结果
    print(json.dumps(result, ensure_ascii=False))
