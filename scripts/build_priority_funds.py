#!/usr/bin/env python3
"""
场外基金数据库建设 - 混合型+股票型优先版
目标：混合型-偏股 + 混合型-平衡 + 主动股票型 = 约6,366只
预计耗时：2-2.5小时
"""

import tushare as ts
import tushare.pro.client as client
import pandas as pd
import numpy as np
import json
import sqlite3
import time
import sys
from datetime import datetime, timedelta
import os

sys.stdout.flush()

# Tushare配置
client.DataApi._DataApi__http_url = 'http://tushare.xyz'
pro = ts.pro_api('080afaf41dbb746406290078112f271e50e79a0858c9494bb52a1ec1')

print("="*70, flush=True)
print("场外基金数据库建设 - 混合型+股票型优先", flush=True)
print("="*70, flush=True)
print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
print(flush=True)

# 创建目录
os.makedirs('/root/.openclaw/workspace/fund_data/volatility_db', exist_ok=True)

# 只保留核心类别
PRIORITY_TYPES = ['混合型', '股票型', '灵活配置型', '平衡型', '成长型', '价值型', 
                  '积极成长型', '稳健增长型', '主题型', '积极配置型']

FUND_CATEGORIES = {
    '股票型': '主动股票型', '成长型': '主动股票型', '价值型': '主动股票型',
    '积极成长型': '主动股票型', '稳健增长型': '主动股票型',
    '混合型': '混合型-偏股', '主题型': '混合型-偏股', '积极配置型': '混合型-偏股',
    '灵活配置型': '混合型-平衡', '平衡型': '混合型-平衡'
}

TARGET_CATEGORIES = ['主动股票型', '混合型-偏股', '混合型-平衡']

# 获取日期
today = datetime.now()
dates = {
    '3m': (today - timedelta(days=90)).strftime('%Y%m%d'),
    '6m': (today - timedelta(days=180)).strftime('%Y%m%d'),
    '1y': (today - timedelta(days=365)).strftime('%Y%m%d'),
}

print("【第一步】获取混合型+股票型基金列表...", flush=True)
df_o = pro.fund_basic(market='O')
df_active = df_o[df_o['status'] == 'L'].copy()
df_target = df_active[df_active['invest_type'].isin(PRIORITY_TYPES)].copy()
df_target['category'] = df_target['invest_type'].map(FUND_CATEGORIES).fillna('其他')
df_target = df_target[df_target['category'].isin(TARGET_CATEGORIES)].copy()

print(f"目标基金: {len(df_target)} 只", flush=True)
for cat in TARGET_CATEGORIES:
    count = len(df_target[df_target['category'] == cat])
    print(f"  {cat}: {count} 只", flush=True)
print(flush=True)

# 保存列表
df_target[['ts_code', 'name', 'invest_type', 'category']].to_csv(
    '/root/.openclaw/workspace/fund_data/priority_target_list.csv', index=False, encoding='utf-8-sig'
)

# 计算指标
print("\n【第二步】计算指标（预计2-2.5小时）...", flush=True)
print(flush=True)

fund_records = []
failed = []
total = len(df_target)
start_time = time.time()
last_report_time = start_time

for i, (idx, row) in enumerate(df_target.iterrows()):
    code = row['ts_code']
    name = row['name'][:30] if len(row['name']) > 30 else row['name']
    category = row['category']
    
    try:
        df_nav = pro.fund_nav(ts_code=code, start_date=dates['1y'], end_date=today.strftime('%Y%m%d'))
        
        if df_nav.empty or len(df_nav) < 30:
            failed.append({'code': code, 'name': name, 'reason': '数据不足'})
            continue
        
        df_nav = df_nav.sort_values('nav_date')
        df_nav['daily_return'] = df_nav['unit_nav'].pct_change()
        latest_nav = df_nav['unit_nav'].iloc[-1]
        
        def calc_return(days):
            try:
                target_idx = max(0, len(df_nav) - days//7)
                past_nav = df_nav.iloc[target_idx]['unit_nav']
                return (latest_nav - past_nav) / past_nav * 100
            except:
                return None
        
        ret_3m = calc_return(90)
        ret_6m = calc_return(180)
        ret_1y = calc_return(365)
        
        daily_rets = df_nav['daily_return'].dropna()
        if len(daily_rets) < 20:
            failed.append({'code': code, 'name': name, 'reason': '收益率数据不足'})
            continue
            
        volatility = daily_rets.std() * np.sqrt(252) * 100
        cummax = df_nav['unit_nav'].cummax()
        max_dd = ((cummax - df_nav['unit_nav']) / cummax).max() * 100
        sharpe = (ret_1y - 2) / volatility if volatility > 0 and ret_1y else 0
        
        fund_records.append({
            'ts_code': code, 'name': row['name'], 'invest_type': row['invest_type'],
            'category': category, 
            'return_3m': round(ret_3m, 2) if ret_3m else None,
            'return_6m': round(ret_6m, 2) if ret_6m else None,
            'return_1y': round(ret_1y, 2) if ret_1y else None,
            'volatility': round(volatility, 2), 
            'max_drawdown': round(max_dd, 2),
            'sharpe': round(sharpe, 2), 
            'data_points': len(df_nav)
        })
        
    except Exception as e:
        failed.append({'code': code, 'name': name, 'reason': str(e)[:40]})
    
    # 进度报告（每100只或每5分钟）
    current_time = time.time()
    time_since_last_report = current_time - last_report_time
    
    if (i + 1) % 100 == 0 or time_since_last_report > 300 or i == total - 1:
        last_report_time = current_time
        elapsed = current_time - start_time
        rate = (i + 1) / elapsed if elapsed > 0 else 0
        eta = (total - i - 1) / rate if rate > 0 else 0
        progress = (i + 1) / total * 100
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] "
              f"进度: {i+1}/{total} ({progress:.1f}%) | "
              f"成功: {len(fund_records)} | 失败: {len(failed)} | "
              f"ETA: {eta/60:.0f}分钟", flush=True)
    
    if (i + 1) % 200 == 0:
        time.sleep(1)

print(f"\n处理完成: 成功 {len(fund_records)} 只, 失败 {len(failed)} 只", flush=True)

# 保存失败记录
if failed:
    pd.DataFrame(failed).to_csv('/root/.openclaw/workspace/fund_data/priority_failed.csv', 
                                 index=False, encoding='utf-8-sig')

# 保存数据
print("\n【第三步】保存数据...", flush=True)
df_main = pd.DataFrame(fund_records)
df_main.to_csv('/root/.openclaw/workspace/fund_data/fund_priority.csv', index=False, encoding='utf-8-sig')
print(f"  CSV已保存: {len(df_main)} 条", flush=True)

# SQLite
db_path = '/root/.openclaw/workspace/fund_data/volatility_db/fund_priority.db'
conn = sqlite3.connect(db_path)
df_main.to_sql('fund_basic', conn, if_exists='replace', index=False)

# 按类别排名
print("\n【第四步】计算类别内排名...", flush=True)
for category in TARGET_CATEGORIES:
    cat_df = df_main[df_main['category'] == category].copy()
    if len(cat_df) == 0:
        continue
    
    valid = cat_df[cat_df['return_1y'].notna()].copy()
    if len(valid) > 0:
        valid['rank_1y'] = valid['return_1y'].rank(ascending=False, method='min')
        valid['percentile_1y'] = round((1 - (valid['rank_1y'] - 1) / len(valid)) * 100, 1)
        
        for idx, row in valid.iterrows():
            mask = df_main['ts_code'] == row['ts_code']
            df_main.loc[mask, 'rank_1y'] = row['rank_1y']
            df_main.loc[mask, 'percentile_1y'] = row['percentile_1y']
    
    print(f"  {category}: {len(cat_df)} 只", flush=True)

df_main.to_sql('fund_ranking', conn, if_exists='replace', index=False)
conn.close()
print(f"  数据库已保存: {db_path}", flush=True)

# 生成摘要
print("\n【第五步】生成摘要...", flush=True)
summary = {
    'data_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'total_target': len(df_target), 
    'success': len(fund_records), 
    'failed': len(failed),
    'categories': {}
}

for category in TARGET_CATEGORIES:
    cat_df = df_main[df_main['category'] == category]
    if len(cat_df) == 0:
        continue
    summary['categories'][category] = {
        'count': len(cat_df),
        'avg_return_1y': round(cat_df['return_1y'].mean(), 1),
        'avg_volatility': round(cat_df['volatility'].mean(), 1),
        'avg_sharpe': round(cat_df['sharpe'].mean(), 2),
        'top_3': cat_df.nlargest(3, 'return_1y')[['ts_code', 'name', 'return_1y']].to_dict('records')
    }

with open('/root/.openclaw/workspace/fund_data/summary_priority.json', 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print(f"  摘要已保存", flush=True)

# 输出结果
print("\n" + "="*70, flush=True)
print("【混合型+股票型基金数据库建设完成】", flush=True)
print("="*70, flush=True)
print(f"目标基金: {summary['total_target']} 只", flush=True)
print(f"成功处理: {summary['success']} 只", flush=True)
print(f"处理失败: {summary['failed']} 只", flush=True)
print()

for cat, data in summary['categories'].items():
    print(f"{cat}: {data['count']}只 | 平均收益: {data['avg_return_1y']}% | 夏普: {data['avg_sharpe']}", flush=True)

print()
print("="*70, flush=True)
print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
print("="*70, flush=True)
