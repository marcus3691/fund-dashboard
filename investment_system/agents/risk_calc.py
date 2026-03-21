#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RiskCalc Agent - 风险测算模块
功能：回撤分析、VaR计算、压力测试、信号监控
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('RiskCalc')


@dataclass
class RiskMetrics:
    """风险指标数据结构"""
    max_drawdown: float
    current_drawdown: float
    max_dd_date: str
    annual_volatility: float
    sharpe_ratio: float
    calmar_ratio: float
    var_95: float
    cvar_95: float
    win_rate: float
    profit_loss_ratio: float
    consecutive_loss_days: int
    status: str  # 'normal', 'warning', 'alert'


class RiskCalcAgent:
    """风险测算Agent"""
    
    def __init__(self, config):
        self.config = config
        self.thresholds = config.SIGNAL_THRESHOLDS
    
    def run(self, data: Dict, tests: List[str] = None) -> Dict:
        """
        执行风险测算
        
        data: {
            'returns': pd.Series,  # 日收益率序列
            'nav': pd.Series,      # 净值序列
            'dates': pd.Series     # 日期序列
        }
        tests: ['drawdown', 'var', 'risk_metrics', 'signals']
        """
        if tests is None:
            tests = ['drawdown', 'var', 'risk_metrics', 'signals']
        
        returns = pd.Series(data.get('returns', []))
        nav = pd.Series(data.get('nav', []))
        dates = data.get('dates', [])
        
        results = {
            'status': 'success',
            'metrics': {},
            'signals': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # 基础指标计算
        metrics = self._calculate_metrics(returns, nav, dates)
        results['metrics'] = metrics
        
        # 信号检测
        if 'signals' in tests:
            signals = self._detect_signals(metrics, returns)
            results['signals'] = signals
        
        # 回撤分析
        if 'drawdown' in tests and len(nav) > 0:
            drawdown_analysis = self._analyze_drawdown(nav, dates)
            results['drawdown_analysis'] = drawdown_analysis
        
        # VaR分析
        if 'var' in tests and len(returns) > 0:
            var_analysis = self._calculate_var(returns)
            results['var_analysis'] = var_analysis
        
        logger.info(f"风险测算完成: {len(results['signals'])}个信号")
        return results
    
    def _calculate_metrics(self, returns: pd.Series, nav: pd.Series, dates: List) -> Dict:
        """计算风险指标"""
        if len(returns) == 0:
            return {}
        
        # 基础统计
        total_return = (nav.iloc[-1] / nav.iloc[0] - 1) if len(nav) > 0 else 0
        annual_vol = returns.std() * np.sqrt(self.config.PORTFOLIO_OPTIMIZATION['trading_days'])
        
        # 回撤
        if len(nav) > 0:
            rolling_max = nav.cummax()
            drawdown = (nav - rolling_max) / rolling_max
            max_dd = drawdown.min()
            max_dd_idx = drawdown.idxmin()
            max_dd_date = dates[max_dd_idx] if len(dates) > max_dd_idx else ''
            current_dd = drawdown.iloc[-1]
        else:
            max_dd = 0
            max_dd_date = ''
            current_dd = 0
        
        # 夏普和卡玛
        risk_free = self.config.PORTFOLIO_OPTIMIZATION['risk_free_rate']
        sharpe = (returns.mean() * self.config.PORTFOLIO_OPTIMIZATION['trading_days'] - risk_free) / annual_vol if annual_vol > 0 else 0
        calmar = (returns.mean() * self.config.PORTFOLIO_OPTIMIZATION['trading_days']) / abs(max_dd) if max_dd != 0 else 0
        
        # VaR
        var_95 = np.percentile(returns, 5) if len(returns) > 0 else 0
        cvar_95 = returns[returns <= var_95].mean() if len(returns) > 0 else 0
        
        # 胜率和盈亏比
        win_rate = (returns > 0).sum() / len(returns) if len(returns) > 0 else 0
        wins = returns[returns > 0]
        losses = returns[returns < 0]
        pl_ratio = wins.mean() / abs(losses.mean()) if len(losses) > 0 and losses.mean() != 0 else 1
        
        # 连续亏损天数
        consecutive_loss = self._count_consecutive_losses(returns)
        
        return {
            'total_return': total_return,
            'annual_volatility': annual_vol,
            'max_drawdown': max_dd,
            'current_drawdown': current_dd,
            'max_dd_date': max_dd_date,
            'sharpe_ratio': sharpe,
            'calmar_ratio': calmar,
            'var_95': var_95,
            'cvar_95': cvar_95,
            'win_rate': win_rate,
            'profit_loss_ratio': pl_ratio,
            'consecutive_loss_days': consecutive_loss,
            'max_daily_gain': returns.max() if len(returns) > 0 else 0,
            'max_daily_loss': returns.min() if len(returns) > 0 else 0,
        }
    
    def _analyze_drawdown(self, nav: pd.Series, dates: List) -> Dict:
        """详细回撤分析"""
        rolling_max = nav.cummax()
        drawdown = (nav - rolling_max) / rolling_max
        
        # 找出所有回撤期
        dd_periods = []
        in_dd = False
        start_idx = 0
        
        for i, dd in enumerate(drawdown):
            if dd < 0 and not in_dd:
                in_dd = True
                start_idx = i
            elif dd >= -0.001 and in_dd:  # 恢复到-0.1%以内算结束
                in_dd = False
                if i > start_idx:
                    dd_slice = drawdown.iloc[start_idx:i]
                    max_dd_idx_in_slice = dd_slice.idxmin()
                    max_dd_idx = max_dd_idx_in_slice + start_idx
                    
                    dd_periods.append({
                        'start_date': dates[start_idx] if len(dates) > start_idx else '',
                        'end_date': dates[i] if len(dates) > i else '',
                        'duration': i - start_idx,
                        'max_dd': dd_slice.min(),
                        'max_dd_date': dates[max_dd_idx] if len(dates) > max_dd_idx else ''
                    })
        
        # 如果当前还在回撤中
        if in_dd:
            dd_slice = drawdown.iloc[start_idx:]
            max_dd_idx_in_slice = dd_slice.idxmin()
            max_dd_idx = max_dd_idx_in_slice + start_idx
            
            dd_periods.append({
                'start_date': dates[start_idx] if len(dates) > start_idx else '',
                'end_date': 'ongoing',
                'duration': len(drawdown) - start_idx,
                'max_dd': dd_slice.min(),
                'max_dd_date': dates[max_dd_idx] if len(dates) > max_dd_idx else ''
            })
        
        # 当前回撤状态
        current_dd = drawdown.iloc[-1]
        
        return {
            'drawdown_series': drawdown.tolist(),
            'dd_periods': dd_periods,
            'current_dd': current_dd,
            'dd_count': len(dd_periods),
            'avg_dd_duration': np.mean([p['duration'] for p in dd_periods]) if dd_periods else 0
        }
    
    def _calculate_var(self, returns: pd.Series, confidence: float = 0.95) -> Dict:
        """计算VaR和CVaR"""
        alpha = 1 - confidence
        
        # 历史模拟法
        var_hist = np.percentile(returns, alpha * 100)
        
        # 参数法（正态近似）
        mu = returns.mean()
        sigma = returns.std()
        var_param = mu - 1.645 * sigma  # 95%置信度
        
        # CVaR
        cvar = returns[returns <= var_hist].mean()
        
        # 不同时间尺度
        var_by_horizon = {}
        for days in [1, 5, 10, 21]:
            var_by_horizon[f'{days}d'] = {
                'historical': var_hist * np.sqrt(days),
                'parametric': var_param * np.sqrt(days)
            }
        
        return {
            'confidence_level': confidence,
            'daily_var': {'historical': var_hist, 'parametric': var_param},
            'daily_cvar': cvar,
            'var_by_horizon': var_by_horizon
        }
    
    def _detect_signals(self, metrics: Dict, returns: pd.Series) -> List[Dict]:
        """检测风险信号"""
        signals = []
        
        # 回撤告警
        current_dd = metrics.get('current_drawdown', 0)
        if current_dd <= self.thresholds['max_drawdown_alert']:
            signals.append({
                'type': 'alert',
                'category': 'drawdown',
                'message': f'回撤超过10%: {current_dd*100:.2f}%',
                'value': current_dd,
                'threshold': self.thresholds['max_drawdown_alert'],
                'action': '建议减仓或对冲'
            })
        elif current_dd <= self.thresholds['max_drawdown_warning']:
            signals.append({
                'type': 'warning',
                'category': 'drawdown',
                'message': f'回撤超过5%: {current_dd*100:.2f}%',
                'value': current_dd,
                'threshold': self.thresholds['max_drawdown_warning'],
                'action': '关注风险'
            })
        
        # 单日大跌告警
        if len(returns) > 0 and returns.iloc[-1] <= self.thresholds['daily_loss_limit']:
            signals.append({
                'type': 'alert',
                'category': 'daily_loss',
                'message': f'单日跌幅超过3%: {returns.iloc[-1]*100:.2f}%',
                'value': returns.iloc[-1],
                'threshold': self.thresholds['daily_loss_limit'],
                'action': '检查市场消息'
            })
        
        # 连续亏损告警
        consecutive = metrics.get('consecutive_loss_days', 0)
        if consecutive >= self.thresholds['consecutive_loss_days']:
            signals.append({
                'type': 'warning',
                'category': 'consecutive_loss',
                'message': f'连续{consecutive}天亏损',
                'value': consecutive,
                'threshold': self.thresholds['consecutive_loss_days'],
                'action': '检查策略有效性'
            })
        
        # 夏普比率预警
        sharpe = metrics.get('sharpe_ratio', 0)
        if sharpe < 0:
            signals.append({
                'type': 'warning',
                'category': 'sharpe',
                'message': f'夏普比率为负: {sharpe:.2f}',
                'value': sharpe,
                'threshold': 0,
                'action': '评估风险调整后收益'
            })
        
        return signals
    
    def _count_consecutive_losses(self, returns: pd.Series) -> int:
        """计算当前连续亏损天数"""
        if len(returns) == 0:
            return 0
        
        count = 0
        for ret in reversed(returns):
            if ret < 0:
                count += 1
            else:
                break
        return count
    
    def run_daily_check(self, portfolio_data: Dict) -> Dict:
        """每日收盘检查（简化接口）"""
        returns = portfolio_data.get('returns', pd.Series())
        nav = portfolio_data.get('nav', pd.Series())
        dates = portfolio_data.get('dates', [])
        
        return self.run({
            'returns': returns,
            'nav': nav,
            'dates': dates
        }, tests=['risk_metrics', 'signals'])


if __name__ == '__main__':
    # 测试
    import sys
    sys.path.append('/root/.openclaw/workspace/investment_system')
    from config.config import *
    
    agent = RiskCalcAgent(Config())
    
    # 测试数据
    np.random.seed(42)
    test_returns = pd.Series(np.random.normal(0.001, 0.02, 50))
    test_nav = (1 + test_returns).cumprod()
    test_dates = [f'2026-03-{i:02d}' for i in range(1, 51)]
    
    result = agent.run({
        'returns': test_returns,
        'nav': test_nav,
        'dates': test_dates
    })
    
    print(f"指标数: {len(result['metrics'])}")
    print(f"信号数: {len(result['signals'])}")
