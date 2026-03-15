#!/usr/bin/env python3
"""
债券型产品库持仓数据获取与深度分析
目标：18只债券型基金
"""

import pandas as pd
import tushare as ts
import tushare.pro.client as client
from datetime import datetime
import time

client.DataApi._DataApi__http_url = 'http://tushare.xyz'
pro = ts.pro_api('080afaf41dbb746406290078112f271e50e79a0858c9494bb52a1ec1')

print("="*70)
print("债券型产品库持仓数据获取")
print("="*70)
print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 加载债券型基金列表
df_bond = pd.read_csv('/root/.openclaw/workspace/fund_data/bond_analysis_list.csv')
codes = df_bond['ts_code'].tolist()

print(f"目标基金: {len(codes)} 只")
print()

# 季度列表
quarters = [
    ('2024Q1', '20240331'),
    ('2024Q2', '20240630'),
    ('2024Q3', '20240930'),
    ('2024Q4', '20241231')
]

all_holdings = []
failed_records = []

total_tasks = len(codes) * len(quarters)
completed = 0

print("开始获取持仓数据...")
print()

for code in codes:
    for quarter_name, end_date in quarters:
        try:
            df_portfolio = pro.fund_portfolio(ts_code=code, end_date=end_date)
            
            if df_portfolio.empty:
                failed_records.append({'ts_code': code, 'quarter': quarter_name, 'reason': '无数据'})
            else:
                df_portfolio['quarter'] = quarter_name
                df_portfolio['fund_code'] = code
                all_holdings.append(df_portfolio)
            
            completed += 1
            time.sleep(0.3)
            
        except Exception as e:
            failed_records.append({'ts_code': code, 'quarter': quarter_name, 'reason': str(e)[:50]})
            completed += 1
            time.sleep(0.5)
    
    print(f"  {code} 完成")

print()
print(f"获取完成: 成功 {len(all_holdings)} 只基金季度组合, 失败 {len(failed_records)} 条记录")

# 保存数据
if all_holdings:
    df_all = pd.concat(all_holdings, ignore_index=True)
    df_all.to_csv('/root/.openclaw/workspace/fund_data/holdings/bond_selected_holdings.csv', 
                  index=False, encoding='utf-8-sig')
    print(f"  持仓数据已保存: {len(df_all)} 条记录")

if failed_records:
    pd.DataFrame(failed_records).to_csv('/root/.openclaw/workspace/fund_data/holdings/bond_failed.csv',
                                        index=False, encoding='utf-8-sig')

print()
print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)
