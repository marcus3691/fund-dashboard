#!/usr/bin/env python3
"""
观点冲突检测系统
自动识别不同来源（研报/纪要/文章）之间的观点冲突和一致性
"""

import os
import json
import re
from datetime import datetime
from pathlib import Path

class OpinionConflictDetector:
    """观点冲突检测器"""
    
    def __init__(self):
        self.opinions_db = []
        self.keywords_map = {
            "黄金": ["黄金", "贵金属", "金价"],
            "原油": ["原油", "石油", "油价", "能源"],
            "煤炭": ["煤炭", "动力煤", "焦煤"],
            "有色": ["有色", "铜", "铝", "稀土"],
            "光伏": ["光伏", "太阳能", "储能"],
            "半导体": ["半导体", "芯片", "存储", "设备"],
            "AI": ["AI", "人工智能", "大模型"],
            "军工": ["军工", "国防", "航空"],
            "医药": ["医药", "医疗", "创新药", "医疗器械"],
            "消费": ["消费", "白酒", "食品饮料"],
            "银行": ["银行", "金融", "保险"],
            "港股": ["港股", "恒生科技", "互联网"],
        }
        
        self.sentiment_keywords = {
            "看好": ["看好", "推荐", "关注", "机会", "上行", "配置", "优选", "强势"],
            "看空": ["看空", "谨慎", "回避", "风险", "下行", "调整", "压力", "不利"],
            "中性": ["中性", "震荡", "观望", "等待", "不确定"]
        }
    
    def add_opinion(self, source, date, content, source_type="article"):
        """添加观点到数据库"""
        # 提取涉及的主题
        topics = self._extract_topics(content)
        
        # 提取对每个主题的观点
        topic_opinions = {}
        for topic in topics:
            sentiment = self._extract_sentiment(content, topic)
            topic_opinions[topic] = sentiment
        
        opinion = {
            "source": source,
            "date": date,
            "source_type": source_type,
            "content_preview": content[:500],
            "topics": topics,
            "topic_opinions": topic_opinions,
            "added_at": datetime.now().isoformat()
        }
        
        self.opinions_db.append(opinion)
        return opinion
    
    def _extract_topics(self, content):
        """提取文本涉及的主题"""
        topics = []
        for topic, keywords in self.keywords_map.items():
            if any(kw in content for kw in keywords):
                topics.append(topic)
        return topics
    
    def _extract_sentiment(self, content, topic):
        """提取对特定主题的观点倾向"""
        # 找到主题附近的句子
        sentences = re.split(r'[。！？\n]', content)
        
        relevant_sentences = []
        for sent in sentences:
            if any(kw in sent for kw in self.keywords_map.get(topic, [])):
                relevant_sentences.append(sent)
        
        if not relevant_sentences:
            return {"sentiment": "未知", "confidence": 0, "evidence": ""}
        
        # 分析情感倾向
        combined_text = " ".join(relevant_sentences)
        
        bullish_count = sum(1 for kw in self.sentiment_keywords["看好"] if kw in combined_text)
        bearish_count = sum(1 for kw in self.sentiment_keywords["看空"] if kw in combined_text)
        
        if bullish_count > bearish_count:
            sentiment = "看好"
            confidence = min(bullish_count * 0.3, 1.0)
        elif bearish_count > bullish_count:
            sentiment = "看空"
            confidence = min(bearish_count * 0.3, 1.0)
        else:
            sentiment = "中性"
            confidence = 0.3
        
        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "evidence": relevant_sentences[0][:100] if relevant_sentences else ""
        }
    
    def detect_conflicts(self, topic=None):
        """检测观点冲突"""
        conflicts = []
        
        # 按主题分组
        topic_groups = {}
        for opinion in self.opinions_db:
            for t in opinion["topics"]:
                if topic and t != topic:
                    continue
                if t not in topic_groups:
                    topic_groups[t] = []
                topic_groups[t].append(opinion)
        
        # 检测每个主题的冲突
        for t, opinions in topic_groups.items():
            if len(opinions) < 2:
                continue
            
            # 提取观点
            views = []
            for op in opinions:
                if t in op["topic_opinions"]:
                    views.append({
                        "source": op["source"],
                        "date": op["date"],
                        "sentiment": op["topic_opinions"][t]["sentiment"],
                        "confidence": op["topic_opinions"][t]["confidence"],
                        "evidence": op["topic_opinions"][t]["evidence"]
                    })
            
            # 检测冲突
            bullish = [v for v in views if v["sentiment"] == "看好"]
            bearish = [v for v in views if v["sentiment"] == "看空"]
            
            if bullish and bearish:
                conflicts.append({
                    "topic": t,
                    "type": "观点冲突",
                    "severity": "高" if len(bullish) >= 2 and len(bearish) >= 2 else "中",
                    "bullish_views": bullish,
                    "bearish_views": bearish,
                    "summary": f"{t}: {len(bullish)}个看好 vs {len(bearish)}个看空"
                })
            elif len(views) >= 2:
                # 检查一致性
                sentiments = [v["sentiment"] for v in views]
                if len(set(sentiments)) == 1:
                    conflicts.append({
                        "topic": t,
                        "type": "观点一致",
                        "severity": "信息",
                        "views": views,
                        "summary": f"{t}: {len(views)}个来源一致看好" if sentiments[0] == "看好" else f"{t}: {len(views)}个来源一致看空"
                    })
        
        return conflicts
    
    def generate_conflict_report(self):
        """生成冲突检测报告"""
        conflicts = self.detect_conflicts()
        
        output = []
        output.append("="*70)
        output.append("观点冲突检测报告")
        output.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output.append(f"分析来源数: {len(self.opinions_db)}")
        output.append("="*70)
        
        # 分离冲突和一致
        real_conflicts = [c for c in conflicts if c["type"] == "观点冲突"]
        agreements = [c for c in conflicts if c["type"] == "观点一致"]
        
        if real_conflicts:
            output.append("\n⚠️ 观点冲突发现")
            output.append("-"*70)
            
            for c in real_conflicts:
                output.append(f"\n【{c['topic']}】冲突级别: {c['severity']}")
                output.append(f"{c['summary']}")
                
                output.append(f"\n  👍 看好方:")
                for v in c["bullish_views"][:2]:
                    output.append(f"    - {v['source']} ({v['date']}): {v['evidence']}")
                
                output.append(f"\n  👎 看空方:")
                for v in c["bearish_views"][:2]:
                    output.append(f"    - {v['source']} ({v['date']}): {v['evidence']}")
                
                output.append(f"\n  💡 建议:")
                output.append(f"    观点分歧较大，建议等待更明确的信号或深入研究双方论据")
        else:
            output.append("\n✅ 未发现明显观点冲突")
        
        if agreements:
            output.append("\n\n📊 观点一致性发现")
            output.append("-"*70)
            
            for a in agreements[:5]:  # 只显示前5个
                output.append(f"\n【{a['topic']}】{a['summary']}")
                for v in a["views"][:2]:
                    output.append(f"  - {v['source']} ({v['date']})")
        
        return "\n".join(output)
    
    def compare_with_meeting_minutes(self, fund_code, meeting_topics):
        """对比基金持仓与会议纪要方向"""
        # 读取基金持仓
        holdings_file = f"/root/.openclaw/workspace/fund_data/holdings/{fund_code}_holdings.csv"
        if not os.path.exists(holdings_file):
            return {"error": f"未找到 {fund_code} 持仓数据"}
        
        import pandas as pd
        df = pd.read_csv(holdings_file)
        
        # 提取持仓行业
        stock_industry = {
            '601225.SH': '煤炭', '600938.SH': '石油', '000933.SZ': '煤炭',
            '603993.SH': '有色', '600362.SH': '有色', '000630.SZ': '有色',
            '600259.SH': '有色/稀土', '600111.SH': '稀土',
            '002028.SZ': '电网设备', '688599.SH': '光伏', '002459.SZ': '光伏',
            '300274.SZ': '光伏', '002049.SZ': '半导体', '688981.SH': '半导体',
            '601689.SH': '汽车零部件', '002050.SZ': '汽车零部件',
            '600519.SH': '白酒', '002142.SZ': '银行',
            '600026.SH': '航运', '601872.SH': '航运',
        }
        
        if 'quarter' in df.columns:
            df = df[df['quarter'] == df['quarter'].max()]
        
        holdings_industries = {}
        for _, row in df.iterrows():
            symbol = row.get('symbol', '')
            ratio = row.get('stk_mkv_ratio', 0)
            industry = stock_industry.get(symbol, '其他')
            holdings_industries[industry] = holdings_industries.get(industry, 0) + ratio
        
        # 对比会议纪要方向
        aligned = []
        misaligned = []
        
        for topic in meeting_topics:
            if topic in holdings_industries:
                aligned.append({
                    "topic": topic,
                    "ratio": holdings_industries[topic],
                    "match": True
                })
            else:
                misaligned.append({
                    "topic": topic,
                    "match": False
                })
        
        return {
            "fund_code": fund_code,
            "aligned_topics": aligned,
            "misaligned_topics": misaligned,
            "alignment_score": len(aligned) / len(meeting_topics) if meeting_topics else 0,
            "holdings_industries": holdings_industries
        }


def demo():
    """演示：添加之前的几个来源并进行冲突检测"""
    detector = OpinionConflictDetector()
    
    # 添加一粒尘埃的观点（2026-03-09）
    detector.add_opinion(
        source="一粒尘埃《黄金走势的误解与认知》",
        date="2026-03-09",
        content="""
        黄金处于五十年大牛市中的区间震荡，不是历史大顶。
        供给短缺型通胀不应该加息，黄金与油价基本同步。
        中东国家抛售流动性资产导致调整，美债利率企稳=流动性冲击结束。
        看好黄金中长期，资金最终投向印钞机的对立面（黄金）或中国资产。
        """
    )
    
    # 添加韦冀星的观点（2026-03-09）
    detector.add_opinion(
        source="韦冀星《美以伊冲突》",
        date="2026-03-09",
        content="""
        冲突将长尾化，霍尔木兹海峡封锁威胁全球能源安全。
        看好航运、黄金、能源上游（石油、煤炭、煤化工）。
        看好军工AI、无人机。增持能源与航运多头。
        """
    )
    
    # 添加国泰基金观点（2026-03-13）
    detector.add_opinion(
        source="国泰基金多资产配置部3月观点",
        date="2026-03-13",
        content="""
        伊朗冲突带来阶段性超高油价，原油主导暂时领先，之后贵金属再度主导。
        看好中线稀土、短期煤炭。看好电网设备、绿电。
        看好有色、能源产业链。金银暂且休息。
        价值风格占优，看好银行、白酒等防御性资产。
        """
    )
    
    # 添加会议纪要观点（2026-03-13）
    detector.add_opinion(
        source="3月投资月度会议纪要",
        date="2026-03-13",
        content="""
        能源安全是核心主线，看好煤炭、石油、电网设备、绿电。
        科技自立看好半导体设备、新能源车产业链（出海）。
        不看好的方向：AI应用、消费、创新药、港股互联网。
        短期谨慎，中期乐观。价值风格优于成长风格。
        """
    )
    
    # 生成报告
    report = detector.generate_conflict_report()
    print(report)
    
    # 保存数据库
    output_file = "/root/.openclaw/workspace/opinions_db.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(detector.opinions_db, f, ensure_ascii=False, indent=2)
    
    print(f"\n\n观点数据库已保存: {output_file}")
    
    return detector


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo()
    else:
        print("观点冲突检测系统")
        print("="*60)
        print("用法:")
        print("  python3 opinion_conflict_detector.py demo  - 运行演示")
        print("\nAPI使用:")
        print("  detector = OpinionConflictDetector()")
        print("  detector.add_opinion(source, date, content)")
        print("  conflicts = detector.detect_conflicts()")
