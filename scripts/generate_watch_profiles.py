#!/usr/bin/env python3
"""
观察库基金标准档案生成
目标：116只基金，基于现有净值数据生成标准档案
预计耗时：30分钟
"""

import pandas as pd
import json
from datetime import datetime
import os

print("="*70)
print("观察库基金标准档案生成")
print("="*70)
print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 加载观察库基金
df_watch = pd.read_csv('/root/.openclaw/workspace/fund_data/watch_missing_profiles.csv')
print(f"目标基金: {len(df_watch)} 只")
print()

# 加载已有档案
with open('/root/.openclaw/workspace/fund_data/analysis/core_library_full_profiles.json', 'r') as f:
    all_profiles = json.load(f)

# 为每只观察库基金生成标准档案
new_profiles = []

for idx, fund in df_watch.iterrows():
    code = fund['ts_code']
    name = fund['name']
    
    profile = {
        'ts_code': code,
        'name': name,
        'category': fund['category'],
        'analysis_type': '标准档案',
        'quality_score': fund['quality_score'],
        'return_1y': fund['return_1y'],
        'return_6m': fund.get('return_6m'),
        'return_3m': fund.get('return_3m'),
        'sharpe': fund['sharpe'],
        'volatility': fund['volatility'],
        'max_drawdown': fund['max_drawdown'],
        'percentile_1y': fund.get('percentile_1y'),
        'rank_1y': fund.get('rank_1y'),
        'quarters': [],
        'quarter_stats': {},
        'total_stocks': None,
        'persistent_stocks': None,
        'stability_ratio': None,
        'investment_style': '待深度分析',
        'note': '观察库基金，建议后续获取持仓数据进行深度分析',
        'data_status': 'pending_deep_analysis'
    }
    
    new_profiles.append(profile)
    
    if (idx + 1) % 20 == 0:
        print(f"  已生成: {idx+1}/{len(df_watch)}")

# 合并档案
all_profiles.extend(new_profiles)

# 保存更新后的完整档案
with open('/root/.openclaw/workspace/fund_data/analysis/core_library_full_profiles.json', 'w', encoding='utf-8') as f:
    json.dump(all_profiles, f, ensure_ascii=False, indent=2)

# 更新CSV
df_all = pd.DataFrame(all_profiles)
df_all.to_csv('/root/.openclaw/workspace/fund_data/analysis/core_library_profiles.csv', 
              index=False, encoding='utf-8-sig')

print()
print(f"标准档案生成完成: {len(new_profiles)} 只")
print(f"总档案数: {len(all_profiles)} 只")
print()
print("="*70)
print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)
