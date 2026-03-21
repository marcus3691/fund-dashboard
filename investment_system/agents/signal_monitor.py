#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SignalMonitor Agent - 信号监控模块
功能：实时监控、告警触发、每日简报生成
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('SignalMonitor')


@dataclass
class Alert:
    """告警数据结构"""
    timestamp: str
    level: str  # 'info', 'warning', 'alert', 'critical'
    category: str  # 'drawdown', 'daily_loss', 'consecutive_loss', 'sector_deviation', 'rebalance'
    message: str
    value: float
    threshold: float
    action: str


class SignalMonitorAgent:
    """信号监控Agent"""
    
    def __init__(self, config):
        self.config = config
        self.thresholds = config.SIGNAL_THRESHOLDS
        self.alert_history = []
    
    def run(self, data: Dict, check_type: str = 'full') -> Dict:
        """
        执行信号监控检查
        
        data: {
            'portfolio_metrics': Dict,  # 组合指标
            'asset_metrics': Dict,      # 各资产指标
            'market_data': Dict,        # 市场数据
            'historical_alerts': List   # 历史告警
        }
        check_type: 'full', 'daily', 'risk_only'
        """
        results = {
            'status': 'success',
            'alerts': [],
            'daily_summary': {},
            'timestamp': datetime.now().isoformat()
        }
        
        portfolio_metrics = data.get('portfolio_metrics', {})
        asset_metrics = data.get('asset_metrics', {})
        
        # 风险监控
        if check_type in ['full', 'risk_only']:
            risk_alerts = self._check_risk_signals(portfolio_metrics)
            results['alerts'].extend(risk_alerts)
        
        # 资产偏离监控
        if check_type in ['full', 'daily']:
            deviation_alerts = self._check_sector_deviation(asset_metrics)
            results['alerts'].extend(deviation_alerts)
        
        # 再平衡提醒
        if check_type in ['full', 'daily']:
            rebalance_alerts = self._check_rebalance_needed(data)
            results['alerts'].extend(rebalance_alerts)
        
        # 生成每日简报
        if check_type in ['full', 'daily']:
            daily_summary = self._generate_daily_summary(data, results['alerts'])
            results['daily_summary'] = daily_summary
        
        # 保存告警历史
        self.alert_history.extend(results['alerts'])
        
        logger.info(f"信号监控完成: {len(results['alerts'])}个告警")
        return results
    
    def _check_risk_signals(self, metrics: Dict) -> List[Alert]:
        """检查风险信号"""
        alerts = []
        
        # 回撤检查
        current_dd = metrics.get('current_drawdown', 0)
        if current_dd <= self.thresholds['max_drawdown_alert']:
            alerts.append(Alert(
                timestamp=datetime.now().isoformat(),
                level='critical',
                category='drawdown',
                message=f'回撤超过10%: {current_dd*100:.2f}%',
                value=current_dd,
                threshold=self.thresholds['max_drawdown_alert'],
                action='立即减仓或启动对冲'
            ))
        elif current_dd <= self.thresholds['max_drawdown_warning']:
            alerts.append(Alert(
                timestamp=datetime.now().isoformat(),
                level='warning',
                category='drawdown',
                message=f'回撤超过5%: {current_dd*100:.2f}%',
                value=current_dd,
                threshold=self.thresholds['max_drawdown_warning'],
                action='密切关注风险'
            ))
        
        # 夏普比率检查
        sharpe = metrics.get('sharpe_ratio', 0)
        if sharpe < -0.5:
            alerts.append(Alert(
                timestamp=datetime.now().isoformat(),
                level='warning',
                category='sharpe',
                message=f'夏普比率过低: {sharpe:.2f}',
                value=sharpe,
                threshold=-0.5,
                action='评估策略有效性'
            ))
        
        # 波动率检查
        vol = metrics.get('annual_volatility', 0)
        if vol > 0.30:  # 年化波动超30%
            alerts.append(Alert(
                timestamp=datetime.now().isoformat(),
                level='warning',
                category='volatility',
                message=f'波动率过高: {vol*100:.1f}%',
                value=vol,
                threshold=0.30,
                action='考虑降低仓位'
            ))
        
        return alerts
    
    def _check_sector_deviation(self, asset_metrics: Dict) -> List[Alert]:
        """检查行业偏离"""
        alerts = []
        
        for code, metrics in asset_metrics.items():
            current_weight = metrics.get('current_weight', 0)
            target_weight = metrics.get('target_weight', 0)
            deviation = abs(current_weight - target_weight)
            
            if deviation > self.thresholds['sector_deviation_limit']:
                alerts.append(Alert(
                    timestamp=datetime.now().isoformat(),
                    level='info',
                    category='sector_deviation',
                    message=f'{code}偏离目标{deviation*100:.1f}%',
                    value=deviation,
                    threshold=self.thresholds['sector_deviation_limit'],
                    action='考虑再平衡'
                ))
        
        return alerts
    
    def _check_rebalance_needed(self, data: Dict) -> List[Alert]:
        """检查是否需要再平衡"""
        alerts = []
        
        current_weights = data.get('current_weights', {})
        target_weights = data.get('target_weights', {})
        last_rebalance = data.get('last_rebalance_date')
        
        # 检查时间（季度再平衡）
        if last_rebalance:
            last_date = datetime.strptime(last_rebalance, '%Y-%m-%d')
            days_since = (datetime.now() - last_date).days
            
            if days_since >= 90:  # 超过90天
                alerts.append(Alert(
                    timestamp=datetime.now().isoformat(),
                    level='info',
                    category='rebalance',
                    message=f'距离上次再平衡已{days_since}天，建议季度调整',
                    value=days_since,
                    threshold=90,
                    action='执行季度再平衡'
                ))
        
        # 检查偏离度
        total_deviation = sum(
            abs(current_weights.get(a, 0) - target_weights.get(a, 0))
            for a in set(current_weights.keys()) | set(target_weights.keys())
        ) / 2  # 除以2是因为买卖双向
        
        if total_deviation > 0.10:  # 总偏离超10%
            alerts.append(Alert(
                timestamp=datetime.now().isoformat(),
                level='warning',
                category='rebalance',
                message=f'组合偏离度达{total_deviation*100:.1f}%，建议再平衡',
                value=total_deviation,
                threshold=0.10,
                action='执行再平衡'
            ))
        
        return alerts
    
    def _generate_daily_summary(self, data: Dict, alerts: List[Alert]) -> Dict:
        """生成每日简报"""
        metrics = data.get('portfolio_metrics', {})
        
        # 按级别统计告警
        alert_summary = {'critical': 0, 'warning': 0, 'info': 0}
        for alert in alerts:
            alert_summary[alert.level] = alert_summary.get(alert.level, 0) + 1
        
        # 组合状态
        current_dd = metrics.get('current_drawdown', 0)
        if current_dd < -0.10:
            status = '🔴 高风险'
        elif current_dd < -0.05:
            status = '🟡 中风险'
        else:
            status = '🟢 正常'
        
        return {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'status': status,
            'daily_return': metrics.get('daily_return', 0),
            'current_drawdown': current_dd,
            'sharpe_ratio': metrics.get('sharpe_ratio', 0),
            'alert_count': len(alerts),
            'alert_summary': alert_summary,
            'key_actions': [a.action for a in alerts if a.level in ['warning', 'critical']][:3]
        }
    
    def run_daily_monitor(self, portfolio_data: Dict, risk_results: Dict) -> Dict:
        """
        每日监控简化接口
        收盘后调用
        """
        # 构造监控数据
        monitor_data = {
            'portfolio_metrics': risk_results.get('metrics', {}),
            'asset_metrics': portfolio_data.get('asset_metrics', {}),
            'current_weights': portfolio_data.get('current_weights', {}),
            'target_weights': portfolio_data.get('target_weights', {}),
            'last_rebalance_date': portfolio_data.get('last_rebalance_date')
        }
        
        return self.run(monitor_data, check_type='daily')
    
    def get_alert_statistics(self, days: int = 30) -> Dict:
        """获取告警统计"""
        cutoff = datetime.now() - timedelta(days=days)
        recent_alerts = [
            a for a in self.alert_history
            if datetime.fromisoformat(a.timestamp) > cutoff
        ]
        
        by_category = {}
        by_level = {}
        
        for alert in recent_alerts:
            by_category[alert.category] = by_category.get(alert.category, 0) + 1
            by_level[alert.level] = by_level.get(alert.level, 0) + 1
        
        return {
            'total_alerts': len(recent_alerts),
            'by_category': by_category,
            'by_level': by_level,
            'most_common': max(by_category.items(), key=lambda x: x[1])[0] if by_category else None
        }


if __name__ == '__main__':
    # 测试
    import sys
    sys.path.append('/root/.openclaw/workspace/investment_system')
    from config.config import *
    
    agent = SignalMonitorAgent(Config())
    
    # 测试数据
    test_data = {
        'portfolio_metrics': {
            'current_drawdown': -0.08,
            'sharpe_ratio': 1.2,
            'annual_volatility': 0.25,
            'daily_return': -0.02
        },
        'asset_metrics': {
            '518880.SH': {'current_weight': 0.18, 'target_weight': 0.15},
            '300394.SZ': {'current_weight': 0.02, 'target_weight': 0.04}
        },
        'current_weights': {'518880.SH': 0.18, '300394.SZ': 0.02},
        'target_weights': {'518880.SH': 0.15, '300394.SZ': 0.04},
        'last_rebalance_date': '2025-12-01'
    }
    
    result = agent.run(test_data)
    print(f"告警数: {len(result['alerts'])}")
    print(f"状态: {result['daily_summary'].get('status')}")
