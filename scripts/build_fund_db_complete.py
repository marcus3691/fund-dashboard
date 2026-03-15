#!/usr/bin/env python3
"""
全市场基金指标计算脚本 - 修复版
计算收益指标（3m/6m/1y/2y/3y）、风险指标、质量评分
"""

import tushare as ts
import tushare.pro.client as client
import pandas as pd
import numpy as np
import json
import sqlite3
import time
from datetime import datetime, timedelta

# Tushare配置
client.DataApi._DataApi__http_url = 'http://tushare.xyz'
pro = ts.pro_api('080afaf41dbb746406290078112f271e50e79a0858c9494bb52a1ec1')

print("="*70)
print("基金数据库建设 - 全市场指标计算")
print("="*70)
print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 创建输出目录
import os
os.makedirs('/root/.openclaw/workspace/fund_data', exist_ok=True)
os.makedirs('/root/.openclaw/workspace/fund_data/volatility_db', exist_ok=True)

# 定义基金分类映射
FUND_CATEGORIES = {
    '股票型': '主动股票型',
    '成长型': '主动股票型', 
    '价值型': '主动股票型',
    '积极成长型': '主动股票型',
    '稳健增长型': '主动股票型',
    '科技型': '主动股票型',
    '创新型': '主动股票型',
    '混合型': '混合型-偏股',
    '灵活配置型': '混合型-平衡',
    '平衡型': '混合型-平衡',
    '主题型': '混合型-偏股',
    '积极配置型': '混合型-偏股',
    '强化收益型': '混合型-偏债',
    '稳定型': '债券型-主动',
    '债券型': '债券型-主动',
    'FOF': 'FOF',
    '被动指数型': '指数型',
    '增强指数型': '指数增强型',
    'QDII': 'QDII'
}

# 获取日期
today = datetime.now()
dates = {
    '3m': (today - timedelta(days=90)).strftime('%Y%m%d'),
    '6m': (today - timedelta(days=180)).strftime('%Y%m%d'),
    '1y': (today - timedelta(days=365)).strftime('%Y%m%d'),
    '2y': (today - timedelta(days=730)).strftime('%Y%m%d'),
    '3y': (today - timedelta(days=1095)).strftime('%Y%m%d'),
}
print("计算周期日期:")
for k, v in dates.items():
    print(f"  {k}: {v}")
print()

# 第一步：获取基金列表
print("【第一步】获取基金列表...")
df_funds = pro.fund_basic(market='E')

# 筛选有效的主动管理基金（上市状态）
active_funds = df_funds[df_funds['status'] == 'L'].copy()

# 映射到8大类别
active_funds['category'] = active_funds['invest_type'].map(FUND_CATEGORIES)
active_funds['category'] = active_funds['category'].fillna('其他')

# 我们重点关注的8个类别
target_categories = ['主动股票型', '混合型-偏股', '混合型-平衡', '混合型-偏债', 
                     'FOF', '指数增强型', '债券型-主动', 'QDII']
target_funds = active_funds[active_funds['category'].isin(target_categories)].copy()

print(f"全部上市基金: {len(active_funds)} 只")
print(f"目标类别基金: {len(target_funds)} 只")
print()
print("类别分布:")
print(target_funds['category'].value_counts())
print()

# 第二步：计算每只基金的多周期指标
print("【第二步】计算多周期收益和风险指标...")
print("预计耗时: 60-120分钟（取决于基金数量和网络速度）")
print()

fund_records = []
failed_funds = []
total = len(target_funds)

# 批量处理，每50只保存一次中间结果
batch_size = 50
batch_num = 0

for i, (idx, row) in enumerate(target_funds.iterrows()):
    code = row['ts_code']
    name = row['name']
    fund_type = row['invest_type']
    category = row['category']
    
    try:
        # 获取历史净值数据（最近3年）
        df_nav = pro.fund_nav(ts_code=code, start_date=dates['3y'], end_date=today.strftime('%Y%m%d'))
        
        if df_nav.empty or len(df_nav) < 60:  # 至少需要60个数据点
            failed_funds.append({'code': code, 'name': name, 'reason': '数据不足'})
            continue
        
        # 数据预处理
        df_nav = df_nav.sort_values('nav_date')
        df_nav['nav_date'] = pd.to_datetime(df_nav['nav_date'])
        df_nav = df_nav.drop_duplicates(subset=['nav_date'], keep='first')
        df_nav = df_nav.set_index('nav_date')
        
        # 计算日收益率
        df_nav['daily_return'] = df_nav['unit_nav'].pct_change()
        
        # 获取最新净值
        latest_nav = df_nav['unit_nav'].iloc[-1]
        latest_date = df_nav.index[-1]
        
        # 计算各周期收益
        def calc_return(df, days):
            try:
                target_date = df.index[-1] - timedelta(days=days)
                past_nav = df[df.index <= target_date]['unit_nav'].iloc[-1]
                return (latest_nav - past_nav) / past_nav * 100
            except:
                return None
        
        returns = {
            'return_3m': calc_return(df_nav, 90),
            'return_6m': calc_return(df_nav, 180),
            'return_1y': calc_return(df_nav, 365),
            'return_2y': calc_return(df_nav, 730),
            'return_3y': calc_return(df_nav, 1095),
        }
        
        # 计算风险指标（基于最近1年数据）
        one_year_ago = df_nav.index[-1] - timedelta(days=365)
        recent_returns = df_nav[df_nav.index >= one_year_ago]['daily_return'].dropna()
        
        if len(recent_returns) < 30:
            failed_funds.append({'code': code, 'name': name, 'reason': '近期数据不足'})
            continue
        
        # 年化波动率
        volatility = recent_returns.std() * np.sqrt(252) * 100
        
        # 最大回撤（基于最近1年）
        recent_nav = df_nav[df_nav.index >= one_year_ago]['unit_nav']
        cummax = recent_nav.cummax()
        drawdown = (cummax - recent_nav) / cummax
        max_drawdown = drawdown.max() * 100
        
        # 夏普比率（简化：无风险利率2%）
        annual_return = returns['return_1y'] if returns['return_1y'] else 0
        sharpe = (annual_return - 2) / volatility if volatility > 0 else 0
        
        # 月度胜率（最近1年）
        monthly_returns = df_nav['unit_nav'].resample('M').last().pct_change().dropna()
        if len(monthly_returns) >= 6:
            monthly_win_rate = (monthly_returns > 0).mean() * 100
        else:
            monthly_win_rate = None
        
        # 盈亏比
        daily_rets = recent_returns
        avg_gain = daily_rets[daily_rets > 0].mean() if (daily_rets > 0).any() else 0
        avg_loss = abs(daily_rets[daily_rets < 0].mean()) if (daily_rets < 0).any() else 0.001
        profit_loss_ratio = avg_gain / avg_loss if avg_loss > 0 else 0
        
        fund_records.append({
            'ts_code': code,
            'name': name,
            'invest_type': fund_type,
            'category': category,
            'return_3m': round(returns['return_3m'], 2) if returns['return_3m'] else None,
            'return_6m': round(returns['return_6m'], 2) if returns['return_6m'] else None,
            'return_1y': round(returns['return_1y'], 2) if returns['return_1y'] else None,
            'return_2y': round(returns['return_2y'], 2) if returns['return_2y'] else None,
            'return_3y': round(returns['return_3y'], 2) if returns['return_3y'] else None,
            'volatility': round(volatility, 2),
            'max_drawdown': round(max_drawdown, 2),
            'sharpe': round(sharpe, 2),
            'monthly_win_rate': round(monthly_win_rate, 2) if monthly_win_rate else None,
            'profit_loss_ratio': round(profit_loss_ratio, 2),
            'data_points': len(df_nav),
            'latest_nav': latest_nav,
            'latest_date': latest_date.strftime('%Y-%m-%d')
        })
        
        # 每10只报告进度
        if (i + 1) % 10 == 0:
            elapsed = (datetime.now() - datetime.strptime(
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S'
            )).total_seconds() if False else 0
            print(f"  进度: {i+1}/{total} ({(i+1)/total*100:.1f}%) | "
                  f"成功: {len(fund_records)} | 失败: {len(failed_funds)}")
        
        # 每50只暂停一下，避免API限制
        if (i + 1) % 50 == 0:
            time.sleep(1)
            
        # 每100只保存中间结果
        if (i + 1) % batch_size == 0:
            batch_num += 1
            df_temp = pd.DataFrame(fund_records)
            df_temp.to_csv(f'/root/.openclaw/workspace/fund_data/temp_batch_{batch_num}.csv', 
                          index=False, encoding='utf-8-sig')
            
    except Exception as e:
        failed_funds.append({'code': code, 'name': name, 'reason': str(e)[:50]})
        continue

print()
print(f"处理完成: 成功 {len(fund_records)} 只, 失败 {len(failed_funds)} 只")
print()

if not fund_records:
    print("错误: 没有成功获取任何基金数据!")
    exit(1)

# 第三步：保存到主表
print("【第三步】保存主数据...")
df_main = pd.DataFrame(fund_records)
df_main.to_csv('/root/.openclaw/workspace/fund_data/fund_main.csv', index=False, encoding='utf-8-sig')
print(f"  已保存: fund_main.csv ({len(df_main)} 条记录)")

# 保存到SQLite数据库
db_path = '/root/.openclaw/workspace/fund_data/volatility_db/fund_database.db'
conn = sqlite3.connect(db_path)
df_main.to_sql('fund_basic', conn, if_exists='replace', index=False)
conn.close()
print(f"  已保存到SQLite: {db_path}")

# 第四步：按8个类别分别计算排名
print()
print("【第四步】按类别计算排名...")

ranking_records = []

for category in target_categories:
    cat_df = df_main[df_main['category'] == category].copy()
    if len(cat_df) == 0:
        continue
    
    print(f"  处理 {category}: {len(cat_df)} 只基金")
    
    # 按各周期收益排名
    for period in ['3m', '6m', '1y', '2y', '3y']:
        col = f'return_{period}'
        rank_col = f'rank_{period}'
        pct_col = f'percentile_{period}'
        
        # 只对有数据的基金排名
        valid_df = cat_df[cat_df[col].notna()].copy()
        if len(valid_df) == 0:
            continue
            
        valid_df[rank_col] = valid_df[col].rank(ascending=False, method='min')
        valid_df[pct_col] = (1 - (valid_df[rank_col] - 1) / len(valid_df)) * 100
        
        # 更新回原表
        for idx, row in valid_df.iterrows():
            mask = (df_main['ts_code'] == row['ts_code']) & (df_main['category'] == category)
            df_main.loc[mask, rank_col] = row[rank_col]
            df_main.loc[mask, pct_col] = round(row[pct_col], 2)

print(f"  排名计算完成")

# 第五步：质量评分
print()
print("【第五步】计算质量评分...")

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
    
    # 波动率 (20分) - 适中最好
    vol = row.get('volatility', 20) or 20
    if vol <= 15:
        score += 20
    elif vol <= 25:
        score += 20 - (vol - 15) * 0.5
    else:
        score += max(5, 15 - (vol - 25) * 0.2)
    
    # 月度胜率 (15分)
    win_rate = row.get('monthly_win_rate', 50) or 50
    score += min(15, win_rate / 100 * 15)
    
    # 盈亏比 (10分)
    pl_ratio = row.get('profit_loss_ratio', 1) or 1
    if pl_ratio >= 1.5:
        score += 10
    elif pl_ratio >= 0.5:
        score += (pl_ratio - 0.5) / 1 * 10
    else:
        score += 0
    
    return round(score, 1)

df_main['quality_score'] = df_main.apply(calc_quality_score, axis=1)

# 第六步：保存完整数据
print()
print("【第六步】保存完整数据...")

# CSV
df_main.to_csv('/root/.openclaw/workspace/fund_data/fund_complete.csv', index=False, encoding='utf-8-sig')

# SQLite
conn = sqlite3.connect(db_path)
df_main.to_sql('fund_complete', conn, if_exists='replace', index=False)

# 按类别分别保存
for category in target_categories:
    cat_df = df_main[df_main['category'] == category]
    if len(cat_df) > 0:
        cat_df.to_sql(f'category_{category.replace("-", "_")}', conn, if_exists='replace', index=False)

conn.close()

print(f"  已保存完整数据: fund_complete.csv ({len(df_main)} 条)")
print(f"  数据库位置: {db_path}")

# 第七步：生成摘要
print()
print("【第七步】生成摘要报告...")

summary = {
    'data_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'total_target': len(target_funds),
    'success_count': len(fund_records),
    'failed_count': len(failed_funds),
    'categories': {}
}

for category in target_categories:
    cat_df = df_main[df_main['category'] == category]
    if len(cat_df) == 0:
        continue
    
    summary['categories'][category] = {
        'count': len(cat_df),
        'avg_return_1y': round(cat_df['return_1y'].mean(), 2),
        'avg_volatility': round(cat_df['volatility'].mean(), 2),
        'avg_sharpe': round(cat_df['sharpe'].mean(), 2),
        'avg_quality_score': round(cat_df['quality_score'].mean(), 1),
        'top_1y': cat_df.nlargest(3, 'return_1y')[['ts_code', 'name', 'return_1y', 'sharpe']].to_dict('records')
    }

with open('/root/.openclaw/workspace/fund_data/summary_complete.json', 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print(f"  已保存: summary_complete.json")

# 第八步：输出关键发现
print()
print("="*70)
print("关键发现")
print("="*70)

for category in target_categories:
    cat_df = df_main[df_main['category'] == category]
    if len(cat_df) == 0:
        continue
    print(f"\n【{category}】({len(cat_df)}只)")
    print(f"  平均1年收益: {cat_df['return_1y'].mean():.1f}%")
    print(f"  平均波动率: {cat_df['volatility'].mean():.1f}%")
    print(f"  平均夏普: {cat_df['sharpe'].mean():.2f}")
    print(f"  平均质量分: {cat_df['quality_score'].mean():.1f}")
    top = cat_df.loc[cat_df['return_1y'].idxmax()]
    print(f"  最佳收益: {top['name']} ({top['return_1y']:.1f}%)")

print()
print("="*70)
print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)
