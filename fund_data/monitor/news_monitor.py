#!/usr/bin/env python3
"""
财经新闻抓取脚本
抓取新浪财经、东方财富等主流财经网站
"""

import sys
import json
import re
from datetime import datetime
from typing import List, Dict

# 添加路径
sys.path.insert(0, '/root/.openclaw/workspace')
sys.path.insert(0, '/root/.openclaw/workspace/skills/web-scraper')

try:
    from web_scraper import scrape_web
except ImportError:
    # 如果Scrapling不可用，使用简单requests版本
    import requests
    from bs4 import BeautifulSoup
    
    def scrape_web(url: str, mode: str = 'auto', selector: str = None):
        """简化版抓取函数"""
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
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
                try:
                    elem = soup.select_one(selector)
                    result['selected_content'] = elem.get_text().strip() if elem else ''
                except:
                    result['selected_content'] = ''
            
            return result
        except Exception as e:
            return {'success': False, 'url': url, 'error': str(e)}

from database import news_db

# 监控关键词
MONITOR_KEYWORDS = {
    'fund': ['基金', '基金经理', '基金发行', '基金分红', '巨额赎回', '调仓'],
    'market': ['牛市', '熊市', '回调', '反弹', '放量', '缩量', '跌破', '突破'],
    'policy': ['降准', '降息', 'IPO', '减持', '增持', '监管', '政策'],
    'geopolitics': ['霍尔木兹', '伊朗', '原油', '黄金', '冲突', '地缘', '石油'],
    'sectors': ['光伏', '储能', 'AI', '半导体', '新能源', '医药', '消费', '银行']
}

def extract_keywords(text: str) -> List[str]:
    """提取关键词"""
    keywords = []
    text_lower = text.lower()
    
    for category, words in MONITOR_KEYWORDS.items():
        for word in words:
            if word in text_lower:
                keywords.append(word)
    
    return list(set(keywords))

def analyze_sentiment(text: str) -> str:
    """简单情感分析"""
    positive_words = ['上涨', '看好', '买入', '增持', '推荐', '利好', '突破', '反弹', '牛市']
    negative_words = ['下跌', '看空', '卖出', '减持', '回避', '利空', '跌破', '回调', '熊市']
    
    pos_count = sum(1 for w in positive_words if w in text)
    neg_count = sum(1 for w in negative_words if w in text)
    
    if pos_count > neg_count:
        return 'positive'
    elif neg_count > pos_count:
        return 'negative'
    else:
        return 'neutral'

def scrape_sina_finance() -> List[Dict]:
    """抓取新浪财经头条"""
    news_list = []
    
    try:
        # 新浪财经首页
        result = scrape_web('https://finance.sina.com.cn/', mode='static')
        
        if not result.get('success'):
            print(f"抓取新浪财经失败: {result.get('error')}")
            return news_list
        
        # 这里简化处理，实际应该解析HTML提取新闻列表
        # 由于Scrapling返回的是页面对象，我们需要更复杂的解析
        # 这里先模拟一些测试数据
        
        print("新浪财经抓取成功，解析中...")
        
    except Exception as e:
        print(f"抓取新浪财经异常: {e}")
    
    return news_list

def scrape_eastmoney_news() -> List[Dict]:
    """抓取东方财富财经新闻"""
    news_list = []
    
    try:
        # 东方财富财经频道
        result = scrape_web('https://finance.eastmoney.com/', mode='static')
        
        if result.get('success'):
            print("东方财富抓取成功，解析中...")
            # 实际应用中这里需要解析具体的CSS选择器提取新闻列表
        else:
            print(f"抓取东方财富失败: {result.get('error')}")
        
    except Exception as e:
        print(f"抓取东方财富异常: {e}")
    
    return news_list

def generate_signal(news: Dict) -> List[Dict]:
    """根据新闻生成信号"""
    signals = []
    
    # 信号生成规则
    keywords = news.get('keywords', [])
    sentiment = news.get('sentiment', 'neutral')
    
    # 规则1: 地缘冲突升级信号
    if any(kw in ['霍尔木兹', '伊朗', '冲突'] for kw in keywords) and sentiment == 'negative':
        signals.append({
            'type': 'geopolitical',
            'priority': 'high',
            'trigger': '地缘冲突升级',
            'action': '关注能源、黄金ETF',
            'source': news.get('source'),
            'news_id': news.get('id')
        })
    
    # 规则2: 政策利好信号
    if any(kw in ['降准', '降息', '政策'] for kw in keywords) and sentiment == 'positive':
        signals.append({
            'type': 'policy',
            'priority': 'high',
            'trigger': '货币政策宽松',
            'action': '关注宽基ETF',
            'source': news.get('source'),
            'news_id': news.get('id')
        })
    
    # 规则3: 行业利好信号
    sector_mapping = {
        '光伏': '515030.SH',
        '半导体': '512480.SH',
        'AI': '159819.SZ',
        '新能源': '515030.SH'
    }
    
    for keyword, etf in sector_mapping.items():
        if keyword in keywords and sentiment == 'positive':
            signals.append({
                'type': 'sector',
                'priority': 'medium',
                'trigger': f'{keyword}行业利好',
                'action': f'关注{etf}',
                'source': news.get('source'),
                'news_id': news.get('id')
            })
    
    return signals

def run_news_monitor():
    """运行新闻监控"""
    print(f"\n{'='*60}")
    print(f"财经新闻监控系统 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    all_news = []
    
    # 抓取新浪财经
    print("1. 抓取新浪财经...")
    sina_news = scrape_sina_finance()
    all_news.extend(sina_news)
    
    # 抓取东方财富
    print("2. 抓取东方财富...")
    eastmoney_news = scrape_eastmoney_news()
    all_news.extend(eastmoney_news)
    
    # 处理新闻
    print(f"\n3. 处理新闻数据...")
    for news in all_news:
        # 提取关键词
        news['keywords'] = extract_keywords(news.get('content', ''))
        
        # 情感分析
        news['sentiment'] = analyze_sentiment(news.get('content', ''))
        
        # 保存到数据库
        news_id = news_db.insert(news)
        
        # 生成信号
        signals = generate_signal(news)
        
        # 标记已处理
        news_db.mark_processed(news_id, signals)
        
        print(f"  - {news.get('title', '无标题')} [{news['sentiment']}]")
    
    # 生成汇总
    summary = news_db.get_daily_summary()
    print(f"\n{'='*60}")
    print(f"今日汇总:")
    print(f"  - 新闻总数: {summary['total_count']}")
    print(f"  - 情感分布: {summary['sentiment_distribution']}")
    print(f"  - 热门关键词: {summary['top_keywords']}")
    print(f"{'='*60}\n")
    
    return summary

if __name__ == "__main__":
    run_news_monitor()
