#!/usr/bin/env python3
"""
基金经理共识信号生成系统
基于239人（核心层50+重点层189）持仓数据生成市场信号
"""

import sys
import json
from datetime import datetime
from typing import Dict, List, Tuple
from collections import defaultdict

sys.path.insert(0, '/root/.openclaw/workspace/fund_data/monitor')

from database import manager_db

class ManagerConsensusSignal:
    """
    基金经理共识信号生成器
    """
    
    def __init__(self):
        self.data = manager_db.data
        self.signals = []
        
    def load_all_managers(self) -> List[Dict]:
        """加载所有基金经理数据"""
        managers = []
        for item in self.data:
            report = item.get('report', {})
            if report and report.get('manager'):
                managers.append(report)
        return managers
    
    def analyze_stock_consensus(self, managers: List[Dict]) -> Dict[str, Dict]:
        """
        分析重仓股共识
        统计被多位基金经理持有的股票
        """
        stock_votes = defaultdict(lambda: {
            'count': 0,
            'managers': [],
            'total_ratio': 0,
            'avg_ratio': 0
        })
        
        for manager in managers:
            holdings = manager.get('holdings', {})
            if holdings and holdings.get('holdings'):
                manager_name = manager.get('manager', 'Unknown')
                for stock in holdings['holdings']:
                    code = stock.get('stock_code', '')
                    ratio = stock.get('ratio', 0)
                    if code and ratio > 0:
                        stock_votes[code]['count'] += 1
                        stock_votes[code]['managers'].append(manager_name)
                        stock_votes[code]['total_ratio'] += ratio
        
        # 计算平均持仓比例
        for code, data in stock_votes.items():
            if data['count'] > 0:
                data['avg_ratio'] = round(data['total_ratio'] / data['count'], 2)
        
        return dict(stock_votes)
    
    def analyze_sector_consensus(self, managers: List[Dict]) -> Dict[str, Dict]:
        """
        分析行业共识
        根据股票代码前缀判断行业
        """
        # 简化的行业映射
        sector_mapping = {
            '000333': '家电', '600276': '医药', '300750': '新能源',
            '603259': '医药', '002475': '电子', '300760': '医药',
            '000858': '白酒', '600519': '白酒', '601318': '金融',
            '601398': '银行', '601668': '建筑', '600900': '电力',
            '300274': '新能源', '300014': '电子', '688111': '半导体',
            '300502': '通信', '300308': '通信', '002371': '半导体',
            '603501': '半导体', '002241': '电子'
        }
        
        sector_votes = defaultdict(lambda: {
            'count': 0,
            'managers': [],
            'stocks': []
        })
        
        for manager in managers:
            holdings = manager.get('holdings', {})
            if holdings and holdings.get('holdings'):
                manager_name = manager.get('manager', '')
                style = manager.get('style', '')
                for stock in holdings['holdings']:
                    code = stock.get('stock_code', '')
                    # 根据风格推断行业
                    sector = self._infer_sector(code, style)
                    if sector:
                        sector_votes[sector]['count'] += 1
                        if manager_name not in sector_votes[sector]['managers']:
                            sector_votes[sector]['managers'].append(manager_name)
                        if code not in sector_votes[sector]['stocks']:
                            sector_votes[sector]['stocks'].append(code)
        
        return dict(sector_votes)
    
    def _infer_sector(self, stock_code: str, style: str) -> str:
        """根据股票代码和风格推断行业"""
        # 根据代码前缀判断
        if stock_code.startswith('300750') or stock_code.startswith('002594') or '新能源' in style:
            return '新能源'
        elif stock_code.startswith('603259') or stock_code.startswith('300760') or '医药' in style or '医疗' in style:
            return '医药'
        elif stock_code.startswith('000333') or stock_code.startswith('000858') or '消费' in style:
            return '消费'
        elif stock_code.startswith('688') or stock_code.startswith('002371') or '半导体' in style or '科技' in style:
            return '科技/半导体'
        elif stock_code.startswith('300502') or stock_code.startswith('300308') or '通信' in style:
            return '通信/AI'
        elif stock_code.startswith('601') or '金融' in style or '银行' in style:
            return '金融'
        elif '周期' in style or '资源' in style:
            return '周期/资源'
        elif '制造' in style:
            return '制造'
        else:
            return '其他'
    
    def analyze_performance_consensus(self, managers: List[Dict]) -> Dict:
        """
        分析业绩共识
        统计基金经理整体业绩表现
        """
        performance_stats = {
            'excellent': [],  # >30%
            'good': [],       # 10-30%
            'average': [],    # 0-10%
            'poor': [],       # <0%
            'unknown': []
        }
        
        total_return = 0
        count_with_data = 0
        
        for manager in managers:
            perf = manager.get('performance') or {}
            returns = perf.get('returns', {})
            yoy = returns.get('1年')
            
            manager_name = manager.get('manager', '')
            
            if yoy is not None:
                count_with_data += 1
                total_return += yoy
                
                if yoy > 30:
                    performance_stats['excellent'].append({'name': manager_name, 'return': yoy})
                elif yoy > 10:
                    performance_stats['good'].append({'name': manager_name, 'return': yoy})
                elif yoy > 0:
                    performance_stats['average'].append({'name': manager_name, 'return': yoy})
                else:
                    performance_stats['poor'].append({'name': manager_name, 'return': yoy})
            else:
                performance_stats['unknown'].append({'name': manager_name, 'return': None})
        
        avg_return = round(total_return / count_with_data, 2) if count_with_data > 0 else 0
        
        return {
            'stats': performance_stats,
            'average_return': avg_return,
            'total_with_data': count_with_data,
            'total_managers': len(managers)
        }
    
    def generate_signals(self) -> List[Dict]:
        """
        生成共识信号
        """
        print("="*80)
        print("基金经理共识信号生成系统")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        print()
        
        # 加载数据
        managers = self.load_all_managers()
        print(f"加载基金经理数据: {len(managers)}人")
        print()
        
        # 1. 重仓股共识分析
        print("【分析1】重仓股共识...")
        stock_consensus = self.analyze_stock_consensus(managers)
        
        # 筛选高共识股票（被3位以上基金经理持有）
        high_consensus_stocks = {
            code: data for code, data in stock_consensus.items() 
            if data['count'] >= 3
        }
        
        # 排序
        sorted_stocks = sorted(
            high_consensus_stocks.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )[:20]  # Top 20
        
        print(f"  发现高共识股票: {len(sorted_stocks)}只（被3+基金经理持有）")
        
        # 生成股票共识信号
        for code, data in sorted_stocks[:10]:  # Top 10生成信号
            signal = {
                'type': 'stock_consensus',
                'priority': 'high' if data['count'] >= 5 else 'medium',
                'code': code,
                'consensus_count': data['count'],
                'avg_holding_ratio': data['avg_ratio'],
                'managers': data['managers'][:5],  # 前5位
                'trigger': f"{data['count']}位基金经理重仓持有",
                'action': '关注相关ETF或个股',
                'generated_at': datetime.now().isoformat()
            }
            self.signals.append(signal)
        
        print()
        
        # 2. 行业共识分析
        print("【分析2】行业共识...")
        sector_consensus = self.analyze_sector_consensus(managers)
        
        sorted_sectors = sorted(
            sector_consensus.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )[:10]
        
        print(f"  发现热门行业: {len(sorted_sectors)}个")
        
        # 生成行业共识信号
        for sector, data in sorted_sectors[:5]:
            signal = {
                'type': 'sector_consensus',
                'priority': 'high' if data['count'] >= 20 else 'medium',
                'sector': sector,
                'consensus_count': data['count'],
                'managers': data['managers'][:5],
                'stocks': data['stocks'][:5],
                'trigger': f"{data['count']}位基金经理布局{sector}",
                'action': f'关注{sector}板块ETF',
                'generated_at': datetime.now().isoformat()
            }
            self.signals.append(signal)
        
        print()
        
        # 3. 业绩共识分析
        print("【分析3】业绩共识...")
        perf_consensus = self.analyze_performance_consensus(managers)
        
        stats = perf_consensus['stats']
        total = perf_consensus['total_with_data']
        
        print(f"  业绩统计（有数据{total}人）:")
        print(f"    优秀(>30%): {len(stats['excellent'])}人 ({len(stats['excellent'])/total*100:.1f}%)")
        print(f"    良好(10-30%): {len(stats['good'])}人 ({len(stats['good'])/total*100:.1f}%)")
        print(f"    一般(0-10%): {len(stats['average'])}人 ({len(stats['average'])/total*100:.1f}%)")
        print(f"    调整(<0%): {len(stats['poor'])}人 ({len(stats['poor'])/total*100:.1f}%)")
        print(f"    平均收益: {perf_consensus['average_return']}%")
        
        # 生成业绩共识信号
        if len(stats['excellent']) > len(stats['poor']):
            signal = {
                'type': 'performance_consensus',
                'priority': 'high',
                'sentiment': 'positive',
                'trigger': f"优秀基金经理占比高({len(stats['excellent'])}/{total})",
                'action': '市场情绪积极，可增加权益仓位',
                'avg_return': perf_consensus['average_return'],
                'generated_at': datetime.now().isoformat()
            }
        elif len(stats['poor']) > len(stats['excellent']):
            signal = {
                'type': 'performance_consensus',
                'priority': 'high',
                'sentiment': 'negative',
                'trigger': f"业绩调整基金经理占比高({len(stats['poor'])}/{total})",
                'action': '市场情绪谨慎，控制仓位风险',
                'avg_return': perf_consensus['average_return'],
                'generated_at': datetime.now().isoformat()
            }
        else:
            signal = {
                'type': 'performance_consensus',
                'priority': 'medium',
                'sentiment': 'neutral',
                'trigger': "基金经理业绩分化",
                'action': '保持均衡配置，精选个股',
                'avg_return': perf_consensus['average_return'],
                'generated_at': datetime.now().isoformat()
            }
        
        self.signals.append(signal)
        
        print()
        print("="*80)
        print(f"✅ 信号生成完成: {len(self.signals)}个")
        print("="*80)
        
        return self.signals
    
    def save_signals(self, output_file: str = 'manager_consensus_signals.json'):
        """保存信号到文件"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'generated_at': datetime.now().isoformat(),
                'total_managers': len(self.load_all_managers()),
                'signals': self.signals
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 信号已保存: {output_file}")
    
    def print_signals(self):
        """打印信号详情"""
        print("\n" + "="*80)
        print("信号详情")
        print("="*80)
        
        for i, signal in enumerate(self.signals, 1):
            print(f"\n【信号{i}】{signal['type']}")
            print(f"  优先级: {signal['priority']}")
            print(f"  触发条件: {signal['trigger']}")
            print(f"  建议操作: {signal['action']}")
            
            if signal['type'] == 'stock_consensus':
                print(f"  股票代码: {signal['code']}")
                print(f"  共识人数: {signal['consensus_count']}")
                print(f"  平均持仓: {signal['avg_holding_ratio']}%")
            elif signal['type'] == 'sector_consensus':
                print(f"  行业: {signal['sector']}")
                print(f"  共识人数: {signal['consensus_count']}")
            elif signal['type'] == 'performance_consensus':
                print(f"  市场情绪: {signal['sentiment']}")
                print(f"  平均收益: {signal['avg_return']}%")

if __name__ == "__main__":
    generator = ManagerConsensusSignal()
    signals = generator.generate_signals()
    generator.print_signals()
    generator.save_signals()
