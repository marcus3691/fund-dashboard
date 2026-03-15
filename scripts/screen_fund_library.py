#!/usr/bin/env python3
"""
产品库筛选脚本 - 基于入库标准
目标：从6,288只基金中筛选核心库/观察库/备选库
"""

import sqlite3
import pandas as pd
import numpy as np
import json
from datetime import datetime

print("="*70)
print("基金产品库筛选")
print("="*70)
print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 连接数据库
db_path = '/root/.openclaw/workspace/fund_data/volatility_db/fund_priority.db'
conn = sqlite3.connect(db_path)
df = pd.read_sql_query('SELECT * FROM fund_basic', conn)
conn.close()

print(f"总基金数量: {len(df)} 只")
print(f"类别分布:")
print(df['category'].value_counts())
print()

# 数据清洗 - 去除无效数据
df_clean = df[df['return_1y'].notna()].copy()
df_clean = df_clean[df_clean['volatility'] > 0].copy()

print(f"有效数据: {len(df_clean)} 只 (去除{len(df)-len(df_clean)}只无效数据)")
print()

# ============================================================
# 第一步：按类别计算排名百分位
# ============================================================
print("【第一步】计算类别内排名百分位...")

target_categories = ['主动股票型', '混合型-偏股', '混合型-平衡']

for category in target_categories:
    cat_df = df_clean[df_clean['category'] == category].copy()
    if len(cat_df) == 0:
        continue
    
    # 1年收益排名（降序）
    cat_df = cat_df.sort_values('return_1y', ascending=False).reset_index(drop=True)
    cat_df['rank_1y'] = range(1, len(cat_df) + 1)
    cat_df['percentile_1y'] = (1 - (cat_df['rank_1y'] - 1) / len(cat_df)) * 100
    
    # 6个月收益排名
    cat_df_valid_6m = cat_df[cat_df['return_6m'].notna()].copy()
    if len(cat_df_valid_6m) > 0:
        cat_df_valid_6m = cat_df_valid_6m.sort_values('return_6m', ascending=False).reset_index(drop=True)
        cat_df_valid_6m['rank_6m'] = range(1, len(cat_df_valid_6m) + 1)
        cat_df_valid_6m['percentile_6m'] = (1 - (cat_df_valid_6m['rank_6m'] - 1) / len(cat_df_valid_6m)) * 100
        
        # 合并回主表
        for idx, row in cat_df_valid_6m.iterrows():
            mask = (df_clean['ts_code'] == row['ts_code']) & (df_clean['category'] == category)
            df_clean.loc[mask, 'rank_6m'] = row['rank_6m']
            df_clean.loc[mask, 'percentile_6m'] = row['percentile_6m']
    
    # 合并1年排名
    for idx, row in cat_df.iterrows():
        mask = (df_clean['ts_code'] == row['ts_code']) & (df_clean['category'] == category)
        df_clean.loc[mask, 'rank_1y'] = row['rank_1y']
        df_clean.loc[mask, 'percentile_1y'] = row['percentile_1y']

print("  排名计算完成")
print()

# ============================================================
# 第二步：计算质量评分
# ============================================================
print("【第二步】计算质量评分...")

def calc_quality_score(row):
    """计算综合质量评分 (0-100)"""
    score = 0
    
    # 夏普比率 (30分) - 越高越好
    sharpe = row.get('sharpe', 0) or 0
    if sharpe >= 2:
        score += 30
    elif sharpe >= 1:
        score += 20 + (sharpe - 1) * 10
    elif sharpe >= 0:
        score += sharpe * 20
    else:
        score += max(0, 10 + sharpe * 10)
    
    # 最大回撤 (25分) - 越小越好
    mdd = row.get('max_drawdown', 50) or 50
    if mdd <= 10:
        score += 25
    elif mdd <= 30:
        score += 25 - (mdd - 10) * 0.75
    else:
        score += max(0, 10 - (mdd - 30) * 0.25)
    
    # 波动率 (20分) - 适中最好 (10-20%)
    vol = row.get('volatility', 20) or 20
    if 10 <= vol <= 20:
        score += 20
    elif vol < 10:
        score += 15 + vol * 0.5
    elif vol <= 30:
        score += 20 - (vol - 20) * 0.5
    else:
        score += max(5, 15 - (vol - 30) * 0.2)
    
    # 1年收益排名 (15分) - 在同类别中的排名
    pct = row.get('percentile_1y', 50) or 50
    score += min(15, pct / 100 * 15)
    
    # 卡玛比率替代盈亏比 (10分) - 收益/回撤
    ret = row.get('return_1y', 0) or 0
    mdd_for_calmar = max(mdd, 1)  # 避免除0
    calmar = abs(ret) / mdd_for_calmar if mdd_for_calmar > 0 else 0
    if ret > 0:
        score += min(10, calmar * 5)
    else:
        score += 0
    
    return round(score, 1)

df_clean['quality_score'] = df_clean.apply(calc_quality_score, axis=1)

print("  质量评分计算完成")
print(f"  平均分: {df_clean['quality_score'].mean():.1f}")
print(f"  中位数: {df_clean['quality_score'].median():.1f}")
print()

# ============================================================
# 第三步：应用入库标准
# ============================================================
print("【第三步】应用入库标准...")
print()

# 一级筛选（必须全部满足）
print("  一级筛选（必须全部满足）:")
print("    - 近1年收益排名前10%")
print("    - 近6个月收益排名前20%（如有数据）")
print("    - 有完整1年数据")

# 条件1：1年排名前10%
cond1 = df_clean['percentile_1y'] >= 90

# 条件2：6个月排名前20%（如有数据）
cond2 = (df_clean['percentile_6m'] >= 80) | (df_clean['percentile_6m'].isna())

# 条件3：有完整数据
df_stage1 = df_clean[cond1 & cond2].copy()

print(f"    通过一级筛选: {len(df_stage1)} 只")
print()

# 二级筛选（质量评分）
print("  二级筛选（质量评分≥70分）:")
df_stage2 = df_stage1[df_stage1['quality_score'] >= 70].copy()
print(f"    通过二级筛选: {len(df_stage2)} 只")
print()

# 一票否决项（简化版，缺少部分数据）
print("  一票否决项（简化检查）:")
print("    - 波动率 > 同类别90%分位")

# 按类别计算波动率90%分位
for category in target_categories:
    cat_mask = df_stage2['category'] == category
    if cat_mask.sum() == 0:
        continue
    vol_90 = df_stage2[cat_mask]['volatility'].quantile(0.9)
    extreme_vol_mask = (df_stage2['category'] == category) & (df_stage2['volatility'] > vol_90)
    df_stage2.loc[extreme_vol_mask, 'veto_reason'] = '波动率过高'

# 去除被否决的
df_final = df_stage2[df_stage2['veto_reason'].isna()].copy() if 'veto_reason' in df_stage2.columns else df_stage2.copy()

print(f"    通过一票否决: {len(df_final)} 只")
print()

# ============================================================
# 第四步：产品库分级
# ============================================================
print("【第四步】产品库分级...")
print()

# 核心库：质量分≥80 + 连续表现优异
df_core = df_final[df_final['quality_score'] >= 80].copy()

# 观察库：质量分70-80
df_watch = df_final[(df_final['quality_score'] >= 70) & (df_final['quality_score'] < 80)].copy()

print(f"  核心库（质量分≥80）: {len(df_core)} 只")
print(f"  观察库（质量分70-80）: {len(df_watch)} 只")
print()

# ============================================================
# 第五步：输出结果
# ============================================================
print("【第五步】保存结果...")

# 保存完整筛选结果
df_clean.to_csv('/root/.openclaw/workspace/fund_data/fund_screening_all.csv', index=False, encoding='utf-8-sig')

# 保存各级别库
if len(df_core) > 0:
    df_core.to_csv('/root/.openclaw/workspace/fund_data/fund_core_library.csv', index=False, encoding='utf-8-sig')
    
if len(df_watch) > 0:
    df_watch.to_csv('/root/.openclaw/workspace/fund_data/fund_watch_library.csv', index=False, encoding='utf-8-sig')

df_final.to_csv('/root/.openclaw/workspace/fund_data/fund_selected.csv', index=False, encoding='utf-8-sig')

# 生成摘要
summary = {
    'screening_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'total_funds': len(df),
    'valid_funds': len(df_clean),
    'stage1_pass': len(df_stage1),
    'stage2_pass': len(df_stage2),
    'final_selected': len(df_final),
    'core_library': len(df_core),
    'watch_library': len(df_watch),
    'categories': {}
}

for cat in target_categories:
    cat_data = {
        'total': len(df_clean[df_clean['category'] == cat]),
        'selected': len(df_final[df_final['category'] == cat]),
        'core': len(df_core[df_core['category'] == cat]) if len(df_core) > 0 else 0,
        'avg_score': round(df_clean[df_clean['category'] == cat]['quality_score'].mean(), 1)
    }
    summary['categories'][cat] = cat_data

with open('/root/.openclaw/workspace/fund_data/screening_summary.json', 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print("  结果已保存")
print()

# ============================================================
# 输出关键发现
# ============================================================
print("="*70)
print("【筛选结果汇总】")
print("="*70)
print(f"总基金数量: {summary['total_funds']} 只")
print(f"有效数据: {summary['valid_funds']} 只")
print(f"一级筛选通过: {summary['stage1_pass']} 只")
print(f"二级筛选通过: {summary['stage2_pass']} 只")
print(f"最终入选: {summary['final_selected']} 只")
print()
print(f"核心库（质量分≥80）: {summary['core_library']} 只")
print(f"观察库（质量分70-80）: {summary['watch_library']} 只")
print()

print("【各类别入选情况】")
for cat, data in summary['categories'].items():
    print(f"  {cat}:")
    print(f"    总数: {data['total']}只 | 入选: {data['selected']}只 | 核心库: {data['core']}只 | 平均质量分: {data['avg_score']}")

print()

# 输出核心库TOP10
if len(df_core) > 0:
    print("【核心库TOP10（按质量分）】")
    top10 = df_core.nlargest(10, 'quality_score')[['ts_code', 'name', 'category', 'return_1y', 'sharpe', 'quality_score']]
    for idx, row in top10.iterrows():
        print(f"  {row['ts_code']}: {row['name'][:20]} | {row['category']} | 收益:{row['return_1y']:.1f}% | 质量分:{row['quality_score']}")

print()
print("="*70)
print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)
