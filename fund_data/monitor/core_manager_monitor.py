#!/usr/bin/env python3
"""
基金经理核心层监控脚本
监控50位核心基金经理，生成九维度分析报告
"""

import sys
import json
import re
from datetime import datetime
from typing import List, Dict

sys.path.insert(0, '/root/.openclaw/workspace')
sys.path.insert(0, '/root/.openclaw/workspace/fund_data/monitor')

from manager_tiers import CORE_MANAGERS, DATA_SOURCES
from database import manager_db

# 导入抓取工具
try:
    sys.path.insert(0, '/root/.openclaw/workspace/skills/web-scraper')
    from web_scraper import scrape_web
except:
    import requests
    from bs4 import BeautifulSoup
    
    def scrape_web(url, mode='auto', selector=None):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            result = {
                'success': True,
                'url': url,
                'title': soup.title.string if soup.title else '',
                'content': soup.get_text()[:5000],
                'fetcher_used': 'requests'
            }
            if selector:
                elem = soup.select_one(selector)
                result['selected_content'] = elem.get_text().strip() if elem else ''
            return result
        except Exception as e:
            return {'success': False, 'url': url, 'error': str(e)}

def fetch_quarterly_report(manager: Dict) -> Dict:
    """
    抓取基金经理季报中的"投资策略和运作分析"部分
    """
    code = manager.get('code')
    if not code or code == '私募':
        return {'success': False, 'error': '无法获取代码'}
    
    # 天天基金网基金详情页
    url = f"https://fund.eastmoney.com/{code}.html"
    
    try:
        result = scrape_web(url, selector='.detail .box')
        
        if result.get('success'):
            content = result.get('selected_content', '') or result.get('content', '')
            
            # 提取关键信息
            view_data = {
                'manager': manager['name'],
                'fund': manager['fund'],
                'fund_code': code,
                'company': manager['company'],
                'style': manager['style'],
                'source': '基金季报',
                'url': url,
                'content': content[:3000],  # 限制长度
                'extracted_at': datetime.now().isoformat()
            }
            
            # 提取关键观点（简单规则匹配）
            key_points = []
            
            # 市场展望
            if '看好' in content or '乐观' in content:
                key_points.append('市场展望：看好')
            elif '谨慎' in content or '悲观' in content:
                key_points.append('市场展望：谨慎')
            
            # 调仓方向
            if '加仓' in content or '增持' in content:
                key_points.append('调仓方向：加仓')
            elif '减仓' in content or '减持' in content:
                key_points.append('调仓方向：减仓')
            
            # 看好板块
            sectors = ['消费', '医药', '科技', '新能源', '半导体', '金融', '地产', '周期']
            for sector in sectors:
                if sector in content:
                    key_points.append(f'看好板块：{sector}')
                    break
            
            view_data['key_points'] = key_points
            view_data['sentiment'] = 'positive' if '看好' in content else ('negative' if '谨慎' in content else 'neutral')
            
            return {'success': True, 'data': view_data}
        else:
            return {'success': False, 'error': result.get('error')}
            
    except Exception as e:
        return {'success': False, 'error': str(e)}

def generate_manager_consensus():
    """
    生成基金经理共识分析
    """
    print("\n" + "="*70)
    print("基金经理共识分析")
    print("="*70 + "\n")
    
    # 获取本月所有观点
    current_month = datetime.now().strftime('%Y-%m')
    recent_views = [v for v in manager_db.data 
                   if v.get('created_at', '').startswith(current_month)]
    
    if not recent_views:
        print("本月暂无观点数据")
        return
    
    # 统计共识
    sentiment_dist = {'positive': 0, 'negative': 0, 'neutral': 0}
    sector_mentions = {}
    
    for view in recent_views:
        # 情感统计
        sentiment = view.get('sentiment', 'neutral')
        sentiment_dist[sentiment] = sentiment_dist.get(sentiment, 0) + 1
        
        # 板块提及
        for point in view.get('key_points', []):
            if '看好板块' in point:
                sector = point.replace('看好板块：', '')
                sector_mentions[sector] = sector_mentions.get(sector, 0) + 1
    
    print(f"本月监控基金经理: {len(recent_views)} 位")
    print(f"\n市场情绪分布:")
    print(f"  - 看多: {sentiment_dist['positive']} 人 ({sentiment_dist['positive']/len(recent_views)*100:.1f}%)")
    print(f"  - 看空: {sentiment_dist['negative']} 人 ({sentiment_dist['negative']/len(recent_views)*100:.1f}%)")
    print(f"  - 中性: {sentiment_dist['neutral']} 人 ({sentiment_dist['neutral']/len(recent_views)*100:.1f}%)")
    
    print(f"\n热门板块（基金经理提及次数）:")
    for sector, count in sorted(sector_mentions.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  - {sector}: {count} 次")
    
    # 生成共识信号
    if sentiment_dist['positive'] > sentiment_dist['negative'] * 2:
        signal = {
            'type': 'manager_consensus',
            'priority': 'high',
            'trigger': '基金经理普遍看多',
            'action': '关注权益类ETF',
            'consensus': 'positive'
        }
        print(f"\n⚠️ 生成信号: 基金经理共识看多")
    elif sentiment_dist['negative'] > sentiment_dist['positive'] * 2:
        signal = {
            'type': 'manager_consensus',
            'priority': 'high',
            'trigger': '基金经理普遍看空',
            'action': '降低权益仓位',
            'consensus': 'negative'
        }
        print(f"\n⚠️ 生成信号: 基金经理共识看空")

def run_core_manager_monitor(limit: int = None):
    """
    运行核心层基金经理监控
    
    Args:
        limit: 限制监控人数（用于测试）
    """
    managers = CORE_MANAGERS[:limit] if limit else CORE_MANAGERS
    
    print("\n" + "="*70)
    print(f"核心层基金经理监控 - {datetime.now().strftime('%Y-%m-%d')}")
    print(f"监控人数: {len(managers)}/{len(CORE_MANAGERS)}")
    print("="*70 + "\n")
    
    success_count = 0
    fail_count = 0
    
    for i, manager in enumerate(managers, 1):
        print(f"[{i}/{len(managers)}] 抓取 {manager['name']} ({manager['fund']})...")
        
        result = fetch_quarterly_report(manager)
        
        if result.get('success'):
            view_data = result['data']
            manager_db.insert(view_data)
            
            key_points = view_data.get('key_points', [])
            sentiment = view_data.get('sentiment', 'neutral')
            
            print(f"    ✅ 成功 | 情感: {sentiment} | 关键点: {', '.join(key_points[:3])}")
            success_count += 1
        else:
            print(f"    ❌ 失败: {result.get('error', '未知错误')}")
            fail_count += 1
    
    print(f"\n监控完成: 成功 {success_count} 人, 失败 {fail_count} 人")
    
    # 生成共识分析
    generate_manager_consensus()
    
    return success_count, fail_count

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=None, help='限制监控人数')
    parser.add_argument('--consensus', action='store_true', help='仅生成共识分析')
    
    args = parser.parse_args()
    
    if args.consensus:
        generate_manager_consensus()
    else:
        run_core_manager_monitor(limit=args.limit)
