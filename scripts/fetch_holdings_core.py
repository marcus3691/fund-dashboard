#!/usr/bin/env python3
"""
核心库基金季度持仓数据获取
目标：194只核心库基金，2024Q1-Q4持仓数据
预计耗时：2-3小时
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
print("核心库基金季度持仓数据获取")
print("="*70)
print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 创建输出目录
os.makedirs('/root/.openclaw/workspace/fund_data/holdings', exist_ok=True)

# 加载核心库基金列表
df_core = pd.read_csv('/root/.openclaw/workspace/fund_data/fund_core_library.csv')
codes = df_core['ts_code'].tolist()

print(f"目标基金: {len(codes)} 只")
print()

# 季度列表（2024年四个季度）
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
            # 获取基金持仓数据
            df_portfolio = pro.fund_portfolio(ts_code=code, end_date=end_date)
            
            if df_portfolio.empty:
                failed_records.append({
                    'ts_code': code,
                    'quarter': quarter_name,
                    'reason': '无数据'
                })
            else:
                # 添加季度信息
                df_portfolio['quarter'] = quarter_name
                df_portfolio['fund_code'] = code
                all_holdings.append(df_portfolio)
            
            completed += 1
            
            # 每50个任务报告进度
            if completed % 50 == 0:
                elapsed = time.time() - start_time
                rate = completed / elapsed if elapsed > 0 else 0
                eta = (total_tasks - completed) / rate if rate > 0 else 0
                progress = completed / total_tasks * 100
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                      f"进度: {completed}/{total_tasks} ({progress:.1f}%) | "
                      f"成功: {len(all_holdings)} | 失败: {len(failed_records)} | "
                      f"ETA: {eta/60:.0f}分钟")
            
            # 限速
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

# 合并所有持仓数据
if all_holdings:
    df_all_holdings = pd.concat(all_holdings, ignore_index=True)
    
    # 保存完整持仓数据
    df_all_holdings.to_csv('/root/.openclaw/workspace/fund_data/holdings/core_library_holdings.csv', 
                           index=False, encoding='utf-8-sig')
    print(f"持仓数据已保存: {len(df_all_holdings)} 条记录")
    
    # 按基金保存单独文件
    for code in codes:
        fund_holdings = df_all_holdings[df_all_holdings['fund_code'] == code]
        if len(fund_holdings) > 0:
            fund_holdings.to_csv(f'/root/.openclaw/workspace/fund_data/holdings/{code}_holdings.csv',
                                index=False, encoding='utf-8-sig')
    
    print(f"已生成 {len(codes)} 个基金单独持仓文件")

# 保存失败记录
if failed_records:
    pd.DataFrame(failed_records).to_csv('/root/.openclaw/workspace/fund_data/holdings/failed_holdings.csv',
                                        index=False, encoding='utf-8-sig')

# 生成摘要
summary = {
    'fetch_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'total_funds': len(codes),
    'quarters': [q[0] for q in quarters],
    'total_tasks': total_tasks,
    'success_quarters': len(all_holdings),
    'failed_records': len(failed_records),
    'total_holdings_records': len(df_all_holdings) if all_holdings else 0
}

import json
with open('/root/.openclaw/workspace/fund_data/holdings/holdings_summary.json', 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print()
print("="*70)
print("【持仓数据获取完成】")
print("="*70)
print(f"基金数量: {summary['total_funds']} 只")
print(f"季度数: {len(summary['quarters'])} 个")
print(f"成功获取: {summary['success_quarters']} 只基金季度组合")
print(f"总持仓记录: {summary['total_holdings_records']} 条")
print(f"失败记录: {summary['failed_records']} 条")
print()
print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)
