#!/usr/bin/env python3
"""
基金经理核心层监控 - 备用方案
基于Tushare数据生成基金分析报告
"""

import sys
import json
from datetime import datetime
from typing import Dict, List

sys.path.insert(0, '/root/.openclaw/workspace')
sys.path.insert(0, '/root/.openclaw/workspace/fund_data/monitor')

from manager_tiers import CORE_MANAGERS
from database import manager_db

# Tushare Token
TUSHARE_TOKEN = '33996190080200cd63a01732ad443c390d9d580913ec938d4e1d704d'

def fetch_fund_performance(fund_code: str) -> Dict:
    """获取基金业绩数据"""
    try:
        import tushare as ts
        ts.set_token(TUSHARE_TOKEN)
        pro = ts.pro_api()
        
        # 获取基金净值
        df = pro.fund_nav(ts_code=fund_code + '.OF')
        
        if df.empty:
            return None
        
        # 计算收益
        df = df.sort_values('ann_date')
        latest_nav = float(df.iloc[-1]['nav'])
        latest_date = df.iloc[-1]['ann_date']
        
        # 计算区间收益
        returns = {}
        for days, label in [(30, '1月'), (90, '3月'), (180, '6月'), (365, '1年')]:
            if len(df) > days:
                old_nav = float(df.iloc[-days]['nav'])
                returns[label] = round((latest_nav - old_nav) / old_nav * 100, 2)
        
        return {
            'fund_code': fund_code,
            'latest_nav': latest_nav,
            'latest_date': latest_date,
            'returns': returns
        }
        
    except Exception as e:
        print(f"  ⚠️ 获取业绩数据失败: {e}")
        return None

def fetch_fund_holdings(fund_code: str) -> Dict:
    """获取基金持仓数据"""
    try:
        import tushare as ts
        ts.set_token(TUSHARE_TOKEN)
        pro = ts.pro_api()
        
        # 获取最新季度持仓
        df = pro.fund_portfolio(ts_code=fund_code + '.OF')
        
        if df.empty:
            return None
        
        # 获取最新季度
        latest_quarter = df['end_date'].max()
        latest_holdings = df[df['end_date'] == latest_quarter].head(10)
        
        holdings = []
        for _, row in latest_holdings.iterrows():
            holdings.append({
                'stock_code': row['symbol'],
                'stock_name': row.get('name', ''),
                'ratio': round(float(row['stk_mkv_ratio']), 2) if 'stk_mkv_ratio' in row and row['stk_mkv_ratio'] else 0,
                'mkv': round(float(row['mkv']) / 1e8, 2) if 'mkv' in row else 0  # 市值（亿元）
            })
        
        return {
            'quarter': latest_quarter,
            'holdings': holdings
        }
        
    except Exception as e:
        print(f"  获取持仓数据失败: {e}")
        return None

def generate_manager_report(manager: Dict) -> Dict:
    """生成基金经理分析报告"""
    
    fund_code = manager.get('code')
    if not fund_code or fund_code == '私募':
        return None
    
    print(f"\n  分析 {manager['name']} ({manager['fund']})...")
    
    # 获取业绩数据
    performance = fetch_fund_performance(fund_code)
    
    # 获取持仓数据
    holdings = fetch_fund_holdings(fund_code)
    
    # 构建报告
    report = {
        'manager': manager['name'],
        'fund': manager['fund'],
        'fund_code': fund_code,
        'company': manager['company'],
        'style': manager['style'],
        'aum': manager.get('aum', ''),
        'tenure': manager.get('tenure', ''),
        'generated_at': datetime.now().isoformat(),
        'performance': performance,
        'holdings': holdings,
        'key_insights': []
    }
    
    # 生成关键洞察
    insights = []
    
    if performance and performance.get('returns'):
        returns = performance['returns']
        # 近1年收益判断
        if '1年' in returns:
            yoy_return = returns['1年']
            if yoy_return > 30:
                insights.append(f"近1年收益优秀: +{yoy_return}% 🌟")
            elif yoy_return > 10:
                insights.append(f"近1年收益良好: +{yoy_return}%")
            elif yoy_return > 0:
                insights.append(f"近1年收益: +{yoy_return}%")
            elif yoy_return > -10:
                insights.append(f"近1年收益: {yoy_return}%（小幅调整）")
            else:
                insights.append(f"近1年收益: {yoy_return}% ⚠️ 需关注")
        
        # 短期趋势判断
        if '1月' in returns and '3月' in returns:
            mom = returns['1月']
            qoq = returns['3月']
            if mom > 10 and qoq > 20:
                insights.append("短期趋势强劲，momentum优秀 🚀")
            elif mom > 5 and qoq > 10:
                insights.append("短期趋势向上，表现良好 📈")
            elif mom < -10 and qoq < -20:
                insights.append("短期承压，关注回撤控制 📉")
            elif mom < -5 and qoq < -10:
                insights.append("近期调整，需谨慎观察 ⚠️")
        
        # 波动性判断
        if '1月' in returns and '3月' in returns:
            if abs(returns['1月']) > 15:
                insights.append("近1月波动较大，注意风险控制")
    else:
        insights.append("暂无业绩数据")
    
    if holdings and holdings.get('holdings'):
        top3 = holdings['holdings'][:3]
        holdings_desc = ', '.join([f"{h.get('stock_code', '')}({h.get('ratio', 0)}%)" for h in top3])
        insights.append(f"前3大重仓: {holdings_desc}")
        
        # 集中度判断
        top3_ratio = sum([h.get('ratio', 0) for h in top3])
        if top3_ratio > 30:
            insights.append(f"持仓集中度较高(前3大{top3_ratio:.1f}%)，风格鲜明 🎯")
        elif top3_ratio < 15:
            insights.append(f"持仓分散(前3大{top3_ratio:.1f}%)，风险分散 🛡️")
    else:
        insights.append("暂无持仓数据")
    
    report['key_insights'] = insights
    
    # 保存到数据库
    manager_db.insert({
        'manager': manager['name'],
        'fund': manager['fund'],
        'report': report,
        'generated_at': datetime.now().isoformat()
    })
    
    return report

def run_core_manager_analysis(limit: int = None):
    """运行核心层基金经理分析"""
    
    managers = CORE_MANAGERS[:limit] if limit else CORE_MANAGERS[:10]
    
    print("="*70)
    print("基金经理核心层分析 - 基于Tushare数据")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"分析人数: {len(managers)}/{len(CORE_MANAGERS)}")
    print("="*70)
    
    success_count = 0
    fail_count = 0
    
    reports = []
    
    for i, manager in enumerate(managers, 1):
        print(f"\n[{i}/{len(managers)}] {manager['name']} ({manager['company']}) - {manager['style']}")
        
        report = generate_manager_report(manager)
        
        if report:
            print(f"  ✅ 成功生成报告")
            print(f"     关键洞察: {', '.join(report['key_insights'][:2])}")
            reports.append(report)
            success_count += 1
        else:
            print(f"  ❌ 无法生成报告（代码缺失或私募）")
            fail_count += 1
    
    # 生成汇总
    print("\n" + "="*70)
    print("分析汇总")
    print("="*70)
    print(f"成功: {success_count} 人")
    print(f"失败: {fail_count} 人")
    print()
    
    # 业绩排序
    if reports:
        print("近1年收益排名（前5）:")
        sorted_by_return = sorted(
            [r for r in reports if r.get('performance') and r['performance'].get('returns') and '1年' in r['performance']['returns']],
            key=lambda x: x['performance']['returns'].get('1年', 0),
            reverse=True
        )[:5]
        
        for i, r in enumerate(sorted_by_return, 1):
            ret = r['performance']['returns']['1年']
            print(f"{i}. {r['manager']} ({r['fund']}) - {ret:+.2f}%")
    
    return reports

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=10, help='限制分析人数')
    
    args = parser.parse_args()
    
    run_core_manager_analysis(limit=args.limit)
