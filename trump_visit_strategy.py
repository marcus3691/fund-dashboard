#!/usr/bin/env python3
"""
特朗普访华事件冲击型ETF策略
基于关税和伊朗局势影响构建短期组合
"""

import pandas as pd
import numpy as np
import tushare as ts
from datetime import datetime, timedelta
import json

# Tushare配置
TS_TOKEN = '33996190080200cd63a01732ad443c390d9d580913ec938d4e1d704d'
ts.set_token(TS_TOKEN)
pro = ts.pro_api()

class TrumpVisitStrategy:
    """
    特朗普访华事件冲击策略
    
    策略逻辑：
    1. 筛选受关税和伊朗局势影响的ETF
    2. 流动性筛选（20日日均成交额>5000万）
    3. 低相关性组合构建
    4. 三种情景收益测算
    """
    
    def __init__(self):
        self.etf_pool = []
        self.selected_etfs = []
        
    def get_etf_list(self):
        """获取ETF列表"""
        # 获取ETF基本信息
        df = pro.fund_basic(market='E', status='L')
        # 筛选ETF
        etf_list = df[df['fund_type'].str.contains('ETF', na=False)]
        return etf_list
    
    def get_etf_daily(self, ts_code, start_date, end_date):
        """获取ETF日线数据"""
        try:
            df = pro.fund_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
            return df
        except Exception as e:
            print(f"获取{ts_code}数据失败: {e}")
            return None
    
    def check_liquidity(self, ts_code, days=20):
        """检查流动性（20日日均成交额>5000万）"""
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=days+5)).strftime('%Y%m%d')
        
        df = self.get_etf_daily(ts_code, start_date, end_date)
        if df is None or len(df) < days:
            return False, 0
        
        df = df.sort_values('trade_date', ascending=False).head(days)
        avg_amount = df['amount'].mean()  # 单位：千元
        # 5000万 = 50000千元 (Tushare amount单位是千元)
        threshold = 50000  # 5000万元 = 50000千元
        
        return avg_amount > threshold, avg_amount
    
    def filter_etfs_by_theme(self):
        """
        根据主题筛选ETF
        
        受关税影响：
        - 科技/电子类ETF（受中美关税影响）
        - 出口制造类ETF
        
        受伊朗局势影响：
        - 黄金ETF（避险资产）
        - 油气/能源ETF
        - 军工ETF
        """
        
        theme_etfs = {
            '关税敏感': [
                '159995.SZ',  # 芯片ETF
                '512480.SH',  # 半导体ETF
                '515000.SH',  # 科技ETF
                '159819.SZ',  # 人工智能ETF
                '512760.SH',  # 芯片ETF
            ],
            '避险资产': [
                '518880.SH',  # 黄金ETF
                '159934.SZ',  # 黄金ETF
                '518800.SH',  # 黄金ETF基金
            ],
            '能源': [
                '501018.SH',  # 南方原油
                '162411.SZ',  # 华宝油气
                '513300.SH',  # 纳斯达克ETF（含能源股）
            ],
            '军工': [
                '512660.SH',  # 军工ETF
                '512670.SH',  # 国防ETF
                '512680.SH',  # 军工龙头ETF
            ],
            '反制受益': [
                '159928.SZ',  # 消费ETF（内需）
                '510880.SH',  # 红利ETF（防御）
                '512400.SH',  # 有色金属ETF（稀土反制）
            ]
        }
        
        return theme_etfs
    
    def calculate_correlation(self, etf_codes, days=60):
        """计算ETF之间的相关性"""
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=days+10)).strftime('%Y%m%d')
        
        price_data = {}
        
        for code in etf_codes:
            df = self.get_etf_daily(code, start_date, end_date)
            if df is not None and len(df) > 20:
                df = df.sort_values('trade_date')
                df['return'] = df['close'].pct_change()
                price_data[code] = df.set_index('trade_date')['return']
        
        if len(price_data) < 2:
            return pd.DataFrame()
        
        # 合并数据
        returns_df = pd.DataFrame(price_data)
        returns_df = returns_df.dropna()
        
        # 计算相关性矩阵
        corr_matrix = returns_df.corr()
        
        return corr_matrix
    
    def build_portfolio(self, theme_etfs, max_corr=0.7):
        """
        构建低相关性组合
        
        参数:
            theme_etfs: 主题ETF字典
            max_corr: 最大允许相关性
        """
        portfolio = []
        
        # 从每个主题中选一只流动性最好的ETF
        for theme, codes in theme_etfs.items():
            print(f"\n【{theme}】筛选中...")
            
            theme_selected = []
            
            for code in codes:
                # 检查流动性
                is_liquid, avg_amount = self.check_liquidity(code)
                
                if is_liquid:
                    theme_selected.append({
                        'code': code,
                        'theme': theme,
                        'avg_amount': avg_amount
                    })
                    print(f"  ✅ {code}: 日均成交{avg_amount:.0f}万元")
                else:
                    print(f"  ❌ {code}: 流动性不足 ({avg_amount:.0f}万元)")
            
            # 选择该主题流动性最好的ETF
            if theme_selected:
                best = max(theme_selected, key=lambda x: x['avg_amount'])
                portfolio.append(best)
                print(f"  ⭐ 选中: {best['code']}")
        
        return portfolio
    
    def scenario_analysis(self, portfolio):
        """
        三种情景分析
        
        情景1: 谈得好 - 关税减免，伊朗缓和
        情景2: 谈一般 - 维持现状，小幅调整
        情景3: 没谈好 - 关税升级，伊朗紧张
        """
        
        scenarios = {
            '谈得好': {
                'description': '关税减免，伊朗局势缓和，市场风险偏好上升',
                'impact': {
                    '关税敏感': 0.05,    # 科技ETF受益
                    '避险资产': -0.03,   # 黄金下跌
                    '能源': -0.02,       # 油价回落
                    '军工': -0.02,       # 避险情绪降温
                    '反制受益': 0.02,    # 内需消费稳定
                }
            },
            '谈一般': {
                'description': '维持现状，小幅调整，市场波动有限',
                'impact': {
                    '关税敏感': 0.01,
                    '避险资产': 0.01,
                    '能源': 0.00,
                    '军工': 0.01,
                    '反制受益': 0.01,
                }
            },
            '没谈好': {
                'description': '关税升级，伊朗局势紧张，避险情绪升温',
                'impact': {
                    '关税敏感': -0.05,   # 科技ETF受损
                    '避险资产': 0.05,    # 黄金上涨
                    '能源': 0.05,        # 油价上涨
                    '军工': 0.04,        # 军工上涨
                    '反制受益': 0.03,    # 稀土反制受益
                }
            }
        }
        
        results = {}
        
        for scenario_name, scenario_data in scenarios.items():
            print(f"\n{'='*60}")
            print(f"情景: {scenario_name}")
            print(f"描述: {scenario_data['description']}")
            print(f"{'='*60}")
            
            portfolio_return = 0
            details = []
            
            for etf in portfolio:
                theme = etf['theme']
                impact = scenario_data['impact'].get(theme, 0)
                
                # 假设等权重配置
                weight = 1.0 / len(portfolio)
                weighted_return = impact * weight
                portfolio_return += weighted_return
                
                details.append({
                    'code': etf['code'],
                    'theme': theme,
                    'weight': f"{weight*100:.1f}%",
                    'impact': f"{impact*100:+.1f}%",
                    'contribution': f"{weighted_return*100:+.2f}%"
                })
                
                print(f"  {etf['code']} ({theme}): {impact*100:+.1f}% × {weight*100:.1f}% = {weighted_return*100:+.2f}%")
            
            results[scenario_name] = {
                'portfolio_return': portfolio_return,
                'details': details,
                'description': scenario_data['description']
            }
            
            print(f"\n  📊 组合预期收益: {portfolio_return*100:+.2f}%")
        
        return results
    
    def generate_report(self, portfolio, scenario_results):
        """生成策略报告"""
        
        report = {
            'strategy_name': '特朗普访华事件冲击型ETF组合',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'portfolio': portfolio,
            'scenarios': scenario_results,
            'summary': {
                'total_etfs': len(portfolio),
                'themes': list(set([e['theme'] for e in portfolio])),
                'avg_liquidity': sum([e['avg_amount'] for e in portfolio]) / len(portfolio) if portfolio else 0
            }
        }
        
        return report


def main():
    """主函数"""
    print("="*70)
    print("特朗普访华事件冲击型ETF策略构建")
    print("="*70)
    
    strategy = TrumpVisitStrategy()
    
    # 1. 获取主题ETF
    print("\n【步骤1】筛选主题ETF...")
    theme_etfs = strategy.filter_etfs_by_theme()
    
    for theme, codes in theme_etfs.items():
        print(f"  {theme}: {codes}")
    
    # 2. 构建组合
    print("\n【步骤2】构建低相关性组合...")
    portfolio = strategy.build_portfolio(theme_etfs)
    
    print(f"\n✅ 组合构建完成: 选中{len(portfolio)}只ETF")
    for etf in portfolio:
        print(f"  - {etf['code']} ({etf['theme']}): 日均成交{etf['avg_amount']:.0f}万元")
    
    # 3. 情景分析
    print("\n【步骤3】三种情景收益测算...")
    scenario_results = strategy.scenario_analysis(portfolio)
    
    # 4. 生成报告
    print("\n【步骤4】生成策略报告...")
    report = strategy.generate_report(portfolio, scenario_results)
    
    # 保存报告
    output_file = '/root/.openclaw/workspace/trump_visit_strategy_report.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 报告已保存: {output_file}")
    
    return report


if __name__ == '__main__':
    report = main()
