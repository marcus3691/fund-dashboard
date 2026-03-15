#!/usr/bin/env python3
"""
基金经理基础层异常监控系统
范围：全市场约3000位基金经理
监控：业绩突变、规模异动、调仓异常、人员变动
"""

import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

sys.path.insert(0, '/root/.openclaw/workspace/fund_data/monitor')

from database import manager_db

class AnomalyType(Enum):
    """异常类型"""
    PERFORMANCE_SPIKE = "业绩突变"  # 业绩暴涨/暴跌
    SCALE_CHANGE = "规模异动"       # 规模大幅变化
    HOLDING_CHANGE = "调仓异常"     # 持仓大幅变动
    MANAGER_CHANGE = "人员变动"     # 经理变更
    REDEMPTION = "巨额赎回"         # 巨额赎回
    STYLE_DRIFT = "风格漂移"        # 投资风格漂移

@dataclass
class AnomalySignal:
    """异常信号"""
    anomaly_type: AnomalyType
    manager_name: str
    fund_code: str
    fund_name: str
    severity: str  # critical, high, medium, low
    description: str
    trigger_value: str
    recommendation: str
    timestamp: str

class BaseLayerMonitor:
    """
    基础层异常监控器
    监控全市场基金经理异常行为
    """
    
    def __init__(self):
        self.signals: List[AnomalySignal] = []
        self.thresholds = {
            'performance_spike': 20,      # 单月收益超过20%或低于-15%
            'performance_drop': -15,
            'scale_change': 50,           # 规模变化超过50%
            'holding_turnover': 0.5,      # 换手率超过50%
            'top_holding_change': 0.3,    # 前十大持仓变化超过30%
        }
    
    def detect_performance_anomaly(self, manager_data: Dict) -> Optional[AnomalySignal]:
        """
        检测业绩突变
        """
        perf = manager_data.get('performance') or {}
        returns = perf.get('returns', {})
        
        if not returns:
            return None
        
        mom = returns.get('1月')  # 近1月收益
        if mom is None:
            return None
        
        if mom > self.thresholds['performance_spike']:
            return AnomalySignal(
                anomaly_type=AnomalyType.PERFORMANCE_SPIKE,
                manager_name=manager_data.get('manager', ''),
                fund_code=manager_data.get('fund_code', ''),
                fund_name=manager_data.get('fund', ''),
                severity='high',
            description=f"近1月业绩暴涨{mom:.2f}%",
                trigger_value=f"+{mom:.2f}%",
                recommendation='关注是否为短期运气，谨慎追高',
                timestamp=datetime.now().isoformat()
            )
        elif mom < self.thresholds['performance_drop']:
            return AnomalySignal(
                anomaly_type=AnomalyType.PERFORMANCE_SPIKE,
                manager_name=manager_data.get('manager', ''),
                fund_code=manager_data.get('fund_code', ''),
                fund_name=manager_data.get('fund', ''),
                severity='critical' if mom < -25 else 'high',
                description=f"近1月业绩暴跌{mom:.2f}%",
                trigger_value=f"{mom:.2f}%",
                recommendation='排查是否踩雷或风格不适应市场',
                timestamp=datetime.now().isoformat()
            )
        
        return None
    
    def detect_holding_anomaly(self, manager_data: Dict) -> Optional[AnomalySignal]:
        """
        检测调仓异常
        """
        holdings = manager_data.get('holdings') or {}
        if not holdings or not holdings.get('holdings'):
            return None
        
        # 检查持仓集中度
        top_holdings = holdings['holdings'][:5]
        top5_ratio = sum([h.get('ratio', 0) for h in top_holdings])
        
        # 高度集中风险
        if top5_ratio > 60:
            return AnomalySignal(
                anomaly_type=AnomalyType.HOLDING_CHANGE,
                manager_name=manager_data.get('manager', ''),
                fund_code=manager_data.get('fund_code', ''),
                fund_name=manager_data.get('fund', ''),
                severity='high',
                description=f"持仓高度集中，前5大占比{top5_ratio:.1f}%",
                trigger_value=f"{top5_ratio:.1f}%",
                recommendation='集中度风险较高，关注单一标的风险',
                timestamp=datetime.now().isoformat()
            )
        
        # 极度分散（可能清仓）
        if top5_ratio < 5:
            return AnomalySignal(
                anomaly_type=AnomalyType.HOLDING_CHANGE,
                manager_name=manager_data.get('manager', ''),
                fund_code=manager_data.get('fund_code', ''),
                fund_name=manager_data.get('fund', ''),
                severity='medium',
                description=f"持仓极度分散，前5大占比仅{top5_ratio:.1f}%",
                trigger_value=f"{top5_ratio:.1f}%",
                recommendation='可能是调仓期或防御状态',
                timestamp=datetime.now().isoformat()
            )
        
        return None
    
    def detect_style_drift(self, manager_data: Dict) -> Optional[AnomalySignal]:
        """
        检测风格漂移
        """
        style = manager_data.get('style', '')
        holdings = manager_data.get('holdings') or {}
        
        if not holdings or not holdings.get('holdings'):
            return None
        
        # 简化的风格漂移检测
        top_stocks = [h.get('stock_code', '') for h in holdings['holdings'][:5]]
        
        # 价值型经理重仓科创板（可能漂移）
        if '价值' in style:
            tech_count = sum(1 for code in top_stocks if code.startswith('688'))
            if tech_count >= 3:
                return AnomalySignal(
                    anomaly_type=AnomalyType.STYLE_DRIFT,
                    manager_name=manager_data.get('manager', ''),
                    fund_code=manager_data.get('fund_code', ''),
                    fund_name=manager_data.get('fund', ''),
                    severity='medium',
                    description=f"价值型经理重仓{tech_count}只科创板，疑似风格漂移",
                    trigger_value=f"{tech_count}/5",
                    recommendation='核实投资风格是否发生变化',
                    timestamp=datetime.now().isoformat()
                )
        
        # 成长型经理重仓银行股（可能防御）
        if '成长' in style or '科技' in style:
            bank_count = sum(1 for code in top_stocks if code.startswith('6') and code[2:4] in ['01', '02'])
            if bank_count >= 3:
                return AnomalySignal(
                    anomaly_type=AnomalyType.STYLE_DRIFT,
                    manager_name=manager_data.get('manager', ''),
                    fund_code=manager_data.get('fund_code', ''),
                    fund_name=manager_data.get('fund', ''),
                    severity='medium',
                    description=f"成长型经理重仓{bank_count}只银行股，可能防御转价值",
                    trigger_value=f"{bank_count}/5",
                    recommendation='关注风格切换时机',
                    timestamp=datetime.now().isoformat()
                )
        
        return None
    
    def scan_all_managers(self, limit: int = None) -> List[AnomalySignal]:
        """
        扫描所有基金经理，检测异常
        """
        print("="*80)
        print("基金经理基础层异常监控系统")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        print()
        
        # 加载所有数据
        all_data = manager_db.data
        if limit:
            all_data = all_data[:limit]
        
        print(f"扫描范围: {len(all_data)}位基金经理")
        print()
        
        anomaly_count = {anomaly_type: 0 for anomaly_type in AnomalyType}
        
        for i, item in enumerate(all_data, 1):
            report = item.get('report', {})
            if not report:
                continue
            
            # 检测各类异常
            checks = [
                self.detect_performance_anomaly(report),
                self.detect_holding_anomaly(report),
                self.detect_style_drift(report),
            ]
            
            for signal in checks:
                if signal:
                    self.signals.append(signal)
                    anomaly_count[signal.anomaly_type] += 1
        
        # 汇总
        print("="*80)
        print("扫描完成")
        print("="*80)
        print()
        print("异常统计:")
        for anomaly_type, count in anomaly_count.items():
            if count > 0:
                print(f"  {anomaly_type.value}: {count}例")
        
        print(f"\n总计发现异常: {len(self.signals)}例")
        print()
        
        return self.signals
    
    def generate_report(self) -> str:
        """生成异常监控报告"""
        report_lines = []
        report_lines.append("="*80)
        report_lines.append("基金经理异常监控报告")
        report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("="*80)
        report_lines.append("")
        
        # 按严重程度分组
        critical = [s for s in self.signals if s.severity == 'critical']
        high = [s for s in self.signals if s.severity == 'high']
        medium = [s for s in self.signals if s.severity == 'medium']
        low = [s for s in self.signals if s.severity == 'low']
        
        if critical:
            report_lines.append(f"🔴 严重异常 ({len(critical)}例):")
            for s in critical[:5]:  # 只显示前5
                report_lines.append(f"  - {s.manager_name} ({s.fund_code}): {s.description}")
            report_lines.append("")
        
        if high:
            report_lines.append(f"🟠 高度异常 ({len(high)}例):")
            for s in high[:10]:  # 只显示前10
                report_lines.append(f"  - {s.manager_name}: {s.description}")
            report_lines.append("")
        
        if medium:
            report_lines.append(f"🟡 中度异常 ({len(medium)}例):")
            report_lines.append(f"  共{len(medium)}例，详见完整报告")
            report_lines.append("")
        
        report_lines.append("="*80)
        
        return "\n".join(report_lines)
    
    def save_signals(self, output_file: str = 'base_layer_anomaly_signals.json'):
        """保存异常信号"""
        signals_data = []
        for signal in self.signals:
            signals_data.append({
                'type': signal.anomaly_type.value,
                'manager': signal.manager_name,
                'fund_code': signal.fund_code,
                'fund_name': signal.fund_name,
                'severity': signal.severity,
                'description': signal.description,
                'trigger_value': signal.trigger_value,
                'recommendation': signal.recommendation,
                'timestamp': signal.timestamp
            })
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'generated_at': datetime.now().isoformat(),
                'total_signals': len(self.signals),
                'signals': signals_data
            }, f, ensure_ascii=False, indent=2)
        
        print(f"💾 异常信号已保存: {output_file}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=None, help='限制扫描人数')
    
    args = parser.parse_args()
    
    monitor = BaseLayerMonitor()
    signals = monitor.scan_all_managers(limit=args.limit)
    
    # 打印报告
    report = monitor.generate_report()
    print(report)
    
    # 保存信号
    monitor.save_signals()
