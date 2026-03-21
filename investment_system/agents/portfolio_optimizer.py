#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Portfolio Agent - 资产配置优化模块
功能：风险平价、目标波动率、组合优化、再平衡建议
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Portfolio')


@dataclass
class OptimizationResult:
    """优化结果"""
    method: str
    weights: Dict[str, float]
    expected_return: float
    expected_risk: float
    sharpe_ratio: float
    risk_contributions: Optional[Dict] = None


class PortfolioAgent:
    """资产配置Agent"""
    
    def __init__(self, config):
        self.config = config
        self.opt_config = config.PORTFOLIO_OPTIMIZATION
        self.risk_free_rate = self.opt_config['risk_free_rate']
    
    def run(self, data: Dict, method: str = 'risk_parity') -> Dict:
        """
        执行资产配置优化
        
        data: {
            'returns': pd.DataFrame,  # 资产收益率矩阵
            'current_weights': Dict,  # 当前权重
            'constraints': Dict       # 约束条件
        }
        method: 'risk_parity', 'equal_weight', 'min_variance', 'target_risk'
        """
        returns = data.get('returns')
        current_weights = data.get('current_weights', {})
        
        results = {
            'status': 'success',
            'method': method,
            'optimization': {},
            'rebalance': {},
            'timestamp': pd.Timestamp.now().isoformat()
        }
        
        if returns is None or len(returns) == 0:
            return {'status': 'error', 'message': 'No returns data'}
        
        # 执行优化
        if method == 'risk_parity':
            opt_result = self._risk_parity_optimization(returns)
        elif method == 'equal_weight':
            opt_result = self._equal_weight_optimization(returns)
        elif method == 'min_variance':
            opt_result = self._min_variance_optimization(returns)
        elif method == 'target_risk':
            target = data.get('constraints', {}).get('target_risk', 0.15)
            opt_result = self._target_risk_optimization(returns, target)
        else:
            return {'status': 'error', 'message': f'Unknown method: {method}'}
        
        results['optimization'] = opt_result
        
        # 计算再平衡建议
        if current_weights:
            rebalance = self._calculate_rebalance(current_weights, opt_result.weights)
            results['rebalance'] = rebalance
        
        logger.info(f"资产配置优化完成: {method}")
        return results
    
    def _risk_parity_optimization(self, returns: pd.DataFrame) -> OptimizationResult:
        """
        风险平价优化
        目标：使各资产对组合风险的贡献相等
        """
        # 计算协方差矩阵
        cov_matrix = returns.cov() * self.opt_config['trading_days']
        assets = returns.columns.tolist()
        n = len(assets)
        
        # 迭代求解风险平价权重
        weights = np.array([1.0 / n] * n)
        
        for _ in range(100):  # 迭代100次
            # 计算组合风险
            port_var = weights @ cov_matrix.values @ weights
            
            # 计算边际风险贡献
            marginal_contrib = cov_matrix.values @ weights
            
            # 计算风险贡献
            risk_contrib = weights * marginal_contrib / np.sqrt(port_var)
            
            # 更新权重（使风险贡献相等）
            new_weights = risk_contrib / risk_contrib.sum()
            
            # 检查收敛
            if np.max(np.abs(new_weights - weights)) < 1e-6:
                break
            
            weights = new_weights
        
        # 归一化
        weights = weights / weights.sum()
        
        # 计算结果指标
        weights_dict = dict(zip(assets, weights.round(4)))
        expected_return = (returns.mean() * weights).sum() * self.opt_config['trading_days']
        expected_risk = np.sqrt(weights @ cov_matrix.values @ weights)
        sharpe = (expected_return - self.risk_free_rate) / expected_risk if expected_risk > 0 else 0
        
        # 风险贡献占比
        port_var_final = weights @ cov_matrix.values @ weights
        marginal_final = cov_matrix.values @ weights
        risk_contrib_final = weights * marginal_final / np.sqrt(port_var_final)
        risk_contrib_pct = risk_contrib_final / risk_contrib_final.sum()
        
        return OptimizationResult(
            method='Risk Parity',
            weights=weights_dict,
            expected_return=expected_return,
            expected_risk=expected_risk,
            sharpe_ratio=sharpe,
            risk_contributions=dict(zip(assets, risk_contrib_pct.round(4)))
        )
    
    def _equal_weight_optimization(self, returns: pd.DataFrame) -> OptimizationResult:
        """等权重配置"""
        assets = returns.columns.tolist()
        n = len(assets)
        weights = {asset: 1.0 / n for asset in assets}
        
        cov_matrix = returns.cov() * self.opt_config['trading_days']
        w = np.array([1.0 / n] * n)
        
        expected_return = (returns.mean() * w).sum() * self.opt_config['trading_days']
        expected_risk = np.sqrt(w @ cov_matrix.values @ w)
        sharpe = (expected_return - self.risk_free_rate) / expected_risk if expected_risk > 0 else 0
        
        return OptimizationResult(
            method='Equal Weight',
            weights=weights,
            expected_return=expected_return,
            expected_risk=expected_risk,
            sharpe_ratio=sharpe
        )
    
    def _min_variance_optimization(self, returns: pd.DataFrame) -> OptimizationResult:
        """最小方差优化（简化版）"""
        # 使用波动率倒数加权作为近似
        vols = returns.std() * np.sqrt(self.opt_config['trading_days'])
        inv_vols = 1.0 / vols
        weights = inv_vols / inv_vols.sum()
        
        assets = returns.columns.tolist()
        weights_dict = dict(zip(assets, weights.round(4)))
        
        cov_matrix = returns.cov() * self.opt_config['trading_days']
        expected_return = (returns.mean() * weights).sum() * self.opt_config['trading_days']
        expected_risk = np.sqrt(weights.values @ cov_matrix.values @ weights.values)
        sharpe = (expected_return - self.risk_free_rate) / expected_risk if expected_risk > 0 else 0
        
        return OptimizationResult(
            method='Min Variance',
            weights=weights_dict,
            expected_return=expected_return,
            expected_risk=expected_risk,
            sharpe_ratio=sharpe
        )
    
    def _target_risk_optimization(self, returns: pd.DataFrame, target_risk: float) -> OptimizationResult:
        """
        目标风险优化
        在目标风险水平下最大化收益
        """
        # 先用风险平价得到基础权重
        base_result = self._risk_parity_optimization(returns)
        base_weights = np.array(list(base_result.weights.values()))
        base_risk = base_result.expected_risk
        
        # 缩放权重以达到目标风险（风险与权重线性相关近似）
        if base_risk > 0:
            scale = target_risk / base_risk
            # 限制缩放范围，避免过度集中
            scale = min(max(scale, 0.5), 2.0)
        else:
            scale = 1.0
        
        # 调整权重并归一化
        adjusted_weights = base_weights * scale
        # 剩余权重分配给现金
        cash_weight = 1.0 - adjusted_weights.sum()
        
        # 归一化
        if cash_weight < 0:
            adjusted_weights = adjusted_weights / adjusted_weights.sum()
            cash_weight = 0
        
        assets = list(base_result.weights.keys())
        weights_dict = dict(zip(assets, adjusted_weights.round(4)))
        if cash_weight > 0:
            weights_dict['CASH'] = round(cash_weight, 4)
        
        # 重新计算风险
        cov_matrix = returns.cov() * self.opt_config['trading_days']
        expected_return = (returns.mean() * adjusted_weights).sum() * self.opt_config['trading_days']
        expected_risk = np.sqrt(adjusted_weights @ cov_matrix.values @ adjusted_weights)
        sharpe = (expected_return - self.risk_free_rate) / expected_risk if expected_risk > 0 else 0
        
        return OptimizationResult(
            method=f'Target Risk ({target_risk*100:.0f}%)',
            weights=weights_dict,
            expected_return=expected_return,
            expected_risk=expected_risk,
            sharpe_ratio=sharpe
        )
    
    def _calculate_rebalance(self, current: Dict, target: Dict) -> Dict:
        """计算再平衡建议"""
        all_assets = set(current.keys()) | set(target.keys())
        
        trades = []
        total_deviation = 0
        
        for asset in all_assets:
            curr_w = current.get(asset, 0)
            target_w = target.get(asset, 0)
            deviation = target_w - curr_w
            
            if abs(deviation) > 0.001:  # 0.1%以上才调整
                trades.append({
                    'asset': asset,
                    'current': curr_w,
                    'target': target_w,
                    'deviation': deviation,
                    'action': 'BUY' if deviation > 0 else 'SELL'
                })
                total_deviation += abs(deviation)
        
        return {
            'trades': trades,
            'trade_count': len(trades),
            'total_deviation': total_deviation,
            'rebalance_cost_estimate': total_deviation * 0.001  # 假设0.1%交易成本
        }
    
    def check_rebalance_needed(self, current_weights: Dict, target_weights: Dict, threshold: float = 0.05) -> bool:
        """检查是否需要再平衡"""
        for asset in set(current_weights.keys()) | set(target_weights.keys()):
            curr = current_weights.get(asset, 0)
            target = target_weights.get(asset, 0)
            if abs(curr - target) > threshold:
                return True
        return False


if __name__ == '__main__':
    # 测试
    import sys
    sys.path.append('/root/.openclaw/workspace/investment_system')
    from config.config import *
    
    agent = PortfolioAgent(Config())
    
    # 测试数据
    np.random.seed(42)
    test_returns = pd.DataFrame({
        'A': np.random.normal(0.001, 0.02, 100),
        'B': np.random.normal(0.0005, 0.015, 100),
        'C': np.random.normal(0.0008, 0.025, 100)
    })
    
    result = agent.run({
        'returns': test_returns,
        'current_weights': {'A': 0.4, 'B': 0.4, 'C': 0.2}
    }, method='risk_parity')
    
    print(f"方法: {result['optimization'].method}")
    print(f"权重: {result['optimization'].weights}")
    print(f"夏普: {result['optimization'].sharpe_ratio:.2f}")
