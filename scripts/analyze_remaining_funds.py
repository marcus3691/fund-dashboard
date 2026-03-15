#!/usr/bin/env python3
"""
核心库剩余基金全面分析
目标：162只基金（95只深度分析+67只标准档案）
"""

import pandas as pd
import json
from datetime import datetime
import os

print("="*70)
print("核心库剩余基金全面分析")
print("="*70)
print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 加载核心库所有基金
df_core = pd.read_csv('/root/.openclaw/workspace/fund_data/fund_core_library.csv')

# 加载已分析的基金
with open('/root/.openclaw/workspace/fund_data/analysis/deep_analysis_results_v2.json', 'r') as f:
    analyzed = json.load(f)
analyzed_codes = [a['ts_code'] for a in analyzed]

# 找出未分析的基金
df_remaining = df_core[~df_core['ts_code'].isin(analyzed_codes)].copy()
print(f"待分析基金: {len(df_remaining)} 只")

# 加载持仓数据
df_holdings = pd.read_csv('/root/.openclaw/workspace/fund_data/holdings/core_library_holdings.csv')
codes_with_data = set(df_holdings['fund_code'].unique())

# 分离有持仓数据和无持仓数据的基金
df_with_data = df_remaining[df_remaining['ts_code'].isin(codes_with_data)].copy()
df_without_data = df_remaining[~df_remaining['ts_code'].isin(codes_with_data)].copy()

print(f"  - 有持仓数据（深度分析）: {len(df_with_data)} 只")
print(f"  - 无持仓数据（标准档案）: {len(df_without_data)} 只")
print()

# 创建输出目录
os.makedirs('/root/.openclaw/workspace/fund_data/analysis/funds', exist_ok=True)

all_results = analyzed.copy()  # 包含之前分析的32只

# ============================================================
# 第一部分：深度分析（有持仓数据的95只）
# ============================================================
print("【第一部分】深度分析（有持仓数据）...")
print()

deep_analysis_count = 0
for idx, fund in df_with_data.iterrows():
    code = fund['ts_code']
    name = fund['name']
    category = fund['category']
    quality_score = fund['quality_score']
    return_1y = fund['return_1y']
    sharpe = fund['sharpe']
    volatility = fund['volatility']
    max_drawdown = fund['max_drawdown']
    
    # 获取持仓数据
    fund_holdings = df_holdings[df_holdings['fund_code'] == code].copy()
    
    if fund_holdings.empty:
        continue
    
    # 季度分析
    quarters = sorted(fund_holdings['quarter'].unique())
    quarter_stats = {}
    
    for q in quarters:
        q_data = fund_holdings[fund_holdings['quarter'] == q].sort_values('stk_mkv_ratio', ascending=False)
        if not q_data.empty:
            quarter_stats[q] = {
                'stocks_count': len(q_data),
                'top10_ratio': round(q_data['stk_mkv_ratio'].sum(), 2),
                'top_stock': q_data.iloc[0]['symbol'],
                'top_ratio': round(q_data.iloc[0]['stk_mkv_ratio'], 2)
            }
    
    # 重仓股稳定性
    all_stocks = set()
    quarter_stocks = {}
    for q in quarters:
        q_data = fund_holdings[fund_holdings['quarter'] == q]
        stocks = set(q_data['symbol'].tolist())
        quarter_stocks[q] = stocks
        all_stocks.update(stocks)
    
    persistent_stocks = []
    for stock in all_stocks:
        count = sum(1 for q in quarters if stock in quarter_stocks.get(q, set()))
        if count >= 3:
            persistent_stocks.append(stock)
    
    stability_ratio = len(persistent_stocks) / len(all_stocks) if all_stocks else 0
    
    # 投资风格
    if stability_ratio >= 0.5:
        style = "长期持有型"
    elif stability_ratio <= 0.1:
        style = "高频调仓型"
    else:
        style = "平衡型"
    
    result = {
        'ts_code': code,
        'name': name,
        'category': category,
        'analysis_type': '深度分析',
        'quality_score': quality_score,
        'return_1y': return_1y,
        'sharpe': sharpe,
        'volatility': volatility,
        'max_drawdown': max_drawdown,
        'quarters': quarters,
        'quarter_stats': quarter_stats,
        'total_stocks': len(all_stocks),
        'persistent_stocks': len(persistent_stocks),
        'stability_ratio': round(stability_ratio, 2),
        'investment_style': style
    }
    
    all_results.append(result)
    deep_analysis_count += 1
    
    # 保存单独档案
    with open(f'/root/.openclaw/workspace/fund_data/analysis/funds/{code}_profile.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    if deep_analysis_count % 20 == 0:
        print(f"  已完成: {deep_analysis_count}/{len(df_with_data)}")

print(f"  深度分析完成: {deep_analysis_count} 只")
print()

# ============================================================
# 第二部分：标准档案（无持仓数据的67只）
# ============================================================
print("【第二部分】标准档案（无持仓数据）...")
print()

standard_count = 0
for idx, fund in df_without_data.iterrows():
    code = fund['ts_code']
    name = fund['name']
    category = fund['category']
    
    result = {
        'ts_code': code,
        'name': name,
        'category': category,
        'analysis_type': '标准档案',
        'quality_score': fund['quality_score'],
        'return_1y': fund['return_1y'],
        'sharpe': fund['sharpe'],
        'volatility': fund['volatility'],
        'max_drawdown': fund['max_drawdown'],
        'quarters': [],
        'quarter_stats': {},
        'total_stocks': None,
        'persistent_stocks': None,
        'stability_ratio': None,
        'investment_style': '待补充',
        'note': '缺少季度持仓数据，建议后续补录'
    }
    
    all_results.append(result)
    standard_count += 1
    
    # 保存单独档案
    with open(f'/root/.openclaw/workspace/fund_data/analysis/funds/{code}_profile.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    if standard_count % 20 == 0:
        print(f"  已完成: {standard_count}/{len(df_without_data)}")

print(f"  标准档案完成: {standard_count} 只")
print()

# ============================================================
# 第三部分：保存完整档案库
# ============================================================
print("【第三部分】保存完整档案库...")

# 保存所有194只基金的完整档案
with open('/root/.openclaw/workspace/fund_data/analysis/core_library_full_profiles.json', 'w', encoding='utf-8') as f:
    json.dump(all_results, f, ensure_ascii=False, indent=2)

# 生成CSV汇总
df_profiles = pd.DataFrame(all_results)
df_profiles.to_csv('/root/.openclaw/workspace/fund_data/analysis/core_library_profiles.csv', index=False, encoding='utf-8-sig')

# 生成摘要
summary = {
    'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'total_funds': len(all_results),
    'deep_analysis': deep_analysis_count,
    'standard_profiles': standard_count,
    'previous_analyzed': len(analyzed),
    'categories': {}
}

for cat in df_core['category'].unique():
    cat_count = len([r for r in all_results if r['category'] == cat])
    summary['categories'][cat] = cat_count

with open('/root/.openclaw/workspace/fund_data/analysis/full_analysis_summary.json', 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print(f"  完整档案库已保存: {len(all_results)} 只基金")
print()

# ============================================================
# 输出报告
# ============================================================
print("="*70)
print("【全面分析完成】")
print("="*70)
print(f"核心库基金总数: {summary['total_funds']} 只")
print(f"  - 深度分析（有持仓）: {summary['deep_analysis']} 只")
print(f"  - 标准档案（无持仓）: {summary['standard_profiles']} 只")
print()

print("【类别分布】")
for cat, count in summary['categories'].items():
    print(f"  {cat}: {count}只")
print()

print("【生成文件】")
print(f"  - core_library_full_profiles.json（194只完整档案）")
print(f"  - core_library_profiles.csv（汇总表）")
print(f"  - funds/*_profile.json（194只单独档案）")
print()

print("="*70)
print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)
