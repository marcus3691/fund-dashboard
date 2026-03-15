#!/usr/bin/env python3
"""
批量基金持仓数据获取与更新
支持批量下载TOP100基金的持仓数据，并自动分析行业分布
"""

import os
import sys
import json
import time
import pandas as pd
from datetime import datetime
from pathlib import Path

class BatchFundProcessor:
    """批量基金处理器"""
    
    def __init__(self):
        self.data_dir = "/root/.openclaw/workspace/fund_data"
        self.holdings_dir = f"{self.data_dir}/holdings"
        self.output_dir = f"{self.data_dir}/batch_analysis"
        
        os.makedirs(self.holdings_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.load_data()
    
    def load_data(self):
        """加载基础数据"""
        csv_path = f"{self.data_dir}/equity_selected_2025_deduplicated.csv"
        if os.path.exists(csv_path):
            self.fund_df = pd.read_csv(csv_path)
            print(f"已加载 {len(self.fund_df)} 只基金数据")
        else:
            self.fund_df = pd.DataFrame()
            print("警告: 未找到基金数据文件")
    
    def get_top_funds(self, n=100):
        """获取TOP N基金"""
        if self.fund_df.empty:
            return []
        
        return self.fund_df.nlargest(n, 'quality_score')['ts_code'].tolist()
    
    def check_existing_holdings(self, fund_code):
        """检查是否已有持仓数据"""
        file_path = f"{self.holdings_dir}/{fund_code}_holdings.csv"
        return os.path.exists(file_path)
    
    def analyze_all_holdings(self, top_n=100):
        """分析所有已有持仓数据的基金"""
        # 获取TOP N基金
        top_funds = self.get_top_funds(top_n)
        
        # 检查哪些有持仓数据
        existing = []
        missing = []
        
        for code in top_funds:
            if self.check_existing_holdings(code):
                existing.append(code)
            else:
                missing.append(code)
        
        print(f"\nTOP{top_n}基金持仓数据情况:")
        print(f"  已有持仓数据: {len(existing)} 只")
        print(f"  缺少持仓数据: {len(missing)} 只")
        
        if missing:
            print(f"\n缺少持仓数据的基金 (前20只):")
            for code in missing[:20]:
                fund_info = self.fund_df[self.fund_df['ts_code'] == code]
                if not fund_info.empty:
                    name = fund_info.iloc[0].get('name', '')
                    score = fund_info.iloc[0].get('quality_score', 0)
                    print(f"  {code} {name} (质量分: {score:.1f})")
        
        return existing, missing
    
    def batch_analyze_industry_distribution(self, fund_codes):
        """批量分析行业分布"""
        # 股票行业映射（扩展版）
        stock_map = {
            # 传统能源
            '601225.SH': ('陕西煤业', '煤炭'), '600938.SH': ('中国海油', '石油'),
            '000933.SZ': ('神火股份', '煤炭'), '600256.SH': ('广汇能源', '石油/天然气'),
            '601857.SH': ('中国石油', '石油'), '600028.SH': ('中国石化', '石油'),
            
            # 有色/稀土
            '603993.SH': ('洛阳钼业', '有色'), '600362.SH': ('江西铜业', '有色'),
            '000630.SZ': ('铜陵有色', '有色'), '600259.SH': ('广晟有色', '有色/稀土'),
            '000657.SZ': ('中钨高新', '有色'), '600111.SH': ('北方稀土', '稀土'),
            
            # 电网/电力设备
            '002028.SZ': ('思源电气', '电网设备'), '600406.SH': ('国电南瑞', '电网设备'),
            '601669.SH': ('中国电建', '电力'), '600900.SH': ('长江电力', '水电'),
            
            # 光伏/新能源
            '688599.SH': ('天合光能', '光伏'), '002459.SZ': ('晶澳科技', '光伏'),
            '300274.SZ': ('阳光电源', '光伏'), '600438.SH': ('通威股份', '光伏'),
            '300014.SZ': ('亿纬锂能', '锂电池'), '300750.SZ': ('宁德时代', '锂电池'),
            '000408.SZ': ('藏格矿业', '锂矿'), '002466.SZ': ('天齐锂业', '锂矿'),
            
            # 半导体/科技
            '002049.SZ': ('紫光国微', '半导体'), '688981.SH': ('中芯国际', '半导体'),
            '603501.SH': ('韦尔股份', '半导体'), '688012.SH': ('中微公司', '半导体设备'),
            '688017.SH': ('绿的谐波', '机器人'), '688378.SH': ('奥来德', '半导体设备'),
            
            # 汽车/制造
            '601689.SH': ('拓普集团', '汽车零部件'), '002050.SZ': ('三花智控', '汽车零部件'),
            '002176.SZ': ('江特电机', '电机'), '601058.SH': ('赛轮轮胎', '汽车零部件'),
            '601127.SH': ('赛力斯', '整车'), '000625.SZ': ('长安汽车', '整车'),
            
            # 银行/金融
            '002142.SZ': ('宁波银行', '银行'), '600036.SH': ('招商银行', '银行'),
            '601398.SH': ('工商银行', '银行'), '601318.SH': ('中国平安', '保险'),
            
            # 白酒/消费
            '600519.SH': ('贵州茅台', '白酒'), '000568.SZ': ('泸州老窖', '白酒'),
            '000858.SZ': ('五粮液', '白酒'),
            
            # 航运/军工
            '600026.SH': ('中远海能', '航运'), '601872.SH': ('招商轮船', '航运'),
            '600760.SH': ('中航沈飞', '军工'), '601989.SH': ('中国重工', '军工'),
            
            # 医药
            '300122.SZ': ('智飞生物', '医药'), '600521.SH': ('华海药业', '医药'),
            '600529.SH': ('山东药玻', '医疗器械'),
            
            # 化工
            '601233.SH': ('桐昆股份', '化工'), '300487.SZ': ('蓝晓科技', '化工'),
        }
        
        results = []
        
        print(f"\n正在批量分析 {len(fund_codes)} 只基金...")
        
        for i, code in enumerate(fund_codes, 1):
            file_path = f"{self.holdings_dir}/{code}_holdings.csv"
            if not os.path.exists(file_path):
                continue
            
            try:
                df = pd.read_csv(file_path)
                
                # 获取最新季度
                if 'quarter' in df.columns:
                    latest_q = df['quarter'].max()
                    df = df[df['quarter'] == latest_q]
                
                if 'stk_mkv_ratio' in df.columns:
                    df = df.sort_values('stk_mkv_ratio', ascending=False)
                
                # 分析行业分布
                industry_dist = {}
                for _, row in df.head(10).iterrows():
                    symbol = row.get('symbol', '')
                    ratio = row.get('stk_mkv_ratio', 0)
                    
                    _, industry = stock_map.get(symbol, ('', '其他'))
                    industry_dist[industry] = industry_dist.get(industry, 0) + ratio
                
                # 获取基金信息
                fund_info = self.fund_df[self.fund_df['ts_code'] == code]
                fund_name = fund_info.iloc[0].get('name', '') if not fund_info.empty else ''
                quality_score = fund_info.iloc[0].get('quality_score', 0) if not fund_info.empty else 0
                
                results.append({
                    'code': code,
                    'name': fund_name,
                    'quality_score': quality_score,
                    'industry_distribution': industry_dist,
                    'top_industry': max(industry_dist.items(), key=lambda x: x[1]) if industry_dist else ('', 0)
                })
                
                if i % 10 == 0:
                    print(f"  已处理 {i}/{len(fund_codes)}...")
                
            except Exception as e:
                print(f"  处理 {code} 时出错: {e}")
                continue
        
        return results
    
    def generate_industry_report(self, analysis_results):
        """生成行业分布报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"{self.output_dir}/industry_analysis_{timestamp}.json"
        
        # 保存详细结果
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n详细结果已保存: {output_file}")
        
        # 生成汇总统计
        all_industries = {}
        for r in analysis_results:
            for ind, ratio in r['industry_distribution'].items():
                all_industries[ind] = all_industries.get(ind, [])
                all_industries[ind].append({
                    'code': r['code'],
                    'name': r['name'],
                    'ratio': ratio,
                    'quality_score': r['quality_score']
                })
        
        # 按行业汇总
        industry_summary = []
        for ind, funds in all_industries.items():
            avg_quality = sum(f['quality_score'] for f in funds) / len(funds)
            total_ratio = sum(f['ratio'] for f in funds)
            industry_summary.append({
                'industry': ind,
                'fund_count': len(funds),
                'avg_quality_score': avg_quality,
                'total_ratio': total_ratio
            })
        
        industry_summary.sort(key=lambda x: x['fund_count'], reverse=True)
        
        # 输出汇总
        print("\n" + "="*60)
        print("行业分布汇总")
        print("="*60)
        
        for item in industry_summary[:15]:
            print(f"\n【{item['industry']}】")
            print(f"  涉及基金: {item['fund_count']} 只")
            print(f"  平均质量分: {item['avg_quality_score']:.1f}")
            print(f"  持仓占比合计: {item['total_ratio']:.1f}%")
            
            # 显示该行业持仓最多的3只基金
            top_funds = sorted(all_industries[item['industry']], 
                              key=lambda x: x['ratio'], 
                              reverse=True)[:3]
            print(f"  重点基金:")
            for f in top_funds:
                print(f"    - {f['code']} {f['name']}: {f['ratio']:.1f}%")
        
        return industry_summary
    
    def find_opportunity_funds(self, target_industries, min_quality_score=85):
        """寻找特定行业的优质基金"""
        print(f"\n寻找重仓【{'/'.join(target_industries)}】的基金 (质量分≥{min_quality_score})...")
        
        # 获取有持仓数据的基金
        existing, _ = self.analyze_all_holdings(top_n=100)
        
        matches = []
        for code in existing:
            file_path = f"{self.holdings_dir}/{code}_holdings.csv"
            try:
                df = pd.read_csv(file_path)
                
                if 'quarter' in df.columns:
                    df = df[df['quarter'] == df['quarter'].max()]
                
                # 获取基金信息
                fund_info = self.fund_df[self.fund_df['ts_code'] == code]
                if fund_info.empty:
                    continue
                
                quality_score = fund_info.iloc[0].get('quality_score', 0)
                if quality_score < min_quality_score:
                    continue
                
                fund_name = fund_info.iloc[0].get('name', '')
                
                # 检查持仓是否匹配目标行业
                matched_ratio = 0
                matched_stocks = []
                
                for _, row in df.iterrows():
                    symbol = row.get('symbol', '')
                    ratio = row.get('stk_mkv_ratio', 0)
                    
                    # 简单匹配（实际可以更精确）
                    for target in target_industries:
                        if target in symbol or self._is_industry_match(symbol, target):
                            matched_ratio += ratio
                            matched_stocks.append((symbol, ratio))
                
                if matched_ratio > 10:  # 至少10%持仓匹配
                    matches.append({
                        'code': code,
                        'name': fund_name,
                        'quality_score': quality_score,
                        'matched_ratio': matched_ratio,
                        'stocks': matched_stocks
                    })
            
            except Exception as e:
                continue
        
        # 按匹配度排序
        matches.sort(key=lambda x: x['matched_ratio'], reverse=True)
        
        print(f"\n找到 {len(matches)} 只符合条件的基金:")
        for i, m in enumerate(matches[:10], 1):
            print(f"\n{i}. {m['code']} {m['name']}")
            print(f"   质量分: {m['quality_score']:.1f} | 匹配持仓: {m['matched_ratio']:.1f}%")
            print(f"   相关持仓: {', '.join([f'{s[0]}({s[1]:.1f}%)' for s in m['stocks'][:3]])}")
        
        return matches
    
    def _is_industry_match(self, symbol, target_industry):
        """检查股票是否属于目标行业（简化版）"""
        # 这里可以扩展更详细的映射
        industry_map = {
            '煤炭': ['601225.SH', '000933.SZ', '600123.SH'],
            '石油': ['600938.SH', '600256.SH', '601857.SH'],
            '有色': ['603993.SH', '600362.SH', '000630.SZ'],
            '稀土': ['600259.SH', '600111.SH'],
            '光伏': ['688599.SH', '002459.SZ', '300274.SZ'],
            '半导体': ['002049.SZ', '688981.SH', '603501.SH'],
        }
        
        for ind, symbols in industry_map.items():
            if target_industry in ind and symbol in symbols:
                return True
        return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='批量基金分析工具')
    parser.add_argument('--analyze', action='store_true', help='分析已有持仓数据')
    parser.add_argument('--top-n', type=int, default=50, help='分析前N只基金')
    parser.add_argument('--find', nargs='+', help='寻找特定行业的基金')
    parser.add_argument('--min-score', type=float, default=85, help='最低质量分')
    
    args = parser.parse_args()
    
    processor = BatchFundProcessor()
    
    if args.analyze:
        # 分析已有持仓
        existing, missing = processor.analyze_all_holdings(args.top_n)
        
        if existing:
            results = processor.batch_analyze_industry_distribution(existing)
            processor.generate_industry_report(results)
    
    elif args.find:
        # 寻找特定行业基金
        processor.find_opportunity_funds(args.find, args.min_score)
    
    else:
        # 默认：分析持仓数据情况
        existing, missing = processor.analyze_all_holdings(args.top_n)
        
        print("\n" + "="*60)
        print("使用说明:")
        print("="*60)
        print("1. 分析已有持仓分布:")
        print(f"   python3 {sys.argv[0]} --analyze --top-n 50")
        print("\n2. 寻找能源/有色行业基金:")
        print(f"   python3 {sys.argv[0]} --find 煤炭 石油 有色 --min-score 90")


if __name__ == "__main__":
    main()
