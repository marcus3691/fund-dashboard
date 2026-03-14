#!/usr/bin/env python3
"""
基金经理重点层监控脚本
标准：管理规模30-100亿，标准分析报告（简化版）
"""

import sys
import json
from datetime import datetime
from typing import Dict, List

sys.path.insert(0, '/root/.openclaw/workspace')
sys.path.insert(0, '/root/.openclaw/workspace/fund_data/monitor')

from key_manager_tiers import UNIQUE_KEY_MANAGERS
from database import manager_db

TUSHARE_TOKEN = '33996190080200cd63a01732ad443c390d9d580913ec938d4e1d704d'

def fetch_fund_basic(fund_code: str) -> Dict:
    """获取基金基础数据"""
    try:
        import tushare as ts
        ts.set_token(TUSHARE_TOKEN)
        pro = ts.pro_api()
        
        # 获取基金净值
        df = pro.fund_nav(ts_code=fund_code + '.OF')
        
        if df.empty:
            return None
        
        df = df.sort_values('ann_date')
        latest_nav = float(df.iloc[-1]['unit_nav'])
        latest_date = df.iloc[-1]['ann_date']
        
        # 计算收益
        returns = {}
        for days, label in [(30, '1月'), (90, '3月'), (180, '6月'), (365, '1年')]:
            if len(df) > days:
                old_nav = float(df.iloc[-days]['unit_nav'])
                returns[label] = round((latest_nav - old_nav) / old_nav * 100, 2)
        
        return {
            'latest_nav': latest_nav,
            'latest_date': latest_date,
            'returns': returns
        }
    except Exception as e:
        return None

def fetch_fund_holdings(fund_code: str) -> Dict:
    """获取基金持仓数据"""
    try:
        import tushare as ts
        ts.set_token(TUSHARE_TOKEN)
        pro = ts.pro_api()
        
        df = pro.fund_portfolio(ts_code=fund_code + '.OF')
        
        if df.empty:
            return None
        
        latest_quarter = df['end_date'].max()
        latest_holdings = df[df['end_date'] == latest_quarter].head(5)  # 只取前5
        
        holdings = []
        for _, row in latest_holdings.iterrows():
            holdings.append({
                'stock_code': row['symbol'],
                'ratio': round(float(row['stk_mkv_ratio']), 2) if 'stk_mkv_ratio' in row and row['stk_mkv_ratio'] else 0
            })
        
        return {
            'quarter': latest_quarter,
            'holdings': holdings
        }
    except Exception as e:
        return None

def generate_standard_report(manager: Dict) -> Dict:
    """生成标准分析报告（简化版）"""
    
    fund_code = manager.get('code')
    if not fund_code or fund_code == '私募':
        return None
    
    # 获取基础数据
    basic = fetch_fund_basic(fund_code)
    holdings = fetch_fund_holdings(fund_code)
    
    # 标准分析框架（简化版，不含九维度深度分析）
    report = {
        'manager': manager['name'],
        'fund': manager['fund'],
        'fund_code': fund_code,
        'company': manager['company'],
        'style': manager['style'],
        'aum': manager.get('aum', ''),
        'note': manager.get('note', ''),
        'tier': 'key',  # 重点层标识
        'report_type': 'standard',  # 标准报告
        'generated_at': datetime.now().isoformat(),
        
        # 基础数据
        'performance': basic,
        'holdings': holdings,
        
        # 标准分析（简化）
        'analysis': {
            'summary': '',  # 一句话总结
            'strengths': [],  # 优势
            'risks': [],  # 风险点
            'recommendation': ''  # 建议
        }
    }
    
    # 生成分析总结
    analysis = report['analysis']
    
    # 业绩分析
    if basic and basic.get('returns'):
        returns = basic['returns']
        yoy = returns.get('1年')
        
        if yoy is not None:
            if yoy > 30:
                analysis['summary'] = f"近1年表现优秀(+{yoy}%)，"
                analysis['strengths'].append('业绩领先同类')
            elif yoy > 10:
                analysis['summary'] = f"近1年表现良好(+{yoy}%)，"
                analysis['strengths'].append('业绩稳健')
            elif yoy > 0:
                analysis['summary'] = f"近1年小幅上涨(+{yoy}%)，"
            else:
                analysis['summary'] = f"近1年调整({yoy}%)，"
                analysis['risks'].append('近期业绩承压')
        
        # 趋势判断
        if '1月' in returns and '3月' in returns:
            mom = returns['1月']
            if mom > 5:
                analysis['strengths'].append('短期趋势向上')
            elif mom < -5:
                analysis['risks'].append('短期趋势向下')
    else:
        analysis['summary'] = '业绩数据待更新，'
    
    # 持仓分析
    if holdings and holdings.get('holdings'):
        top3 = holdings['holdings'][:3]
        top3_ratio = sum([h.get('ratio', 0) for h in top3])
        
        if top3_ratio > 25:
            analysis['summary'] += '持仓相对集中'
            analysis['risks'].append('持仓集中度较高')
        elif top3_ratio < 10:
            analysis['summary'] += '持仓较为分散'
            analysis['strengths'].append('风险分散')
        else:
            analysis['summary'] += '持仓均衡'
        
        # 重仓股信息
        top_stocks = ', '.join([h['stock_code'] for h in top3])
        analysis['top_holdings'] = top_stocks
    else:
        analysis['summary'] += '持仓数据待更新'
    
    # 建议
    if len(analysis['strengths']) > len(analysis['risks']):
        analysis['recommendation'] = '可重点关注'
    elif len(analysis['risks']) > len(analysis['strengths']):
        analysis['recommendation'] = '建议观望'
    else:
        analysis['recommendation'] = '保持关注'
    
    return report

def run_key_manager_monitor(limit: int = None):
    """运行重点层基金经理监控"""
    
    managers = UNIQUE_KEY_MANAGERS[:limit] if limit else UNIQUE_KEY_MANAGERS[:50]  # 先测试50人
    
    print("="*70)
    print("基金经理重点层监控 - 标准分析报告")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"监控人数: {len(managers)}/{len(UNIQUE_KEY_MANAGERS)}")
    print("="*70)
    print()
    
    success_count = 0
    fail_count = 0
    
    for i, manager in enumerate(managers, 1):
        print(f"[{i}/{len(managers)}] {manager['name']} ({manager['company']}) - {manager['style']}")
        
        report = generate_standard_report(manager)
        
        if report:
            # 保存到数据库
            manager_db.insert({
                'manager': manager['name'],
                'fund': manager['fund'],
                'report': report,
                'tier': 'key',
                'generated_at': datetime.now().isoformat()
            })
            
            analysis = report['analysis']
            print(f"    ✅ 成功 | {analysis.get('summary', '')}")
            print(f"       建议: {analysis.get('recommendation', '')}")
            success_count += 1
        else:
            print(f"    ❌ 失败: 无法生成报告")
            fail_count += 1
    
    print()
    print("="*70)
    print("监控完成")
    print(f"  成功: {success_count} 人")
    print(f"  失败: {fail_count} 人")
    print(f"  成功率: {success_count/len(managers)*100:.1f}%")
    print("="*70)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=50, help='限制分析人数')
    
    args = parser.parse_args()
    
    run_key_manager_monitor(limit=args.limit)
