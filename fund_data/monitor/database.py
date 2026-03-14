#!/usr/bin/env python3
"""
智能舆情监控系统 - 核心数据库模块
支持MongoDB和JSON文件两种存储模式
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional

# 存储配置
USE_MONGODB = False  # 暂时使用JSON文件，后续切换为MongoDB
DATA_DIR = "/root/.openclaw/workspace/fund_data/monitor"

# 确保数据目录存在
os.makedirs(DATA_DIR, exist_ok=True)

class NewsDatabase:
    """新闻舆情数据库"""
    
    def __init__(self):
        self.file_path = os.path.join(DATA_DIR, "news_collection.json")
        self.data = self._load()
    
    def _load(self) -> List[Dict]:
        """加载数据"""
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def _save(self):
        """保存数据"""
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def insert(self, news: Dict) -> str:
        """插入新闻"""
        news_id = f"NEWS_{datetime.now().strftime('%Y%m%d')}_{len(self.data)+1:03d}"
        news['id'] = news_id
        news['created_at'] = datetime.now().isoformat()
        news['processed'] = False
        self.data.append(news)
        self._save()
        return news_id
    
    def find_unprocessed(self, limit: int = 100) -> List[Dict]:
        """查找未处理的新闻"""
        return [n for n in self.data if not n.get('processed', False)][:limit]
    
    def mark_processed(self, news_id: str, signals: List[Dict]):
        """标记为已处理"""
        for item in self.data:
            if item['id'] == news_id:
                item['processed'] = True
                item['processed_at'] = datetime.now().isoformat()
                item['extracted_signals'] = signals
                break
        self._save()
    
    def get_daily_summary(self, date: str = None) -> Dict:
        """获取每日汇总"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        daily_news = [n for n in self.data if n.get('created_at', '').startswith(date)]
        
        return {
            'date': date,
            'total_count': len(daily_news),
            'unprocessed': len([n for n in daily_news if not n.get('processed')]),
            'sentiment_distribution': self._analyze_sentiment(daily_news),
            'top_keywords': self._extract_keywords(daily_news)
        }
    
    def _analyze_sentiment(self, news_list: List[Dict]) -> Dict:
        """情感分布统计"""
        sentiment = {'positive': 0, 'negative': 0, 'neutral': 0}
        for n in news_list:
            s = n.get('sentiment', 'neutral')
            sentiment[s] = sentiment.get(s, 0) + 1
        return sentiment
    
    def _extract_keywords(self, news_list: List[Dict]) -> List[str]:
        """提取热门关键词"""
        keywords = {}
        for n in news_list:
            for kw in n.get('keywords', []):
                keywords[kw] = keywords.get(kw, 0) + 1
        return sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:10]

class ManagerViewsDatabase:
    """基金经理观点数据库"""
    
    def __init__(self):
        self.file_path = os.path.join(DATA_DIR, "manager_views.json")
        self.data = self._load()
    
    def _load(self) -> List[Dict]:
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def _save(self):
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def insert(self, view: Dict) -> str:
        """插入观点"""
        view_id = f"VIEW_{datetime.now().strftime('%Y%m%d')}_{len(self.data)+1:03d}"
        view['id'] = view_id
        view['created_at'] = datetime.now().isoformat()
        self.data.append(view)
        self._save()
        return view_id
    
    def get_manager_consensus(self, keyword: str) -> Dict:
        """获取基金经理共识"""
        recent_views = [v for v in self.data 
                       if v.get('created_at', '').startswith(datetime.now().strftime('%Y-%m'))]
        
        consensus = {'positive': 0, 'negative': 0, 'neutral': 0}
        for v in recent_views:
            if keyword in v.get('key_points', []):
                sentiment = v.get('sentiment', 'neutral')
                consensus[sentiment] = consensus.get(sentiment, 0) + 1
        
        return consensus

class ResearchReportsDatabase:
    """研报数据库"""
    
    def __init__(self):
        self.file_path = os.path.join(DATA_DIR, "research_reports.json")
        self.data = self._load()
    
    def _load(self) -> List[Dict]:
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def _save(self):
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def insert(self, report: Dict) -> str:
        """插入研报"""
        report_id = f"RPT_{datetime.now().strftime('%Y%m%d')}_{len(self.data)+1:03d}"
        report['id'] = report_id
        report['created_at'] = datetime.now().isoformat()
        self.data.append(report)
        self._save()
        return report_id
    
    def get_broker_consensus(self, category: str) -> List[Dict]:
        """获取券商共识"""
        recent_reports = [r for r in self.data 
                         if r.get('category') == category 
                         and r.get('created_at', '').startswith(datetime.now().strftime('%Y-%m'))]
        return recent_reports

# 全局数据库实例
news_db = NewsDatabase()
manager_db = ManagerViewsDatabase()
report_db = ResearchReportsDatabase()

if __name__ == "__main__":
    # 测试
    print("数据库模块测试")
    print(f"新闻数量: {len(news_db.data)}")
    print(f"观点数量: {len(manager_db.data)}")
    print(f"研报数量: {len(report_db.data)}")
