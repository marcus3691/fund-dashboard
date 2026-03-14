#!/usr/bin/env python3
"""
ETF调仓信号自动抓取系统
Tushare + 新浪财经 + 东方财富 + 人工复核
"""

import json
import os
import sys
import re
import time
from datetime import datetime, timedelta
from urllib.request import urlopen, Request
from urllib.parse import quote
import ssl

# 屏蔽SSL验证（部分网站需要）
ssl._create_default_https_context = ssl._create_unverified_context

# 关键词配置
KEYWORDS = {
    "geopolitical": {
        "keywords": ["霍尔木兹", "伊朗", "以色列", "中东", "石油", "航运", "BDI", "地缘"],
        "threshold": 0.6,  # 匹配度阈值
        "priority": "high"
    },
    "tech_rotation": {
        "keywords": ["英伟达", "NVIDIA", "AI芯片", "光模块", "CPO", "大模型", "算力", "OpenAI", "ChatGPT"],
        "threshold": 0.5,
        "priority": "medium"
    },
    "macro": {
        "keywords": ["美联储", "加息", "降息", "CPI", "PMI", "OPEC", "原油库存", "GDP", "中美"],
        "threshold": 0.6,
        "priority": "high"
    }
}

# Tushare配置（从环境变量或配置文件读取）
TUSHARE_TOKEN = os.environ.get('TUSHARE_TOKEN', '33996190080200cd63a01732ad443c390d9d580913ec938d4e1d704d')

def fetch_tushare_major_news():
    """
    从Tushare获取重要新闻快讯
    需要TUSHARE_TOKEN环境变量
    """
    if not TUSHARE_TOKEN:
        print("⚠️ 未配置TUSHARE_TOKEN，跳过Tushare抓取")
        return []
    
    try:
        import tushare as ts
        pro = ts.pro_api(TUSHARE_TOKEN)
        
        # 获取最近24小时的重要新闻
        df = pro.major_news(start_date=(datetime.now() - timedelta(days=1)).strftime('%Y%m%d'),
                           end_date=datetime.now().strftime('%Y%m%d'))
        
        news_list = []
        for _, row in df.iterrows():
            news_list.append({
                "title": row.get('title', ''),
                "content": row.get('content', ''),
                "source": "Tushare",
                "time": row.get('datetime', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                "url": ""
            })
        
        print(f"✅ Tushare抓取: {len(news_list)}条新闻")
        return news_list
        
    except Exception as e:
        print(f"❌ Tushare抓取失败: {str(e)}")
        return []

def fetch_sina_finance():
    """
    抓取新浪财经快讯
    """
    try:
        url = "https://finance.sina.com.cn/stock/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        req = Request(url, headers=headers)
        with urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
        
        # 简单的正则提取新闻标题
        # 实际应用中需要更精确的解析
        news_list = []
        
        # 匹配新闻标题的正则（示例）
        pattern = r'<a[^>]*href="([^"]*finance[^"]*)"[^>]*>([^<]{10,100})</a>'
        matches = re.findall(pattern, html)
        
        for url, title in matches[:10]:  # 只取前10条
            news_list.append({
                "title": title.strip(),
                "content": "",
                "source": "新浪财经",
                "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "url": url if url.startswith('http') else f"https://finance.sina.com.cn{url}"
            })
        
        print(f"✅ 新浪财经抓取: {len(news_list)}条新闻")
        return news_list
        
    except Exception as e:
        print(f"❌ 新浪财经抓取失败: {str(e)}")
        return []

def fetch_eastmoney_news():
    """
    抓取东方财富要闻
    """
    try:
        url = "https://finance.eastmoney.com/a/cywjh.html"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        req = Request(url, headers=headers)
        with urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
        
        news_list = []
        
        # 匹配东方财富新闻标题
        pattern = r'<a[^>]*href="([^"]*)"[^>]*title="([^"]*)"[^>]*>'
        matches = re.findall(pattern, html)
        
        for url, title in matches[:10]:
            news_list.append({
                "title": title.strip(),
                "content": "",
                "source": "东方财富",
                "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "url": url if url.startswith('http') else f"https://finance.eastmoney.com{url}"
            })
        
        print(f"✅ 东方财富抓取: {len(news_list)}条新闻")
        return news_list
        
    except Exception as e:
        print(f"❌ 东方财富抓取失败: {str(e)}")
        return []

def analyze_news(news_list):
    """
    分析新闻内容，匹配关键词，生成信号候选
    """
    signals = []
    
    for news in news_list:
        title = news.get('title', '')
        content = news.get('content', '')
        full_text = f"{title} {content}"
        
        for signal_type, config in KEYWORDS.items():
            keywords = config['keywords']
            threshold = config['threshold']
            priority = config['priority']
            
            # 计算匹配度
            matched_keywords = [k for k in keywords if k in full_text]
            match_ratio = len(matched_keywords) / len(keywords)
            
            if match_ratio >= threshold and len(matched_keywords) >= 2:
                # 生成信号候选
                signal = {
                    "id": f"AUTO_{datetime.now().strftime('%Y%m%d')}_{len(signals)+1:03d}",
                    "timestamp": datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
                    "type": signal_type,
                    "priority": priority,
                    "status": "pending_review",  # 需要人工复核
                    "trigger": {
                        "event": title[:50] + "..." if len(title) > 50 else title,
                        "threshold": f"关键词匹配: {', '.join(matched_keywords[:3])}",
                        "current_value": f"匹配度: {match_ratio:.1%}",
                        "source": news['source']
                    },
                    "action": {
                        "layer": "satellite" if signal_type == "tech_rotation" else "core",
                        "target": infer_target_etfs(signal_type, matched_keywords),
                        "direction": "待确认",
                        "suggested_weight": 3 if priority == "medium" else 5,
                        "rationale": f"自动检测到关键词: {', '.join(matched_keywords)}"
                    },
                    "review_status": "pending",
                    "reviewer": None,
                    "review_notes": f"原始新闻: {news.get('url', '无链接')}",
                    "expires_at": (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%dT%H:%M:%S')
                }
                
                signals.append(signal)
                print(f"🎯 发现信号候选: {signal['id']} - {signal_type} - 匹配度{match_ratio:.1%}")
    
    return signals

def infer_target_etfs(signal_type, keywords):
    """
    根据信号类型和关键词推断目标ETF
    """
    etf_mapping = {
        "geopolitical": {
            "霍尔木兹": "515220.SH,518880.SH",  # 煤炭、黄金
            "伊朗": "515220.SH,512400.SH",       # 煤炭、有色
            "以色列": "518880.SH",                # 黄金
            "石油": "515220.SH",                  # 煤炭
            "航运": "159972.SZ"                   # 地债（替代航运）
        },
        "tech_rotation": {
            "英伟达": "512480.SH,515880.SH",      # 半导体、通信
            "NVIDIA": "512480.SH,515880.SH",
            "AI芯片": "512480.SH",
            "光模块": "515880.SH",
            "CPO": "515880.SH",
            "大模型": "159819.SZ,516510.SH",      # AI、云计算
            "算力": "512480.SH,516510.SH",
            "OpenAI": "159819.SZ"
        },
        "macro": {
            "美联储": "518880.SH,511010.SH",      # 黄金、国债
            "加息": "511010.SH",                  # 国债
            "降息": "510300.SH",                  # 沪深300
            "CPI": "518880.SH",                   # 黄金
            "OPEC": "515220.SH"                   # 煤炭
        }
    }
    
    targets = set()
    mapping = etf_mapping.get(signal_type, {})
    
    for keyword in keywords:
        if keyword in mapping:
            for code in mapping[keyword].split(','):
                targets.add(code)
    
    return ','.join(list(targets)) if targets else "待确认"

def save_signals(signals):
    """
    保存信号到待复核队列
    """
    if not signals:
        print("ℹ️ 未发现新的信号候选")
        return
    
    signals_file = os.path.join(os.path.dirname(__file__), '..', 'etf_signals.json')
    
    # 读取现有数据
    with open(signals_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 添加到待复核队列
    existing_ids = {s['id'] for s in data.get('pending_signals', [])}
    new_signals = [s for s in signals if s['id'] not in existing_ids]
    
    if new_signals:
        data['pending_signals'].extend(new_signals)
        
        # 保存
        with open(signals_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 已保存 {len(new_signals)} 个信号到待复核队列")
        print(f"📋 请人工复核后发布: {signals_file}")
    else:
        print("\nℹ️ 所有信号已存在，未添加重复项")

def main():
    """
    主函数：抓取新闻 → 分析 → 生成信号候选
    """
    print(f"\n{'='*60}")
    print(f"ETF调仓信号自动抓取系统")
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    all_news = []
    
    # 1. Tushare抓取
    print("📡 正在抓取Tushare...")
    all_news.extend(fetch_tushare_major_news())
    time.sleep(1)
    
    # 2. 新浪财经抓取
    print("📡 正在抓取新浪财经...")
    all_news.extend(fetch_sina_finance())
    time.sleep(1)
    
    # 3. 东方财富抓取
    print("📡 正在抓取东方财富...")
    all_news.extend(fetch_eastmoney_news())
    
    print(f"\n📊 共抓取 {len(all_news)} 条新闻")
    
    # 4. 分析新闻，生成信号
    if all_news:
        print("\n🔍 正在分析新闻内容...")
        signals = analyze_news(all_news)
        
        # 5. 保存信号
        save_signals(signals)
    
    print(f"\n{'='*60}")
    print("抓取完成！请人工复核 pending_signals 后发布。")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
