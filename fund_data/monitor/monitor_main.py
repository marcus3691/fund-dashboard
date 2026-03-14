#!/usr/bin/env python3
"""
智能舆情监控系统 - 主控脚本
集成新闻抓取、基金经理监控、研报抓取
"""

import sys
import json
from datetime import datetime
from typing import List, Dict

sys.path.insert(0, '/root/.openclaw/workspace')
sys.path.insert(0, '/root/.openclaw/workspace/fund_data/monitor')

from database import news_db, manager_db, report_db
from news_monitor import run_news_monitor
from daily_report import generate_and_send_report

# 监控的基金经理名单 - 分层监控体系
# 核心层：从manager_tiers导入50位核心基金经理
from manager_tiers import CORE_MANAGERS

MONITOR_MANAGERS = CORE_MANAGERS  # 50位核心层基金经理

def update_etf_signals():
    """将生成的信号更新到ETF信号系统"""
    
    # 读取现有信号
    signals_file = '/root/.openclaw/workspace/fund_data/analysis/etf_signals.json'
    
    try:
        with open(signals_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except:
        data = {'active_signals': [], 'pending_signals': []}
    
    # 获取未处理的新闻信号
    unprocessed_news = news_db.find_unprocessed()
    
    new_signals = []
    for news in unprocessed_news:
        signals = news.get('extracted_signals', [])
        for signal in signals:
            # 转换为ETF信号格式
            etf_signal = {
                'id': f"AUTO_{datetime.now().strftime('%Y%m%d')}_{len(new_signals)+1:03d}",
                'timestamp': datetime.now().isoformat(),
                'type': signal.get('type', 'macro'),
                'priority': signal.get('priority', 'medium'),
                'status': 'pending_review',
                'trigger': {
                    'event': signal.get('trigger', ''),
                    'source': news.get('source', '舆情监控'),
                    'current_value': news.get('title', '')
                },
                'action': {
                    'layer': 'satellite',
                    'target': signal.get('action', '').replace('关注', '').strip(),
                    'direction': '关注',
                    'suggested_weight': 3,
                    'rationale': f"【舆情监控生成】{news.get('title', '')}"
                },
                'review_status': 'pending',
                'reviewer': None,
                'review_notes': f"来源: {news.get('url', '')} | 情感: {news.get('sentiment', 'neutral')}"
            }
            new_signals.append(etf_signal)
    
    # 添加到pending_signals
    if 'pending_signals' not in data:
        data['pending_signals'] = []
    
    data['pending_signals'].extend(new_signals)
    
    # 保存
    with open(signals_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 已将 {len(new_signals)} 个信号录入ETF系统")
    
    return new_signals

def run_manager_monitor():
    """运行基金经理观点监控 - 分层体系"""
    print(f"\n{'='*60}")
    print(f"基金经理观点监控 - 分层监控体系")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"{'='*60}\n")
    
    # 导入核心层监控模块
    from core_manager_monitor import run_core_manager_monitor
    
    print(f"【核心层】监控{len(CORE_MANAGERS)}位顶级基金经理")
    print(f"标准: 管理规模>100亿 + 业绩持续优秀")
    print(f"报告深度: 九维度完整分析")
    print()
    
    # 运行核心层监控（实际抓取）
    success, fail = run_core_manager_monitor(limit=10)  # 先测试10人
    
    print(f"\n【重点层】待扩展至200人")
    print(f"标准: 管理规模30-100亿 + 某领域专长")
    print(f"状态: 框架已就绪，待数据补充")
    print()
    
    print(f"【基础层】全市场异常监控")
    print(f"范围: 所有公募基金约3000位基金经理")
    print(f"触发: 业绩突变/规模异动/调仓异常")
    print(f"状态: 待开发")
    
    return success, fail

def run_report_monitor():
    """运行研报监控"""
    print(f"\n{'='*60}")
    print(f"市场研报监控 - {datetime.now().strftime('%Y-%m-%d')}")
    print(f"{'='*60}\n")
    
    # TODO: 实现研报抓取
    print("⚠️ 研报监控开发中...")
    
    return []

def run_daily_monitor():
    """运行每日监控（新闻+观点+研报）"""
    print(f"\n{'='*70}")
    print(f"🤖 智能舆情监控系统 - 每日扫描")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")
    
    # 1. 新闻监控
    print("【阶段1】新闻舆情监控")
    news_summary = run_news_monitor()
    
    # 2. 基金经理观点监控
    print("\n【阶段2】基金经理观点监控")
    manager_views = run_manager_monitor()
    
    # 3. 研报监控
    print("\n【阶段3】市场研报监控")
    reports = run_report_monitor()
    
    # 4. 更新ETF信号系统
    print("\n【阶段4】更新ETF信号系统")
    new_signals = update_etf_signals()
    
    # 5. 发送每日汇总邮件
    print("\n【阶段5】发送每日汇总邮件")
    generate_and_send_report()
    
    print(f"\n{'='*70}")
    print(f"✅ 每日监控完成！")
    print(f"  - 新闻: {news_summary.get('total_count', 0)} 条")
    print(f"  - 信号: {len(new_signals)} 个")
    print(f"{'='*70}\n")

def run_quick_test():
    """快速测试"""
    print("运行快速测试...")
    
    # 测试数据库
    test_news = {
        'title': '测试新闻：黄金价格上涨',
        'content': '今日黄金价格突破5200美元，市场情绪乐观',
        'source': '测试',
        'url': 'https://test.com',
        'keywords': ['黄金', '上涨'],
        'sentiment': 'positive'
    }
    
    news_id = news_db.insert(test_news)
    print(f"✅ 测试新闻已插入: {news_id}")
    
    # 测试信号生成
    signals = [{
        'type': 'commodity',
        'priority': 'medium',
        'trigger': '黄金价格上涨',
        'action': '关注黄金ETF'
    }]
    
    news_db.mark_processed(news_id, signals)
    print(f"✅ 测试信号已生成")
    
    # 测试汇总
    summary = news_db.get_daily_summary()
    print(f"✅ 测试汇总: {summary}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='智能舆情监控系统')
    parser.add_argument('--mode', choices=['daily', 'test', 'news'], default='daily',
                       help='运行模式: daily(每日监控), test(测试), news(仅新闻)')
    
    args = parser.parse_args()
    
    if args.mode == 'daily':
        run_daily_monitor()
    elif args.mode == 'test':
        run_quick_test()
    elif args.mode == 'news':
        run_news_monitor()
