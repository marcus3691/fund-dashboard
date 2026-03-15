#!/usr/bin/env python3
"""
核心库基金深度分析 - 修正版
目标：50只基金，季度持仓演变、行业分布、投资风格分析
"""

import pandas as pd
import json
from datetime import datetime
import os

print("="*70)
print("核心库基金深度分析 - 修正版")
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
    quarters = sorted(fund_holdings['quarter'].unique())
    quarter_stats = {}
    
    for q in quarters:
        q_data = fund_holdings[fund_holdings['quarter'] == q]
        if not q_data.empty:
            # 按持仓占比排序
            q_data = q_data.sort_values('stk_mkv_ratio', ascending=False)
            quarter_stats[q] = {
                'stocks_count': len(q_data),
                'top10_ratio': q_data['stk_mkv_ratio'].sum(),
                'top_stock': q_data.iloc[0]['symbol'],
                'top_stock_name': q_data.iloc[0].get('name', ''),  # 如果有name字段
                'top_ratio': q_data.iloc[0]['stk_mkv_ratio']
            }
    
    # 2. 重仓股稳定性分析（使用symbol字段）
    all_stocks = set()
    quarter_stocks = {}
    
    for q in quarters:
        q_data = fund_holdings[fund_holdings['quarter'] == q]
        stocks = set(q_data['symbol'].tolist())
        quarter_stocks[q] = stocks
        all_stocks.update(stocks)
    
    # 计算持续重仓股（出现在3个季度以上的）
    stock_quarter_count = {}
    for stock in all_stocks:
        count = sum(1 for q in quarters if stock in quarter_stocks.get(q, set()))
        stock_quarter_count[stock] = count
    
    persistent_stocks = [s for s, c in stock_quarter_count.items() if c >= 3]
    
    stability_ratio = len(persistent_stocks) / len(all_stocks) if all_stocks else 0
    
    # 3. 投资风格判断
    if stability_ratio >= 0.5:
        style = "长期持有型"
    elif stability_ratio <= 0.1:
        style = "高频调仓型"
    else:
        style = "平衡型"
    
    # 4. 行业分析（如果有行业数据）
    # 这里简化，实际需要行业映射表
    
    # 保存分析结果
    result = {
        'ts_code': code,
        'name': name,
        'category': category,
        'quality_score': quality_score,
        'return_1y': return_1y,
        'sharpe': sharpe,
        'quarters': quarters,
        'quarter_stats': quarter_stats,
        'total_stocks': len(all_stocks),
        'persistent_stocks': len(persistent_stocks),
        'persistent_stock_list': persistent_stocks[:5],  # 只保存前5只
        'stability_ratio': round(stability_ratio, 2),
        'investment_style': style
    }
    
    analysis_results.append(result)
    
    print(f"  ✓ 风格: {style} | 重仓股稳定性: {stability_ratio:.1%} | 持续重仓股: {len(persistent_stocks)}只")

print()
print(f"分析完成: {len(analysis_results)} 只基金")
print()

# 保存分析结果
with open('/root/.openclaw/workspace/fund_data/analysis/deep_analysis_results_v2.json', 'w', encoding='utf-8') as f:
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
        'persistent_stocks': r['persistent_stocks'],
        'style': r['investment_style'],
        'return_1y': r['return_1y']
    }
    for r in top10
]

with open('/root/.openclaw/workspace/fund_data/analysis/analysis_summary_v2.json', 'w', encoding='utf-8') as f:
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
    print(f"{i}. {fund['ts_code']}: {fund['name'][:25]} | {fund['category']}")
    print(f"   收益:{fund['return_1y']:.1f}% | 质量分:{fund['quality_score']:.1f} | 风格:{fund['style']} | 稳定性:{fund['stability_ratio']:.1%} | 持续重仓:{fund['persistent_stocks']}只")

print()
print("="*70)
print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)
