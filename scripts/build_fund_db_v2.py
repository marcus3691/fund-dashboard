#!/usr/bin/env python3
"""
基金数据库建设 - 简化高效版
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

# 强制输出刷新
sys.stdout.flush()

# Tushare配置
client.DataApi._DataApi__http_url = 'http://tushare.xyz'
pro = ts.pro_api('080afaf41dbb746406290078112f271e50e79a0858c9494bb52a1ec1')

print("="*70, flush=True)
print("基金数据库建设 - 全量数据获取", flush=True)
print("="*70, flush=True)
print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
print(flush=True)

# 创建目录
os.makedirs('/root/.openclaw/workspace/fund_data/volatility_db', exist_ok=True)

# 基金分类
FUND_CATEGORIES = {
    '股票型': '主动股票型', '成长型': '主动股票型', '价值型': '主动股票型',
    '积极成长型': '主动股票型', '稳健增长型': '主动股票型', '科技型': '主动股票型', '创新型': '主动股票型',
    '混合型': '混合型-偏股', '灵活配置型': '混合型-平衡', '平衡型': '混合型-平衡',
    '主题型': '混合型-偏股', '积极配置型': '混合型-偏股', '强化收益型': '混合型-偏债',
    '稳定型': '债券型-主动', '债券型': '债券型-主动', 'FOF': 'FOF',
    '被动指数型': '指数型', '增强指数型': '指数增强型'
}

target_categories = ['主动股票型', '混合型-偏股', '混合型-平衡', '混合型-偏债', 
                     'FOF', '指数增强型', '债券型-主动']

# 获取日期
today = datetime.now()
dates = {
    '3m': (today - timedelta(days=90)).strftime('%Y%m%d'),
    '6m': (today - timedelta(days=180)).strftime('%Y%m%d'),
    '1y': (today - timedelta(days=365)).strftime('%Y%m%d'),
}

# 获取基金列表
print("【第一步】获取基金列表...", flush=True)
df_funds = pro.fund_basic(market='E')
active_funds = df_funds[df_funds['status'] == 'L'].copy()
active_funds['category'] = active_funds['invest_type'].map(FUND_CATEGORIES).fillna('其他')
target_funds = active_funds[active_funds['category'].isin(target_categories)].copy()

print(f"目标类别基金: {len(target_funds)} 只", flush=True)
for cat in target_categories:
    count = len(target_funds[target_funds['category'] == cat])
    print(f"  {cat}: {count} 只", flush=True)
print(flush=True)

# 计算指标
print("【第二步】计算指标（预计30-60分钟）...", flush=True)
fund_records = []
failed = []
total = len(target_funds)
start_time = time.time()

for i, (idx, row) in enumerate(target_funds.iterrows()):
    code = row['ts_code']
    name = row['name'][:20]  # 截断长名称
    category = row['category']
    
    try:
        # 获取净值数据
        df_nav = pro.fund_nav(ts_code=code, start_date=dates['1y'], end_date=today.strftime('%Y%m%d'))
        
        if df_nav.empty or len(df_nav) < 30:
            failed.append({'code': code, 'reason': '数据不足'})
            continue
        
        df_nav = df_nav.sort_values('nav_date')
        df_nav['daily_return'] = df_nav['unit_nav'].pct_change()
        
        latest_nav = df_nav['unit_nav'].iloc[-1]
        
        # 计算各周期收益
        def calc_return(days):
            try:
                target_idx = max(0, len(df_nav) - days//7)  # 简化：按周估算
                past_nav = df_nav.iloc[target_idx]['unit_nav']
                return (latest_nav - past_nav) / past_nav * 100
            except:
                return None
        
        ret_3m = calc_return(90)
        ret_6m = calc_return(180)
        ret_1y = calc_return(365)
        
        # 风险指标（最近1年）
        daily_rets = df_nav['daily_return'].dropna()
        volatility = daily_rets.std() * np.sqrt(252) * 100
        
        cummax = df_nav['unit_nav'].cummax()
        max_dd = ((cummax - df_nav['unit_nav']) / cummax).max() * 100
        
        sharpe = (ret_1y - 2) / volatility if volatility > 0 and ret_1y else 0
        
        fund_records.append({
            'ts_code': code, 'name': row['name'], 'invest_type': row['invest_type'],
            'category': category, 'return_3m': round(ret_3m, 2) if ret_3m else None,
            'return_6m': round(ret_6m, 2) if ret_6m else None,
            'return_1y': round(ret_1y, 2) if ret_1y else None,
            'volatility': round(volatility, 2), 'max_drawdown': round(max_dd, 2),
            'sharpe': round(sharpe, 2), 'data_points': len(df_nav)
        })
        
    except Exception as e:
        failed.append({'code': code, 'reason': str(e)[:30]})
    
    # 进度报告
    if (i + 1) % 20 == 0 or i == total - 1:
        elapsed = time.time() - start_time
        rate = (i + 1) / elapsed if elapsed > 0 else 0
        eta = (total - i - 1) / rate if rate > 0 else 0
        print(f"  进度: {i+1}/{total} ({(i+1)/total*100:.1f}%) | "
              f"成功: {len(fund_records)} | 失败: {len(failed)} | "
              f"ETA: {eta/60:.1f}分钟", flush=True)
    
    # 限速
    if (i + 1) % 50 == 0:
        time.sleep(0.5)

print(f"\n处理完成: 成功 {len(fund_records)} 只, 失败 {len(failed)} 只", flush=True)

# 保存数据
print("\n【第三步】保存数据...", flush=True)
df_main = pd.DataFrame(fund_records)
df_main.to_csv('/root/.openclaw/workspace/fund_data/fund_main.csv', index=False, encoding='utf-8-sig')
print(f"  CSV已保存: {len(df_main)} 条", flush=True)

# SQLite
db_path = '/root/.openclaw/workspace/fund_data/volatility_db/fund_database.db'
conn = sqlite3.connect(db_path)
df_main.to_sql('fund_basic', conn, if_exists='replace', index=False)

# 按类别排名
print("\n【第四步】计算类别内排名...", flush=True)
for category in target_categories:
    cat_df = df_main[df_main['category'] == category].copy()
    if len(cat_df) == 0:
        continue
    
    # 1年收益排名
    valid = cat_df[cat_df['return_1y'].notna()].copy()
    if len(valid) > 0:
        valid['rank_1y'] = valid['return_1y'].rank(ascending=False, method='min')
        valid['percentile_1y'] = round((1 - (valid['rank_1y'] - 1) / len(valid)) * 100, 1)
        
        for idx, row in valid.iterrows():
            mask = df_main['ts_code'] == row['ts_code']
            df_main.loc[mask, 'rank_1y'] = row['rank_1y']
            df_main.loc[mask, 'percentile_1y'] = row['percentile_1y']
    
    print(f"  {category}: {len(cat_df)} 只", flush=True)

# 保存完整数据
df_main.to_sql('fund_ranking', conn, if_exists='replace', index=False)
conn.close()
print(f"  数据库已保存: {db_path}", flush=True)

# 摘要
print("\n【第五步】生成摘要...", flush=True)
summary = {
    'data_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'total': len(target_funds), 'success': len(fund_records), 'failed': len(failed),
    'categories': {}
}

for category in target_categories:
    cat_df = df_main[df_main['category'] == category]
    if len(cat_df) == 0:
        continue
    summary['categories'][category] = {
        'count': len(cat_df),
        'avg_return_1y': round(cat_df['return_1y'].mean(), 1),
        'avg_volatility': round(cat_df['volatility'].mean(), 1),
        'avg_sharpe': round(cat_df['sharpe'].mean(), 2)
    }

with open('/root/.openclaw/workspace/fund_data/summary_v2.json', 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print(f"  摘要已保存", flush=True)

# 输出结果
print("\n" + "="*70, flush=True)
print("关键数据", flush=True)
print("="*70, flush=True)
for cat, data in summary['categories'].items():
    print(f"{cat}: {data['count']}只 | 平均收益: {data['avg_return_1y']}% | 夏普: {data['avg_sharpe']}", flush=True)

print(f"\n完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
