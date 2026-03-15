#!/usr/bin/env python3
"""
核心库基金深度分析
目标：50只基金，季度持仓演变、行业分布、投资风格分析
"""

import pandas as pd
import sqlite3
import json
from datetime import datetime
import os

print("="*70)
print("核心库基金深度分析")
print("="*70)
print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 加载选择的基金列表
df_selected = pd.read_csv('/root/.openclaw/workspace/fund_data/deep_analysis_selected.csv')
print(f"分析基金数量: {len(df_selected)} 只")
print()

# 加载持仓数据
df_holdings = pd.read_csv('/root/.openclaw/workspace/fund_data/holdings/core_library_holdings.csv')
print(f"持仓数据记录: {len(df_holdings)} 条")
print()

# 创建输出目录
os.makedirs('/root/.openclaw/workspace/fund_data/analysis', exist_ok=True)

# 分析结果存储
analysis_results = []

print("开始深度分析...")
print()

for idx, fund in df_selected.iterrows():
    code = fund['ts_code']
    name = fund['name']
    category = fund['category']
    quality_score = fund['quality_score']
    return_1y = fund['return_1y']
    sharpe = fund['sharpe']
    
    print(f"[{idx+1}/{len(df_selected)}] 分析 {code}: {name[:30]}...")
    
    # 获取该基金的持仓数据
    fund_holdings = df_holdings[df_holdings['fund_code'] == code].copy()
    
    if fund_holdings.empty:
        print(f"  ⚠️ 无持仓数据")
        continue
    
    # 1. 季度持仓统计
    quarters = fund_holdings['quarter'].unique()
    quarter_stats = {}
    
    for q in ['2024Q1', '2024Q2', '2024Q3', '2024Q4']:
        q_data = fund_holdings[fund_holdings['quarter'] == q]
        if not q_data.empty:
            quarter_stats[q] = {
                'stocks_count': len(q_data),
                'top10_ratio': q_data['stk_mkv_ratio'].sum() if 'stk_mkv_ratio' in q_data.columns else None,
                'top_stock': q_data.iloc[0]['stk_nm'] if 'stk_nm' in q_data.columns else None,
                'top_ratio': q_data.iloc[0]['stk_mkv_ratio'] if 'stk_mkv_ratio' in q_data.columns else None
            }
    
    # 2. 行业分布分析（简化，需要行业映射表）
    industries = {}
    if 'stk_industry' in fund_holdings.columns:
        for q in quarters:
            q_data = fund_holdings[fund_holdings['quarter'] == q]
            if not q_data.empty:
                ind_dist = q_data.groupby('stk_industry')['stk_mkv_ratio'].sum().to_dict()
                industries[q] = ind_dist
    
    # 3. 重仓股稳定性分析
    all_stocks = set()
    quarter_stocks = {}
    
    for q in quarters:
        q_data = fund_holdings[fund_holdings['quarter'] == q]
        stocks = set(q_data['stk_cd'].tolist()) if 'stk_cd' in q_data.columns else set()
        quarter_stocks[q] = stocks
        all_stocks.update(stocks)
    
    # 计算持续重仓股（出现在3个季度以上的）
    persistent_stocks = []
    for stock in all_stocks:
        count = sum(1 for q in quarters if stock in quarter_stocks.get(q, set()))
        if count >= 3:
            persistent_stocks.append(stock)
    
    stability_ratio = len(persistent_stocks) / len(all_stocks) if all_stocks else 0
    
    # 4. 投资风格判断
    style = "未知"
    if stability_ratio > 0.6:
        style = "长期持有型"
    elif stability_ratio < 0.3:
        style = "高频调仓型"
    else:
        style = "平衡型"
    
    # 保存分析结果
    result = {
        'ts_code': code,
        'name': name,
        'category': category,
        'quality_score': quality_score,
        'return_1y': return_1y,
        'sharpe': sharpe,
        'quarters': list(quarters),
        'quarter_stats': quarter_stats,
        'industries': industries,
        'total_stocks': len(all_stocks),
        'persistent_stocks': len(persistent_stocks),
        'stability_ratio': round(stability_ratio, 2),
        'investment_style': style
    }
    
    analysis_results.append(result)
    
    print(f"  ✓ 风格: {style} | 重仓股稳定性: {stability_ratio:.1%} | 季度数: {len(quarters)}")

print()
print(f"分析完成: {len(analysis_results)} 只基金")
print()

# 保存分析结果
with open('/root/.openclaw/workspace/fund_data/analysis/deep_analysis_results.json', 'w', encoding='utf-8') as f:
    json.dump(analysis_results, f, ensure_ascii=False, indent=2)

# 生成摘要报告
summary = {
    'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'total_analyzed': len(analysis_results),
    'style_distribution': {},
    'category_distribution': {},
    'avg_stability': 0,
    'top_funds': []
}

# 风格分布
for r in analysis_results:
    style = r['investment_style']
    summary['style_distribution'][style] = summary['style_distribution'].get(style, 0) + 1
    
    cat = r['category']
    summary['category_distribution'][cat] = summary['category_distribution'].get(cat, 0) + 1

# 平均稳定性
summary['avg_stability'] = round(sum(r['stability_ratio'] for r in analysis_results) / len(analysis_results), 2)

# TOP10基金（按质量分+稳定性综合）
for r in analysis_results:
    r['composite_score'] = r['quality_score'] * 0.7 + r['stability_ratio'] * 100 * 0.3

top10 = sorted(analysis_results, key=lambda x: x['composite_score'], reverse=True)[:10]
summary['top_funds'] = [
    {
        'ts_code': r['ts_code'],
        'name': r['name'],
        'category': r['category'],
        'quality_score': r['quality_score'],
        'stability_ratio': r['stability_ratio'],
        'style': r['investment_style'],
        'return_1y': r['return_1y']
    }
    for r in top10
]

with open('/root/.openclaw/workspace/fund_data/analysis/analysis_summary.json', 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

# 输出报告
print("="*70)
print("【深度分析摘要】")
print("="*70)
print(f"分析基金数: {summary['total_analyzed']} 只")
print(f"平均重仓股稳定性: {summary['avg_stability']:.1%}")
print()

print("【投资风格分布】")
for style, count in summary['style_distribution'].items():
    print(f"  {style}: {count}只")
print()

print("【类别分布】")
for cat, count in summary['category_distribution'].items():
    print(f"  {cat}: {count}只")
print()

print("【TOP10基金（质量+稳定性综合）】")
for i, fund in enumerate(summary['top_funds'], 1):
    print(f"{i}. {fund['ts_code']}: {fund['name'][:25]} | {fund['category']} | "
          f"收益:{fund['return_1y']:.1f}% | 风格:{fund['style']} | 稳定性:{fund['stability_ratio']:.1%}")

print()
print("="*70)
print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)
