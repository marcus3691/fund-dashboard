#!/usr/bin/env python3
"""
补全缺失持仓数据
目标：67只基金，2024Q1-Q4持仓数据
"""

import pandas as pd
import tushare as ts
import tushare.pro.client as client
from datetime import datetime
import time
import os

# Tushare配置
client.DataApi._DataApi__http_url = 'http://tushare.xyz'
pro = ts.pro_api('080afaf41dbb746406290078112f271e50e79a0858c9494bb52a1ec1')

print("="*70)
print("补全缺失持仓数据")
print("="*70)
print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 加载缺失列表
df_missing = pd.read_csv('/root/.openclaw/workspace/fund_data/missing_holdings_list.csv')
codes = df_missing['ts_code'].tolist()

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
start_time = time.time()

print("开始获取持仓数据...")
print()

for code in codes:
    for quarter_name, end_date in quarters:
        try:
            df_portfolio = pro.fund_portfolio(ts_code=code, end_date=end_date)
            
            if df_portfolio.empty:
                failed_records.append({
                    'ts_code': code,
                    'quarter': quarter_name,
                    'reason': '无数据'
                })
            else:
                df_portfolio['quarter'] = quarter_name
                df_portfolio['fund_code'] = code
                all_holdings.append(df_portfolio)
            
            completed += 1
            
            if completed % 30 == 0:
                elapsed = time.time() - start_time
                rate = completed / elapsed if elapsed > 0 else 0
                eta = (total_tasks - completed) / rate if rate > 0 else 0
                progress = completed / total_tasks * 100
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                      f"进度: {completed}/{total_tasks} ({progress:.1f}%) | "
                      f"成功: {len(all_holdings)} | 失败: {len(failed_records)} | "
                      f"ETA: {eta/60:.0f}分钟")
            
            time.sleep(0.3)
            
        except Exception as e:
            failed_records.append({
                'ts_code': code,
                'quarter': quarter_name,
                'reason': str(e)[:50]
            })
            completed += 1
            time.sleep(0.5)

print()
print(f"获取完成: 成功 {len(all_holdings)} 只基金季度组合, 失败 {len(failed_records)} 条记录")
print()

# 合并并保存
if all_holdings:
    df_all_holdings = pd.concat(all_holdings, ignore_index=True)
    
    # 追加到现有持仓数据
    df_existing = pd.read_csv('/root/.openclaw/workspace/fund_data/holdings/core_library_holdings.csv')
    df_combined = pd.concat([df_existing, df_all_holdings], ignore_index=True)
    df_combined.to_csv('/root/.openclaw/workspace/fund_data/holdings/core_library_holdings.csv',
                       index=False, encoding='utf-8-sig')
    
    print(f"持仓数据已更新: 新增{len(df_all_holdings)}条，总计{len(df_combined)}条")
    
    # 保存新增部分
    df_all_holdings.to_csv('/root/.openclaw/workspace/fund_data/holdings/supplemental_holdings.csv',
                           index=False, encoding='utf-8-sig')

# 保存失败记录
if failed_records:
    pd.DataFrame(failed_records).to_csv('/root/.openclaw/workspace/fund_data/holdings/supplemental_failed.csv',
                                        index=False, encoding='utf-8-sig')

print()
print("="*70)
print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)
