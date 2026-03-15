#!/usr/bin/env python3
"""
全市场基金波动率数据库建设脚本
从2025年数据开始，逐步扩展至历史数据
"""

import tushare as ts
import tushare.pro.client as client
import pandas as pd
import json
import time
from datetime import datetime

# Tushare配置
client.DataApi._DataApi__http_url = 'http://tushare.xyz'
pro = ts.pro_api('080afaf41dbb746406290078112f271e50e79a0858c9494bb52a1ec1')

print("="*60)
print("全市场基金波动率数据库建设 - 2025年度数据")
print("="*60)
print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 第一步：获取基金列表
print("【第一步】获取基金列表...")
df_funds = pro.fund_basic(market='E')

# 筛选主动权益基金（股票型、混合型、FOF）
valid_types = ['股票型', '混合型', 'FOF']
active_funds = df_funds[
    (df_funds['invest_type'].isin(valid_types)) & 
    (df_funds['status'] == 'L')
].copy()

print(f"有效基金总数: {len(active_funds)}")
print(f"类型分布:")
print(active_funds['invest_type'].value_counts())
print()

# 为了测试先取前50只
# 正式运行时删除这一行，处理全部基金
# active_funds = active_funds.head(50)

# 第二步：计算每只基金的波动率和收益
print("【第二步】计算基金波动率和收益指标...")
print("预计耗时: 30-60分钟（取决于基金数量）")
print()

fund_stats = []
failed_funds = []
total = len(active_funds)

for i, (idx, row) in enumerate(active_funds.iterrows()):
    code = row['ts_code']
    name = row['name']
    fund_type = row['invest_type']
    
    try:
        # 获取2025年净值数据
        df_nav = pro.fund_nav(ts_code=code, start_date='20250101', end_date='20251231')
        
        if df_nav.empty or len(df_nav) < 30:
            failed_funds.append({'code': code, 'reason': '数据不足'})
            continue
        
        # 计算指标
        df_nav = df_nav.sort_values('nav_date')
        df_nav['daily_return'] = df_nav['unit_nav'].pct_change()
        
        # 年化波动率
        volatility = df_nav['daily_return'].std() * (252**0.5) * 100
        
        # 年度收益
        start_nav = df_nav.iloc[0]['unit_nav']
        end_nav = df_nav.iloc[-1]['unit_nav']
        annual_return = (end_nav - start_nav) / start_nav * 100
        
        # 最大回撤
        cummax = df_nav['unit_nav'].cummax()
        drawdown = (cummax - df_nav['unit_nav']) / cummax
        max_drawdown = drawdown.max() * 100
        
        # 夏普比率（简化计算，假设无风险利率2%）
        sharpe = (annual_return - 2) / volatility if volatility > 0 else 0
        
        fund_stats.append({
            'ts_code': code,
            'name': name,
            'invest_type': fund_type,
            'annual_return': round(annual_return, 2),
            'volatility': round(volatility, 2),
            'max_drawdown': round(max_drawdown, 2),
            'sharpe': round(sharpe, 2),
            'data_points': len(df_nav)
        })
        
        # 每10只报告进度
        if (i + 1) % 10 == 0:
            print(f"  进度: {i+1}/{total} ({(i+1)/total*100:.1f}%) | 成功: {len(fund_stats)} | 失败: {len(failed_funds)}")
        
        # 每50只暂停一下，避免API限制
        if (i + 1) % 50 == 0:
            time.sleep(2)
            
    except Exception as e:
        failed_funds.append({'code': code, 'reason': str(e)[:50]})
        continue

print()
print(f"处理完成: 成功 {len(fund_stats)} 只, 失败 {len(failed_funds)} 只")
print()

# 第三步：保存原始数据
print("【第三步】保存原始数据...")
df_stats = pd.DataFrame(fund_stats)
df_stats.to_csv('/root/.openclaw/workspace/fund_data/fund_stats_2025.csv', index=False, encoding='utf-8-sig')
print(f"  已保存: fund_stats_2025.csv ({len(df_stats)} 条记录)")

# 第四步：按波动率分组
print()
print("【第四步】按波动率分组...")

def vol_group(vol):
    if vol < 10:
        return '低波动(0-10%)'
    elif vol < 15:
        return '中低波动(10-15%)'
    elif vol < 20:
        return '中波动(15-20%)'
    elif vol < 30:
        return '高波动(20-30%)'
    else:
        return '极高波动(30%+)'

df_stats['vol_group'] = df_stats['volatility'].apply(vol_group)

print("波动率分组统计:")
print(df_stats['vol_group'].value_counts().sort_index())
print()

# 第五步：生成每组统计
print("【第五步】生成每组统计指标...")

group_stats = df_stats.groupby('vol_group').agg({
    'annual_return': ['count', 'mean', 'median', 'min', 'max'],
    'volatility': ['mean', 'median'],
    'sharpe': ['mean', 'median'],
    'max_drawdown': ['mean', 'median']
}).round(2)

print(group_stats)
print()

# 第六步：保存分组数据
print("【第六步】保存分组数据...")

# 按波动率分组保存
volatility_groups = {}
for group in df_stats['vol_group'].unique():
    group_df = df_stats[df_stats['vol_group'] == group].sort_values('annual_return', ascending=False)
    volatility_groups[group] = group_df.to_dict('records')

with open('/root/.openclaw/workspace/fund_data/volatility_groups_2025.json', 'w', encoding='utf-8') as f:
    json.dump(volatility_groups, f, ensure_ascii=False, indent=2)

print(f"  已保存: volatility_groups_2025.json")

# 第七步：生成摘要报告
print()
print("【第七步】生成摘要报告...")

summary = {
    'data_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'total_funds': len(active_funds),
    'success_count': len(fund_stats),
    'failed_count': len(failed_funds),
    'year': 2025,
    'volatility_distribution': df_stats['vol_group'].value_counts().to_dict(),
    'top_performers': df_stats.nlargest(10, 'annual_return')[['ts_code', 'name', 'annual_return', 'volatility', 'sharpe']].to_dict('records'),
    'best_sharpe': df_stats.nlargest(10, 'sharpe')[['ts_code', 'name', 'annual_return', 'volatility', 'sharpe']].to_dict('records')
}

with open('/root/.openclaw/workspace/fund_data/summary_2025.json', 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print(f"  已保存: summary_2025.json")
print()

# 第八步：输出关键发现
print("="*60)
print("关键发现")
print("="*60)

print(f"\n1. 基金总数: {len(fund_stats)} 只")
print(f"2. 平均收益: {df_stats['annual_return'].mean():.2f}%")
print(f"3. 平均波动率: {df_stats['volatility'].mean():.2f}%")
print(f"4. 最佳收益: {df_stats['annual_return'].max():.2f}% ({df_stats.loc[df_stats['annual_return'].idxmax(), 'name']})")
print(f"5. 最佳夏普: {df_stats['sharpe'].max():.2f} ({df_stats.loc[df_stats['sharpe'].idxmax(), 'name']})")

print("\n波动率分组收益中位数:")
for group in ['低波动(0-10%)', '中低波动(10-15%)', '中波动(15-20%)', '高波动(20-30%)', '极高波动(30%+)']:
    if group in df_stats['vol_group'].values:
        median_return = df_stats[df_stats['vol_group']==group]['annual_return'].median()
        count = len(df_stats[df_stats['vol_group']==group])
        print(f"  {group}: {median_return:.2f}% ({count}只)")

print()
print("="*60)
print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*60)
