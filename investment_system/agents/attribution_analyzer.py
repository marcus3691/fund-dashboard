#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Attribution Agent - 业绩归因模块
功能：Brison归因、行业归因、个股替代效应分析
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Attribution')


@dataclass
class BrisonResult:
    """Brison归因结果"""
    total_return: float
    benchmark_return: float
    excess_return: float
    allocation_effect: float
    selection_effect: float
    interaction_effect: float
    sector_contributions: Dict


class AttributionAgent:
    """业绩归因Agent"""
    
    def __init__(self, config):
        self.config = config
    
    def run(self, data: Dict, method: str = 'brison') -> Dict:
        """
        执行业绩归因分析
        
        data: {
            'portfolio': {
                'codes': [],
                'weights': {},
                'returns': {}
            },
            'benchmark': {
                'codes': [],
                'weights': {},
                'returns': {}
            }
        }
        method: 'brison', 'sector', 'factor'
        """
        results = {
            'status': 'success',
            'method': method,
            'attribution': {},
            'timestamp': pd.Timestamp.now().isoformat()
        }
        
        if method == 'brison':
            brison_result = self._brison_attribution(data)
            results['attribution'] = brison_result
        elif method == 'sector':
            sector_result = self._sector_attribution(data)
            results['attribution'] = sector_result
        elif method == 'substitution':
            # 个股替代效应分析
            sub_result = self._substitution_analysis(data)
            results['attribution'] = sub_result
        
        logger.info(f"归因分析完成: {method}")
        return results
    
    def _brison_attribution(self, data: Dict) -> Dict:
        """
        Brison归因模型
        计算配置效应、选股效应、交互效应
        """
        portfolio = data.get('portfolio', {})
        benchmark = data.get('benchmark', {})
        
        port_weights = portfolio.get('weights', {})
        port_returns = portfolio.get('returns', {})
        bench_weights = benchmark.get('weights', {})
        bench_returns = benchmark.get('returns', {})
        
        # 获取所有资产代码
        all_codes = set(port_weights.keys()) | set(bench_weights.keys())
        
        # 计算组合和基准收益
        port_total = sum(port_weights.get(c, 0) * port_returns.get(c, 0) for c in all_codes)
        bench_total = sum(bench_weights.get(c, 0) * bench_returns.get(c, 0) for c in all_codes)
        
        # Brison分解
        allocation_effect = 0
        selection_effect = 0
        interaction_effect = 0
        
        for code in all_codes:
            wp = port_weights.get(code, 0)
            wb = bench_weights.get(code, 0)
            rp = port_returns.get(code, 0)
            rb = bench_returns.get(code, 0)
            
            # 配置效应: (Wp - Wb) * Rb
            allocation_effect += (wp - wb) * rb
            
            # 选股效应: Wb * (Rp - Rb)
            selection_effect += wb * (rp - rb)
            
            # 交互效应: (Wp - Wb) * (Rp - Rb)
            interaction_effect += (wp - wb) * (rp - rb)
        
        return {
            'portfolio_return': port_total,
            'benchmark_return': bench_total,
            'excess_return': port_total - bench_total,
            'allocation_effect': allocation_effect,
            'selection_effect': selection_effect,
            'interaction_effect': interaction_effect,
            'allocation_pct': allocation_effect / (port_total - bench_total) if (port_total - bench_total) != 0 else 0,
            'selection_pct': selection_effect / (port_total - bench_total) if (port_total - bench_total) != 0 else 0,
        }
    
    def _sector_attribution(self, data: Dict) -> Dict:
        """行业归因分析"""
        portfolio = data.get('portfolio', {})
        benchmark = data.get('benchmark', {})
        
        port_weights = portfolio.get('weights', {})
        port_returns = portfolio.get('returns', {})
        
        # 按行业分组
        sector_mapping = self._get_sector_mapping()
        
        sector_results = {}
        for sector, codes in sector_mapping.items():
            # 组合中该行业的权重和收益贡献
            port_sector_weight = sum(port_weights.get(c, 0) for c in codes)
            port_sector_contrib = sum(
                port_weights.get(c, 0) * port_returns.get(c, 0) 
                for c in codes
            )
            
            sector_results[sector] = {
                'portfolio_weight': port_sector_weight,
                'portfolio_contribution': port_sector_contrib,
                'codes': codes
            }
        
        return {
            'sector_breakdown': sector_results,
            'top_contributors': sorted(
                sector_results.items(), 
                key=lambda x: x[1]['portfolio_contribution'], 
                reverse=True
            )[:3],
            'bottom_contributors': sorted(
                sector_results.items(), 
                key=lambda x: x[1]['portfolio_contribution']
            )[:3]
        }
    
    def _substitution_analysis(self, data: Dict) -> Dict:
        """
        个股替代效应分析
        比较ETF方案和个股方案的差异
        """
        substitution_cases = data.get('substitutions', [])
        
        results = []
        for case in substitution_cases:
            etf_code = case.get('etf_code')
            etf_return = case.get('etf_return')
            etf_weight = case.get('etf_weight')
            
            stock_codes = case.get('stock_codes', [])
            stock_weights = case.get('stock_weights', [])
            stock_returns = case.get('stock_returns', [])
            
            # 计算个股组合收益
            stock_portfolio_return = sum(
                w * r for w, r in zip(stock_weights, stock_returns)
            ) / sum(stock_weights) if sum(stock_weights) > 0 else 0
            
            # 替代效应
            substitution_effect = stock_portfolio_return - etf_return
            portfolio_impact = substitution_effect * etf_weight
            
            results.append({
                'etf_code': etf_code,
                'etf_return': etf_return,
                'stock_portfolio_return': stock_portfolio_return,
                'substitution_effect': substitution_effect,
                'portfolio_impact': portfolio_impact,
                'stocks': list(zip(stock_codes, stock_weights, stock_returns))
            })
        
        # 汇总
        total_impact = sum(r['portfolio_impact'] for r in results)
        
        return {
            'substitutions': results,
            'total_substitution_impact': total_impact,
            'best_substitution': max(results, key=lambda x: x['substitution_effect']) if results else None,
            'worst_substitution': min(results, key=lambda x: x['substitution_effect']) if results else None
        }
    
    def _get_sector_mapping(self) -> Dict:
        """获取行业映射"""
        return {
            '黄金': ['518880.SH', '159562.SZ'],
            '科技': ['300394.SZ', '688195.SH', '512480.SH', '159819.SZ'],
            '电力': ['159326.SZ', '159611.SZ'],
            '军工': ['512710.SH'],
            '港股': ['513130.SH', '513120.SH'],
        }
    
    def generate_report_section(self, attribution_data: Dict) -> str:
        """生成归因分析的Markdown报告段落"""
        if 'brison' in attribution_data.get('method', ''):
            attr = attribution_data.get('attribution', {})
            
            report = f"""### Brison归因分析

| 归因项 | 贡献 | 占比 |
|:---|:---:|:---:|
| 配置效应 | {attr.get('allocation_effect', 0)*100:+.2f}% | {attr.get('allocation_pct', 0)*100:.1f}% |
| 选股效应 | {attr.get('selection_effect', 0)*100:+.2f}% | {attr.get('selection_pct', 0)*100:.1f}% |
| 交互效应 | {attr.get('interaction_effect', 0)*100:+.2f}% | - |
| **总超额收益** | {attr.get('excess_return', 0)*100:+.2f}% | 100% |

**解读**: 
- 配置效应: 行业/资产配置决策的贡献
- 选股效应: 行业内个股选择的贡献
"""
            return report
        
        elif 'substitution' in attribution_data.get('method', ''):
            attr = attribution_data.get('attribution', {})
            
            report = f"""### 个股替代效应分析

| 替代方案 | ETF收益 | 个股组合收益 | 替代效应 | 组合影响 |
|:---|:---:|:---:|:---:|:---:|
"""
            for sub in attr.get('substitutions', []):
                report += f"| {sub['etf_code']} | {sub['etf_return']*100:.2f}% | {sub['stock_portfolio_return']*100:.2f}% | {sub['substitution_effect']*100:+.2f}% | {sub['portfolio_impact']*100:+.2f}% |\n"
            
            report += f"\n**总替代效应**: {attr.get('total_substitution_impact', 0)*100:+.2f}%\n"
            return report
        
        return ""


if __name__ == '__main__':
    # 测试
    import sys
    sys.path.append('/root/.openclaw/workspace/investment_system')
    from config.config import *
    
    agent = AttributionAgent(Config())
    
    # 测试Brison归因
    test_data = {
        'portfolio': {
            'weights': {'A': 0.5, 'B': 0.5},
            'returns': {'A': 0.1, 'B': 0.05}
        },
        'benchmark': {
            'weights': {'A': 0.4, 'B': 0.6},
            'returns': {'A': 0.08, 'B': 0.06}
        }
    }
    
    result = agent.run(test_data, method='brison')
    print(f"超额收益: {result['attribution'].get('excess_return', 0)*100:.2f}%")
