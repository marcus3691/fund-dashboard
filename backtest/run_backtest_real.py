#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETF投资组合回测分析 - 2026年Q1 (真实数据)
使用Tushare Pro获取真实行情
"""

import os
import sys
import pandas as pd
import numpy as np
import tushare as ts
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'WenQuanYi Micro Hei']
plt.rcParams['axes.unicode_minus'] = False

# ========== 配置参数 ==========
START_DATE = '20260101'
END_DATE = '20260320'
MONEY_FUND_RATE = 0.02  # 货币基金年化收益率2%
RISK_FREE_RATE = 0.02   # 无风险利率2%
TRADING_DAYS = 252      # 年交易日

# ETF配置
ETF_CONFIG = [
    {'name': '黄金ETF', 'code': '518880.SH', 'weight': 0.15},
    {'name': '黄金股ETF', 'code': '159562.SZ', 'weight': 0.10},
    {'name': '军工龙头ETF', 'code': '512710.SH', 'weight': 0.08},
    {'name': '通信设备ETF', 'code': '515880.SH', 'weight': 0.12},
    {'name': '半导体ETF', 'code': '512480.SH', 'weight': 0.05},
    {'name': '人工智能ETF', 'code': '159819.SZ', 'weight': 0.03},
    {'name': '电网设备ETF', 'code': '159326.SZ', 'weight': 0.10},
    {'name': '电力ETF', 'code': '159611.SZ', 'weight': 0.05},
    {'name': '恒生科技ETF', 'code': '513130.SH', 'weight': 0.05},
    {'name': '港股创新药ETF', 'code': '513120.SH', 'weight': 0.02},
    {'name': '货币基金', 'code': 'CASH', 'weight': 0.25},
]

# 基准配置
BENCHMARKS = [
    {'name': '沪深300', 'code': '000300.SH'},
    {'name': '中证800', 'code': '000906.SH'},
]

# 初始化Tushare
TOKEN = '33996190080200cd63a01732ad443c390d9d580913ec938d4e1d704d'
ts.set_token(TOKEN)
pro = ts.pro_api(TOKEN)

# ========== 数据获取函数 ==========

def get_etf_data(ts_code, start_date, end_date):
    """获取ETF日线数据"""
    try:
        df = pro.fund_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        if df is not None and len(df) > 0:
            df = df.sort_values('trade_date').reset_index(drop=True)
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            return df[['trade_date', 'close']].copy()
    except Exception as e:
        print(f"  获取{ts_code}失败: {e}")
    return None

def get_index_data(ts_code, start_date, end_date):
    """获取指数日线数据"""
    try:
        df = pro.index_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        if df is not None and len(df) > 0:
            df = df.sort_values('trade_date').reset_index(drop=True)
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            return df[['trade_date', 'close']].copy()
    except Exception as e:
        print(f"  获取{ts_code}失败: {e}")
    return None

def calculate_metrics(df):
    """计算收益率和风险指标"""
    df = df.copy()
    df['daily_return'] = df['close'].pct_change()
    df['nav'] = (1 + df['daily_return'].fillna(0)).cumprod()
    return df

def calculate_annualized_volatility(returns):
    """计算年化波动率"""
    return returns.std() * np.sqrt(TRADING_DAYS)

def calculate_max_drawdown(nav_series):
    """计算最大回撤"""
    rolling_max = nav_series.cummax()
    drawdown = (nav_series - rolling_max) / rolling_max
    return drawdown.min()

def calculate_sharpe_ratio(returns, risk_free_rate=RISK_FREE_RATE):
    """计算夏普比率"""
    excess_returns = returns.mean() * TRADING_DAYS - risk_free_rate
    volatility = returns.std() * np.sqrt(TRADING_DAYS)
    if volatility == 0:
        return 0
    return excess_returns / volatility

def calculate_calmar_ratio(returns, max_dd, trading_days_used=None):
    """计算卡玛比率"""
    if trading_days_used is None:
        annual_return = returns.mean() * TRADING_DAYS
    else:
        # 根据实际交易天数计算年化收益
        total_return = (1 + returns).prod() - 1
        annual_return = (1 + total_return) ** (TRADING_DAYS / trading_days_used) - 1
    
    if max_dd == 0:
        return 0
    return annual_return / abs(max_dd)

# ========== 主程序 ==========

def main():
    print("=" * 60)
    print("ETF投资组合回测分析 - 2026年Q1 (真实数据)")
    print(f"回测区间: {START_DATE} ~ {END_DATE}")
    print("=" * 60)
    
    # 1. 获取ETF数据
    print("\n【1/4】获取ETF数据...")
    etf_data = {}
    
    for cfg in ETF_CONFIG:
        code = cfg['code']
        name = cfg['name']
        
        if code == 'CASH':
            # 货币基金特殊处理
            continue
            
        print(f"  获取 {name} ({code})...", end=' ')
        df = get_etf_data(code, START_DATE, END_DATE)
        if df is not None:
            etf_data[code] = calculate_metrics(df)
            print(f"✓ {len(df)}条记录")
        else:
            print(f"✗ 失败")
    
    # 2. 获取基准数据
    print("\n【2/4】获取基准数据...")
    benchmark_data = {}
    for cfg in BENCHMARKS:
        print(f"  获取 {cfg['name']} ({cfg['code']})...", end=' ')
        df = get_index_data(cfg['code'], START_DATE, END_DATE)
        if df is not None:
            benchmark_data[cfg['code']] = calculate_metrics(df)
            print(f"✓ {len(df)}条记录")
        else:
            print(f"✗ 失败")
    
    # 3. 构建组合
    print("\n【3/4】计算组合表现...")
    
    # 获取统一的交易日历
    trading_dates = None
    for code, df in etf_data.items():
        if trading_dates is None:
            trading_dates = set(df['trade_date'])
        else:
            trading_dates = trading_dates & set(df['trade_date'])
    
    trading_dates = sorted(list(trading_dates))
    trading_days_used = len(trading_dates)
    print(f"  统一交易日: {trading_days_used}天")
    
    # 初始化组合净值
    portfolio_nav = pd.DataFrame({'trade_date': trading_dates})
    portfolio_nav['nav'] = 1.0
    portfolio_nav['daily_return'] = 0.0
    
    # 计算每日组合收益率
    for i in range(1, len(portfolio_nav)):
        date = portfolio_nav.loc[i, 'trade_date']
        prev_date = portfolio_nav.loc[i-1, 'trade_date']
        
        daily_return = 0
        for cfg in ETF_CONFIG:
            code = cfg['code']
            weight = cfg['weight']
            
            if code == 'CASH':
                # 货币基金日收益
                daily_return += weight * (MONEY_FUND_RATE / TRADING_DAYS)
            else:
                # ETF日收益
                if code in etf_data:
                    df = etf_data[code]
                    day_data = df[df['trade_date'] == date]
                    if len(day_data) > 0:
                        etf_return = day_data['daily_return'].values[0]
                        if not np.isnan(etf_return):
                            daily_return += weight * etf_return
        
        portfolio_nav.loc[i, 'daily_return'] = daily_return
        portfolio_nav.loc[i, 'nav'] = portfolio_nav.loc[i-1, 'nav'] * (1 + daily_return)
    
    # 计算组合指标
    portfolio_returns = portfolio_nav['daily_return'].dropna()
    portfolio_total_return = portfolio_nav['nav'].iloc[-1] - 1
    portfolio_vol = calculate_annualized_volatility(portfolio_returns)
    portfolio_dd = calculate_max_drawdown(portfolio_nav['nav'])
    portfolio_sharpe = calculate_sharpe_ratio(portfolio_returns)
    portfolio_calmar = calculate_calmar_ratio(portfolio_returns, portfolio_dd, trading_days_used)
    
    # 4. 计算各ETF指标
    print("\n【4/4】计算ETF和基准指标...")
    
    results = []
    
    # 组合结果
    results.append({
        '名称': '组合',
        '代码': 'PORTFOLIO',
        '权重': '100%',
        '区间收益': f"{portfolio_total_return*100:.2f}%",
        '年化波动': f"{portfolio_vol*100:.2f}%",
        '最大回撤': f"{portfolio_dd*100:.2f}%",
        '夏普比率': f"{portfolio_sharpe:.2f}",
        '卡玛比率': f"{portfolio_calmar:.2f}",
    })
    
    # ETF结果
    for cfg in ETF_CONFIG:
        code = cfg['code']
        name = cfg['name']
        weight = cfg['weight']
        
        if code == 'CASH':
            # 货币基金
            cash_return = MONEY_FUND_RATE * trading_days_used / TRADING_DAYS
            results.append({
                '名称': name,
                '代码': code,
                '权重': f"{weight*100:.0f}%",
                '区间收益': f"{cash_return*100:.2f}%",
                '年化波动': '0.00%',
                '最大回撤': '0.00%',
                '夏普比率': '-',
                '卡玛比率': '-',
            })
        elif code in etf_data:
            df = etf_data[code]
            returns = df['daily_return'].dropna()
            total_return = df['nav'].iloc[-1] - 1
            vol = calculate_annualized_volatility(returns)
            dd = calculate_max_drawdown(df['nav'])
            sharpe = calculate_sharpe_ratio(returns)
            calmar = calculate_calmar_ratio(returns, dd, trading_days_used)
            
            results.append({
                '名称': name,
                '代码': code,
                '权重': f"{weight*100:.0f}%",
                '区间收益': f"{total_return*100:.2f}%",
                '年化波动': f"{vol*100:.2f}%",
                '最大回撤': f"{dd*100:.2f}%",
                '夏普比率': f"{sharpe:.2f}",
                '卡玛比率': f"{calmar:.2f}",
            })
    
    # 基准结果
    for cfg in BENCHMARKS:
        code = cfg['code']
        name = cfg['name']
        
        if code in benchmark_data:
            df = benchmark_data[code]
            returns = df['daily_return'].dropna()
            total_return = df['nav'].iloc[-1] - 1
            vol = calculate_annualized_volatility(returns)
            dd = calculate_max_drawdown(df['nav'])
            sharpe = calculate_sharpe_ratio(returns)
            calmar = calculate_calmar_ratio(returns, dd, trading_days_used)
            
            results.append({
                '名称': name,
                '代码': code,
                '权重': '基准',
                '区间收益': f"{total_return*100:.2f}%",
                '年化波动': f"{vol*100:.2f}%",
                '最大回撤': f"{dd*100:.2f}%",
                '夏普比率': f"{sharpe:.2f}",
                '卡玛比率': f"{calmar:.2f}",
            })
    
    # 输出结果
    results_df = pd.DataFrame(results)
    print("\n" + "=" * 80)
    print("回测结果汇总")
    print("=" * 80)
    print(results_df.to_string(index=False))
    
    # 计算收益贡献
    print("\n" + "=" * 80)
    print("各ETF收益贡献分析")
    print("=" * 80)
    
    contributions = []
    for cfg in ETF_CONFIG:
        code = cfg['code']
        name = cfg['name']
        weight = cfg['weight']
        
        if code == 'CASH':
            cash_return = MONEY_FUND_RATE * trading_days_used / TRADING_DAYS
            contribution = weight * cash_return
            total_return_pct = cash_return
        elif code in etf_data:
            df = etf_data[code]
            total_return_pct = df['nav'].iloc[-1] - 1
            contribution = weight * total_return_pct
        else:
            continue
        
        contributions.append({
            'ETF': name,
            '权重': f"{weight*100:.0f}%",
            '区间收益': f"{total_return_pct*100:.2f}%",
            '收益贡献': contribution * 100,
        })
    
    contrib_df = pd.DataFrame(contributions)
    contrib_df = contrib_df.sort_values('收益贡献', ascending=False)
    print(contrib_df.to_string(index=False))
    
    total_contribution = contrib_df['收益贡献'].sum()
    print(f"\n组合总收益: {portfolio_total_return*100:.2f}%")
    print(f"加总贡献: {total_contribution:.2f}%")
    
    # 保存CSV
    csv_path = '/root/.openclaw/workspace/backtest/portfolio_backtest_real_2026q1.csv'
    results_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"\n✓ 结果已保存: {csv_path}")
    
    # 生成净值曲线图
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # 净值曲线
    ax1.plot(portfolio_nav['trade_date'], portfolio_nav['nav'], label='组合', linewidth=2, color='blue')
    
    for cfg in BENCHMARKS:
        code = cfg['code']
        name = cfg['name']
        if code in benchmark_data:
            df = benchmark_data[code]
            ax1.plot(df['trade_date'], df['nav'], label=name, linewidth=1.5, alpha=0.7)
    
    ax1.set_title('Portfolio NAV vs Benchmarks (2026 Q1)', fontsize=14)
    ax1.set_xlabel('Date')
    ax1.set_ylabel('NAV')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 回撤曲线
    rolling_max = portfolio_nav['nav'].cummax()
    drawdown = (portfolio_nav['nav'] - rolling_max) / rolling_max * 100
    ax2.fill_between(portfolio_nav['trade_date'], drawdown, 0, color='red', alpha=0.3)
    ax2.plot(portfolio_nav['trade_date'], drawdown, color='red', linewidth=1)
    ax2.set_title('Portfolio Drawdown (%)', fontsize=14)
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Drawdown (%)')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    chart_path = '/root/.openclaw/workspace/backtest/nav_curve_real_2026q1.png'
    plt.savefig(chart_path, dpi=150, bbox_inches='tight')
    print(f"✓ 图表已保存: {chart_path}")
    
    # 生成Markdown报告
    report = f"""# ETF投资组合回测报告 - 2026年Q1 (真实数据)

## 回测概览

| 项目 | 值 |
|:---|:---|
| 回测区间 | 2026-01-05 ~ 2026-03-20 |
| 交易日数 | {trading_days_used}天 |
| 无风险利率 | {RISK_FREE_RATE*100}% |
| 货币基金收益 | {MONEY_FUND_RATE*100}% |

## 组合表现

| 指标 | 数值 |
|:---|:---|
| 区间收益率 | {portfolio_total_return*100:.2f}% |
| 年化波动率 | {portfolio_vol*100:.2f}% |
| 最大回撤 | {portfolio_dd*100:.2f}% |
| 夏普比率 | {portfolio_sharpe:.2f} |
| 卡玛比率 | {portfolio_calmar:.2f} |

## 详细结果

{results_df.to_markdown(index=False)}

## 收益贡献分析

{contrib_df.to_markdown(index=False)}

## 说明

- 数据来源: Tushare Pro (真实行情)
- 货币基金按年化{MONEY_FUND_RATE*100}%计算日收益
- 组合每日收益率 = Σ(ETF日收益率 × 权重)
- 净值曲线图: nav_curve_real_2026q1.png

---
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    report_path = '/root/.openclaw/workspace/backtest/portfolio_backtest_report_real_2026q1.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"✓ 报告已保存: {report_path}")
    
    print("\n" + "=" * 60)
    print("回测完成!")
    print("=" * 60)

if __name__ == '__main__':
    main()
