#!/usr/bin/env python3
"""
ETF历史行情验证脚本
获取近期真实数据，验证地缘冲突期间的ETF表现
"""

import json
import os
import sys
from datetime import datetime, timedelta

# Tushare Token
TUSHARE_TOKEN = '33996190080200cd63a01732ad443c390d9d580913ec938d4e1d704d'

# 需要验证的ETF
ETF_CODES = {
    '515220.SH': '煤炭ETF',
    '512400.SH': '有色金属ETF',
    '518880.SH': '黄金ETF',
    '512480.SH': '半导体ETF',
    '515880.SH': '通信ETF',
    '510300.SH': '沪深300ETF'
}

def fetch_etf_daily(code, start_date, end_date):
    """从Tushare获取ETF日线数据"""
    try:
        import tushare as ts
        ts.set_token(TUSHARE_TOKEN)
        pro = ts.pro_api()
        
        # 转换日期格式
        start = start_date.replace('-', '')
        end = end_date.replace('-', '')
        
        # 获取日线数据
        df = pro.fund_daily(ts_code=code, start_date=start, end_date=end)
        
        if df.empty:
            return None
        
        # 按日期排序
        df = df.sort_values('trade_date')
        
        result = {}
        for _, row in df.iterrows():
            date = row['trade_date']
            result[date] = {
                'open': float(row['open']),
                'close': float(row['close']),
                'high': float(row['high']),
                'low': float(row['low']),
                'vol': int(row['vol']),
                'amount': float(row['amount'])
            }
        
        return result
        
    except Exception as e:
        print(f"❌ 获取 {code} 数据失败: {str(e)}")
        return None

def calculate_returns(data):
    """计算收益率"""
    if not data or len(data) < 2:
        return None
    
    dates = sorted(data.keys())
    start_price = data[dates[0]]['close']
    end_price = data[dates[-1]]['close']
    
    return {
        'start_date': dates[0],
        'end_date': dates[-1],
        'start_price': start_price,
        'end_price': end_price,
        'total_return': (end_price - start_price) / start_price * 100,
        'days': len(dates)
    }

def verify_conflict_impact():
    """
    验证地缘冲突期间（3月10日-3月14日）ETF表现
    关键时间点：
    - 3月10日前：冲突前基准
    - 3月14日：当前（美军轰炸哈尔克岛后）
    """
    print("="*70)
    print("ETF历史行情验证 - 地缘冲突期间表现")
    print("="*70)
    print()
    
    # 设置时间范围 - 完整冲突周期
    # 美以袭击伊朗起点：2026年2月28日
    # 验证截止：2026年3月13日（Tushare最新数据）
    end_date = '2026-03-13'
    start_date = '2026-02-28'  # 冲突爆发日
    
    print(f"验证周期: {start_date} 至 {end_date}")
    print()
    
    results = {}
    
    for code, name in ETF_CODES.items():
        print(f"\n📊 正在获取 {name} ({code})...")
        
        data = fetch_etf_daily(code, start_date, end_date)
        
        if data:
            returns = calculate_returns(data)
            if returns:
                results[code] = {
                    'name': name,
                    'returns': returns,
                    'daily_data': data
                }
                
                print(f"   起始价: {returns['start_price']:.3f} ({returns['start_date']})")
                print(f"   最新价: {returns['end_price']:.3f} ({returns['end_date']})")
                print(f"   涨跌幅: {returns['total_return']:+.2f}%")
                print(f"   交易日: {returns['days']}天")
        else:
            print(f"   ⚠️ 未能获取数据")
    
    return results

def analyze_results(results):
    """分析验证结果，修正之前的观点"""
    print("\n" + "="*70)
    print("验证结果分析")
    print("="*70)
    print()
    
    # 分类
    energy = ['515220.SH']  # 煤炭
    metal = ['512400.SH', '518880.SH']  # 有色、黄金
    tech = ['512480.SH', '515880.SH']  # 半导体、通信
    benchmark = ['510300.SH']  # 沪深300
    
    categories = {
        '能源（煤炭）': energy,
        '贵金属/工业金属': metal,
        '科技（半导体/通信）': tech,
        '基准（沪深300）': benchmark
    }
    
    print("📈 分类表现：\n")
    
    for category, codes in categories.items():
        print(f"【{category}】")
        for code in codes:
            if code in results:
                r = results[code]
                ret = r['returns']['total_return']
                emoji = '📈' if ret > 0 else '📉' if ret < 0 else '➡️'
                print(f"   {emoji} {r['name']}: {ret:+.2f}%")
        print()
    
    print("="*70)
    print("观点验证结论")
    print("="*70)
    print()
    
    # 验证具体观点
    print("1️⃣ 煤炭ETF（能源安全逻辑）：")
    if '515220.SH' in results:
        ret = results['515220.SH']['returns']['total_return']
        if ret > 2:
            print(f"   ✅ 验证正确：上涨 {ret:+.2f}%，能源安全逻辑成立")
        elif ret > 0:
            print(f"   ⚠️ 小幅上涨 {ret:+.2f}%，逻辑部分成立但不如预期")
        else:
            print(f"   ❌ 实际下跌 {ret:+.2f}%，能源安全逻辑未体现")
    
    print()
    print("2️⃣ 黄金ETF（避险逻辑）：")
    if '518880.SH' in results:
        ret = results['518880.SH']['returns']['total_return']
        if ret > 1:
            print(f"   ✅ 明显上涨 {ret:+.2f}%，避险逻辑成立")
        elif ret > -0.5:
            print(f"   ⚠️ 基本持平 {ret:+.2f}%，避险逻辑未明显体现（与文章描述一致）")
        else:
            print(f"   ❌ 实际下跌 {ret:+.2f}%，避险逻辑不成立")
    
    print()
    print("3️⃣ 有色ETF（工业金属）：")
    if '512400.SH' in results:
        ret = results['512400.SH']['returns']['total_return']
        if ret > 1:
            print(f"   ✅ 明显上涨 {ret:+.2f}%，通胀/供应担忧逻辑成立")
        elif ret > -1:
            print(f"   ⚠️ 基本持平 {ret:+.2f}%，工业需求担忧与供应担忧抵消")
        else:
            print(f"   📉 实际下跌 {ret:+.2f}%，工业需求下降担忧占主导")
    
    print()
    print("4️⃣ 科技ETF（美股映射）：")
    tech_return = 0
    tech_count = 0
    for code in ['512480.SH', '515880.SH']:
        if code in results:
            tech_return += results[code]['returns']['total_return']
            tech_count += 1
    
    if tech_count > 0:
        avg_tech = tech_return / tech_count
        if avg_tech < -2:
            print(f"   📉 明显下跌 {avg_tech:+.2f}%，受美股科技调整影响")
        elif avg_tech < 0:
            print(f"   ⚠️ 小幅下跌 {avg_tech:+.2f}%，科技股承压")
        else:
            print(f"   ✅ 实际上涨 {avg_tech:+.2f}%，独立于美股走势")

def save_verification_results(results):
    """保存验证结果到文件"""
    output = {
        'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'verification_period': '2026-03-07 to 2026-03-14',
        'data_source': 'Tushare Pro',
        'etf_performance': {}
    }
    
    for code, data in results.items():
        output['etf_performance'][code] = {
            'name': data['name'],
            'start_price': data['returns']['start_price'],
            'end_price': data['returns']['end_price'],
            'total_return': data['returns']['total_return'],
            'daily_data': data['daily_data']
        }
    
    output_path = os.path.join(os.path.dirname(__file__), '..', 'etf_verification_results.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 验证结果已保存: {output_path}")

if __name__ == "__main__":
    print("\n🔍 ETF历史行情验证系统")
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 执行验证
    results = verify_conflict_impact()
    
    if results:
        # 分析结果
        analyze_results(results)
        
        # 保存结果
        save_verification_results(results)
        
        print("\n" + "="*70)
        print("✅ 验证完成")
        print("="*70)
    else:
        print("\n❌ 未能获取任何ETF数据，请检查Tushare Token权限")
