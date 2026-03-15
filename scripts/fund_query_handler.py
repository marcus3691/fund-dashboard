#!/usr/bin/env python3
"""
飞书指令处理器 - 基金持仓匹配度快速查询
处理自然语言指令，自动分析基金与会议纪要方向的匹配度
"""

import os
import sys
import json
import re
import pandas as pd
from pathlib import Path

class FundQueryHandler:
    """基金查询处理器"""
    
    def __init__(self):
        self.data_dir = "/root/.openclaw/workspace/fund_data"
        self.holdings_dir = f"{self.data_dir}/holdings"
        self.load_fund_data()
        
        # 会议纪要方向关键词映射
        self.direction_keywords = {
            "能源安全": ["煤炭", "石油", "天然气", "电力", "电网", "光伏", "储能"],
            "传统能源": ["煤炭", "石油", "天然气", "原油"],
            "新型电力": ["电网", "电力设备", "光伏", "储能", "特高压", "变压器"],
            "科技自立": ["半导体", "芯片", "存储", "设备", "机器人", "AI"],
            "硬科技": ["半导体设备", "存储芯片", "机器人", "高端装备"],
            "出海制造": ["汽车零部件", "新能源车", "电池", "轮胎", "出海"],
            "价值风格": ["银行", "保险", "白酒", "公用事业"],
            "周期股": ["有色", "稀土", "化工", "钢铁", "煤炭"]
        }
        
        # 股票行业映射（简化版，实际可扩展）
        self.stock_industry = {}
        self._load_stock_info()
    
    def _load_stock_info(self):
        """加载股票信息"""
        # 这里可以从CSV或数据库加载，先用内置的
        basic_info = {
            # 能源
            '601225.SH': '煤炭', '600938.SH': '石油', '000933.SZ': '煤炭',
            '600256.SH': '石油/天然气', '002028.SZ': '电网设备',
            # 有色/稀土
            '603993.SH': '有色', '600362.SH': '有色', '000630.SZ': '有色',
            '600259.SH': '有色/稀土', '000657.SZ': '有色',
            # 光伏/新能源
            '688599.SH': '光伏', '002459.SZ': '光伏', '300274.SZ': '光伏',
            '300014.SZ': '锂电池', '000408.SZ': '锂矿',
            # 半导体/科技
            '002049.SZ': '半导体', '688017.SH': '机器人', '688378.SH': '半导体设备',
            # 汽车/制造
            '601689.SH': '汽车零部件', '002050.SZ': '汽车零部件',
            '002176.SZ': '电机', '601058.SH': '汽车零部件',
            # 价值/防御
            '600519.SH': '白酒', '002142.SZ': '银行', '000568.SZ': '白酒',
            # 航运/其他
            '600026.SH': '航运/油运', '601872.SH': '航运',
            '600760.SH': '军工', '601989.SH': '军工',
        }
        self.stock_industry = basic_info
    
    def load_fund_data(self):
        """加载基金基础数据"""
        csv_path = f"{self.data_dir}/equity_selected_2025_deduplicated.csv"
        if os.path.exists(csv_path):
            self.fund_df = pd.read_csv(csv_path)
        else:
            self.fund_df = pd.DataFrame()
    
    def parse_query(self, query_text):
        """解析用户查询"""
        query_lower = query_text.lower()
        
        # 识别查询意图
        intent = {
            "action": None,
            "fund_code": None,
            "direction": None,
            "top_n": 10
        }
        
        # 提取基金代码
        code_match = re.search(r'(\d{6}\.[A-Z]{2})', query_text)
        if code_match:
            intent["fund_code"] = code_match.group(1)
        
        # 识别动作
        if any(kw in query_lower for kw in ["匹配", "符合", "方向", "分析"]):
            intent["action"] = "match_analysis"
        elif any(kw in query_lower for kw in ["持仓", "重仓", "买了什么"]):
            intent["action"] = "holdings"
        elif any(kw in query_lower for kw in ["top", "排名", "最好"]):
            intent["action"] = "top_ranking"
        
        # 识别方向
        for direction, keywords in self.direction_keywords.items():
            if any(kw in query_text for kw in [direction] + keywords):
                intent["direction"] = direction
                break
        
        # 提取数量
        num_match = re.search(r'(\d+)只', query_text)
        if num_match:
            intent["top_n"] = int(num_match.group(1))
        
        return intent
    
    def get_fund_holdings(self, fund_code):
        """获取基金持仓"""
        file_path = f"{self.holdings_dir}/{fund_code}_holdings.csv"
        if not os.path.exists(file_path):
            return None
        
        df = pd.read_csv(file_path)
        if 'quarter' in df.columns:
            latest_q = df['quarter'].max()
            df = df[df['quarter'] == latest_q]
        
        if 'stk_mkv_ratio' in df.columns:
            df = df.sort_values('stk_mkv_ratio', ascending=False)
        
        return df.head(10)
    
    def analyze_direction_match(self, fund_code, direction=None):
        """分析基金与方向的匹配度"""
        holdings = self.get_fund_holdings(fund_code)
        if holdings is None:
            return {"error": f"未找到 {fund_code} 的持仓数据"}
        
        # 分析持仓行业分布
        industry_dist = {}
        matched_stocks = []
        
        for _, row in holdings.iterrows():
            symbol = row.get('symbol', '')
            ratio = row.get('stk_mkv_ratio', 0)
            
            industry = self.stock_industry.get(symbol, '其他')
            industry_dist[industry] = industry_dist.get(industry, 0) + ratio
            
            # 检查是否匹配指定方向
            if direction:
                keywords = self.direction_keywords.get(direction, [])
                if any(kw in industry for kw in keywords):
                    matched_stocks.append({
                        "symbol": symbol,
                        "industry": industry,
                        "ratio": ratio
                    })
        
        result = {
            "fund_code": fund_code,
            "industry_distribution": dict(sorted(industry_dist.items(), 
                                                  key=lambda x: x[1], 
                                                  reverse=True)),
            "total_analyzed": len(holdings)
        }
        
        if direction:
            matched_ratio = sum(s["ratio"] for s in matched_stocks)
            result["direction"] = direction
            result["match_ratio"] = matched_ratio
            result["matched_stocks"] = matched_stocks
            result["match_score"] = min(matched_ratio / 20, 5)  # 20% = 1星，100% = 5星
        
        return result
    
    def handle_query(self, query_text):
        """处理查询并返回结果"""
        intent = self.parse_query(query_text)
        
        if intent["action"] == "match_analysis":
            if intent["fund_code"]:
                # 分析单只基金
                result = self.analyze_direction_match(
                    intent["fund_code"], 
                    intent["direction"]
                )
                return self.format_match_result(result)
            else:
                # 分析多只基金
                return self.batch_match_analysis(intent["direction"], intent["top_n"])
        
        elif intent["action"] == "holdings":
            if intent["fund_code"]:
                result = self.analyze_direction_match(intent["fund_code"])
                return self.format_holdings_result(result)
        
        elif intent["action"] == "top_ranking":
            return self.get_top_funds(intent["top_n"])
        
        return {"error": "无法识别查询意图，请尝试：\n- 分析基金 013495.OF 的持仓\n- TOP10基金匹配能源安全方向"}
    
    def format_match_result(self, result):
        """格式化匹配结果"""
        if "error" in result:
            return result["error"]
        
        output = [f"\n【{result['fund_code']}】持仓方向分析"]
        output.append("=" * 50)
        
        if "direction" in result:
            stars = "⭐" * int(result.get("match_score", 0))
            output.append(f"\n匹配方向: {result['direction']} {stars}")
            output.append(f"匹配度: {result['match_ratio']:.1f}%")
            
            if result.get("matched_stocks"):
                output.append(f"\n相关持仓:")
                for s in result["matched_stocks"]:
                    output.append(f"  - {s['symbol']} ({s['industry']}): {s['ratio']:.2f}%")
        
        output.append(f"\n行业分布:")
        for ind, ratio in list(result["industry_distribution"].items())[:5]:
            output.append(f"  {ind}: {ratio:.2f}%")
        
        return "\n".join(output)
    
    def format_holdings_result(self, result):
        """格式化持仓结果"""
        if "error" in result:
            return result["error"]
        
        output = [f"\n【{result['fund_code']}】持仓明细"]
        output.append("=" * 50)
        
        for ind, ratio in result["industry_distribution"].items():
            output.append(f"  {ind}: {ratio:.2f}%")
        
        return "\n".join(output)
    
    def batch_match_analysis(self, direction, top_n=10):
        """批量分析多只基金"""
        if self.fund_df.empty:
            return "基金数据未加载"
        
        # 取质量分最高的N只
        top_funds = self.fund_df.nlargest(top_n, 'quality_score')
        
        results = []
        for _, row in top_funds.iterrows():
            fund_code = row['ts_code']
            result = self.analyze_direction_match(fund_code, direction)
            if "error" not in result:
                results.append({
                    "code": fund_code,
                    "name": row.get('name', ''),
                    "quality_score": row.get('quality_score', 0),
                    "match_ratio": result.get("match_ratio", 0),
                    "match_score": result.get("match_score", 0)
                })
        
        # 按匹配度排序
        results.sort(key=lambda x: x["match_score"], reverse=True)
        
        output = [f"\nTOP{top_n}基金匹配【{direction}】方向排名"]
        output.append("=" * 60)
        
        for i, r in enumerate(results[:10], 1):
            stars = "⭐" * int(r["match_score"])
            output.append(f"\n{i}. {r['code']} {r['name']}")
            output.append(f"   质量分: {r['quality_score']:.1f} | 匹配度: {r['match_ratio']:.1f}% {stars}")
        
        return "\n".join(output)
    
    def get_top_funds(self, n=10):
        """获取TOP N基金"""
        if self.fund_df.empty:
            return "基金数据未加载"
        
        top = self.fund_df.nlargest(n, 'quality_score')[['ts_code', 'name', 'quality_score', 'return_1y', 'sharpe']]
        
        output = [f"\nTOP{n} 基金（按质量评分）"]
        output.append("=" * 60)
        
        for i, (_, row) in enumerate(top.iterrows(), 1):
            output.append(f"\n{i}. {row['ts_code']} {row['name']}")
            output.append(f"   质量分: {row['quality_score']:.1f} | 1年收益: {row['return_1y']:.2f}% | 夏普: {row['sharpe']:.2f}")
        
        return "\n".join(output)


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='基金持仓查询工具')
    parser.add_argument('query', nargs='?', help='查询内容')
    parser.add_argument('-i', '--interactive', action='store_true', help='交互模式')
    
    args = parser.parse_args()
    
    handler = FundQueryHandler()
    
    if args.interactive or not args.query:
        print("基金持仓查询系统 - 交互模式")
        print("=" * 60)
        print("示例查询:")
        print("  - 分析 025476.OF 匹配能源安全方向")
        print("  - TOP10基金持仓")
        print("  - 哪些基金符合周期股方向")
        print("  - 退出")
        print("=" * 60)
        
        while True:
            query = input("\n请输入查询: ").strip()
            if query.lower() in ['退出', 'exit', 'quit']:
                break
            if query:
                result = handler.handle_query(query)
                print(result)
    else:
        result = handler.handle_query(args.query)
        print(result)


if __name__ == "__main__":
    main()
