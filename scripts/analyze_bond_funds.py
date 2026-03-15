#!/usr/bin/env python3
"""
债券型产品库深度分析报告生成
目标：18只债券型基金
"""

import pandas as pd
import json
from datetime import datetime

print("="*70)
print("债券型产品库深度分析报告生成")
print("="*70)
print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 加载债券型基金列表（从完整数据中获取）
df_bond_full = pd.read_csv('/root/.openclaw/workspace/fund_data/fund_bond.csv')
df_bond_list = pd.read_csv('/root/.openclaw/workspace/fund_data/bond_analysis_list.csv')

# 合并获取完整数据
df_bond = df_bond_list.merge(df_bond_full[['ts_code', 'return_1y', 'sharpe', 'volatility', 'max_drawdown']], 
                              on='ts_code', how='left')

# 加载持仓数据
df_holdings = pd.read_csv('/root/.openclaw/workspace/fund_data/holdings/bond_selected_holdings.csv')
print(f"持仓数据: {len(df_holdings)} 条记录")
print()

# 加载完整档案
with open('/root/.openclaw/workspace/fund_data/analysis/core_library_full_profiles.json', 'r') as f:
    all_profiles = json.load(f)

# 为每只债券型基金生成深度分析
bond_profiles = []

for idx, fund in df_bond.iterrows():
    code = fund['ts_code']
    name = fund['name']
    
    # 获取持仓数据
    fund_holdings = df_holdings[df_holdings['fund_code'] == code].copy()
    
    if fund_holdings.empty:
        # 无持仓数据，生成标准档案
        profile = {
            'ts_code': code,
            'name': name,
            'category': '债券型-主动',
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
            'note': '债券型基金，持仓数据待补充'
        }
    else:
        # 有持仓数据，生成深度分析
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
        
        # 重仓股稳定性（债券型基金可能持仓较多，放宽标准）
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
            if count >= 2:  # 债券型基金放宽到2个季度
                persistent_stocks.append(stock)
        
        stability_ratio = len(persistent_stocks) / len(all_stocks) if all_stocks else 0
        
        # 债券型基金风格
        if stability_ratio >= 0.4:
            style = "长期持有型"
        elif stability_ratio <= 0.15:
            style = "高频调仓型"
        else:
            style = "平衡型"
        
        profile = {
            'ts_code': code,
            'name': name,
            'category': '债券型-主动',
            'analysis_type': '深度分析',
            'quality_score': fund['quality_score'],
            'return_1y': fund['return_1y'],
            'sharpe': fund['sharpe'],
            'volatility': fund['volatility'],
            'max_drawdown': fund['max_drawdown'],
            'quarters': quarters,
            'quarter_stats': quarter_stats,
            'total_stocks': len(all_stocks),
            'persistent_stocks': len(persistent_stocks),
            'stability_ratio': round(stability_ratio, 2),
            'investment_style': style
        }
    
    bond_profiles.append(profile)
    print(f"  {code}: {name[:25]} | {profile['analysis_type']} | 风格:{profile.get('investment_style', 'N/A')}")

# 合并到总档案
all_profiles.extend(bond_profiles)

# 保存更新后的完整档案
with open('/root/.openclaw/workspace/fund_data/analysis/core_library_full_profiles.json', 'w', encoding='utf-8') as f:
    json.dump(all_profiles, f, ensure_ascii=False, indent=2)

# 更新CSV
df_all = pd.DataFrame(all_profiles)
df_all.to_csv('/root/.openclaw/workspace/fund_data/analysis/core_library_profiles.csv', 
              index=False, encoding='utf-8-sig')

# 保存债券型单独档案
with open('/root/.openclaw/workspace/fund_data/analysis/bond_profiles.json', 'w', encoding='utf-8') as f:
    json.dump(bond_profiles, f, ensure_ascii=False, indent=2)

print()
print(f"债券型分析报告生成完成: {len(bond_profiles)} 只")
print(f"总档案数: {len(all_profiles)} 只")
print()

# 统计
deep_count = len([p for p in bond_profiles if p['analysis_type'] == '深度分析'])
standard_count = len([p for p in bond_profiles if p['analysis_type'] == '标准档案'])
print(f"  - 深度分析: {deep_count} 只")
print(f"  - 标准档案: {standard_count} 只")

print()
print("="*70)
print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)
