#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reporter Agent - 报告生成模块
功能：Markdown报告、每日简报、报告归档
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Reporter')


class ReporterAgent:
    """报告生成Agent"""
    
    def __init__(self, config):
        self.config = config
        self.reports_dir = config.REPORTS_DIR
        os.makedirs(self.reports_dir, exist_ok=True)
    
    def run(self, data: Dict, report_type: str = 'full') -> Dict:
        """
        生成报告
        
        data: {
            'portfolio_data': Dict,
            'risk_results': Dict,
            'attribution_results': Dict,
            'optimization_results': Dict,
            'monitor_results': Dict
        }
        report_type: 'full', 'daily', 'risk', 'attribution'
        """
        results = {
            'status': 'success',
            'files': [],
            'timestamp': datetime.now().isoformat()
        }
        
        if report_type == 'full':
            report = self._generate_full_report(data)
        elif report_type == 'daily':
            report = self._generate_daily_report(data)
        elif report_type == 'risk':
            report = self._generate_risk_report(data)
        elif report_type == 'attribution':
            report = self._generate_attribution_report(data)
        else:
            return {'status': 'error', 'message': f'Unknown report type: {report_type}'}
        
        # 保存报告
        filename = f"{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        filepath = os.path.join(self.reports_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        
        results['files'].append(filepath)
        results['content'] = report
        
        logger.info(f"报告生成完成: {filename}")
        return results
    
    def _generate_full_report(self, data: Dict) -> str:
        """生成完整投研报告"""
        portfolio = data.get('portfolio_data', {})
        risk = data.get('risk_results', {})
        attribution = data.get('attribution_results', {})
        optimization = data.get('optimization_results', {})
        monitor = data.get('monitor_results', {})
        
        report = f"""# 投资组合分析报告

**报告时间**: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}  
**报告类型**: 完整分析  
**组合名称**: ETF+个股混合策略

---

## 一、组合概览

### 1.1 基本信息

| 项目 | 数值 |
|:---|:---|
| 报告日期 | {datetime.now().strftime('%Y-%m-%d')} |
| 资产数量 | {len(portfolio.get('assets', {}))} |
| 权益仓位 | {(1-self.config.CASH_WEIGHT)*100:.0f}% |
| 现金仓位 | {self.config.CASH_WEIGHT*100:.0f}% |

### 1.2 业绩表现

{risk.get('metrics', {}).get('total_return', 0)*100:.2f}%

| 指标 | 数值 | 评价 |
|:---|:---:|:---|
| 区间收益率 | {risk.get('metrics', {}).get('total_return', 0)*100:.2f}% | {'✅ 正收益' if risk.get('metrics', {}).get('total_return', 0) > 0 else '❌ 负收益'} |
| 年化波动率 | {risk.get('metrics', {}).get('annual_volatility', 0)*100:.2f}% | {'中高波动' if risk.get('metrics', {}).get('annual_volatility', 0) > 0.2 else '中低波动'} |
| 最大回撤 | {risk.get('metrics', {}).get('max_drawdown', 0)*100:.2f}% | {'⚠️ 回撤较大' if risk.get('metrics', {}).get('max_drawdown', 0) < -0.1 else '可控'} |
| 夏普比率 | {risk.get('metrics', {}).get('sharpe_ratio', 0):.2f} | {'✅ 优秀' if risk.get('metrics', {}).get('sharpe_ratio', 0) > 1 else '⚠️ 一般'} |
| 卡玛比率 | {risk.get('metrics', {}).get('calmar_ratio', 0):.2f} | - |

---

## 二、风险分析

### 2.1 回撤分析

| 指标 | 数值 |
|:---|:---:|
| 历史最大回撤 | {risk.get('metrics', {}).get('max_drawdown', 0)*100:.2f}% |
| 最大回撤日期 | {risk.get('metrics', {}).get('max_dd_date', 'N/A')} |
| 当前回撤 | {risk.get('metrics', {}).get('current_drawdown', 0)*100:.2f}% |
| 连续亏损天数 | {risk.get('metrics', {}).get('consecutive_loss_days', 0)}天 |

### 2.2 VaR风险价值

| 时间尺度 | VaR(95%) | 说明 |
|:---|:---:|:---|
| 1日 | {risk.get('var_analysis', {}).get('daily_var', {}).get('historical', 0)*100:.2f}% | 每日最大预期损失 |
| 5日 | {risk.get('var_analysis', {}).get('var_by_horizon', {}).get('5d', {}).get('historical', 0)*100:.2f}% | 周度风险 |
| 21日 | {risk.get('var_analysis', {}).get('var_by_horizon', {}).get('21d', {}).get('historical', 0)*100:.2f}% | 月度风险 |

### 2.3 风险信号

{f'⚠️ **共{len(monitor.get("alerts", []))}个风险信号**' if monitor.get("alerts") else '✅ 无风险信号'}

"""
        
        # 添加告警列表
        if monitor.get('alerts'):
            report += "| 级别 | 类别 | 消息 | 建议操作 |\n"
            report += "|:---|:---|:---|:---|\n"
            for alert in monitor['alerts'][:5]:  # 只显示前5个
                # 处理Alert对象或字典
                if isinstance(alert, dict):
                    level = alert.get('level', '')
                    category = alert.get('category', '')
                    message = alert.get('message', '')
                    action = alert.get('action', '')
                else:
                    level = getattr(alert, 'level', '')
                    category = getattr(alert, 'category', '')
                    message = getattr(alert, 'message', '')
                    action = getattr(alert, 'action', '')
                report += f"| {level} | {category} | {message} | {action} |\n"
        
        report += """
---

## 三、业绩归因

### 3.1 Brison归因

"""
        
        # 添加归因分析
        if attribution.get('attribution'):
            attr = attribution['attribution']
            report += f"""
| 归因项 | 贡献 | 说明 |
|:---|:---:|:---|
| 配置效应 | {attr.get('allocation_effect', 0)*100:+.2f}% | 行业配置决策贡献 |
| 选股效应 | {attr.get('selection_effect', 0)*100:+.2f}% | 个股选择能力 |
| 交互效应 | {attr.get('interaction_effect', 0)*100:+.2f}% | 配置与选股交互 |
| **总超额收益** | {attr.get('excess_return', 0)*100:+.2f}% | 相对基准 |
"""
        
        report += """
### 3.2 行业贡献

"""
        
        # 添加行业贡献
        if attribution.get('attribution', {}).get('sector_breakdown'):
            report += "| 行业 | 组合权重 | 组合贡献 |\n|:---|:---:|:---:|\n"
            for sector, data in attribution['attribution']['sector_breakdown'].items():
                report += f"| {sector} | {data.get('portfolio_weight', 0)*100:.1f}% | {data.get('portfolio_contribution', 0)*100:+.2f}% |\n"
        
        report += """
---

## 四、资产配置建议

"""
        
        # 添加优化建议
        opt_data = None
        if optimization:
            if isinstance(optimization, dict):
                opt_data = optimization.get('optimization')
            else:
                opt_data = optimization
        
        if opt_data:
            method = opt_data.get('method', '') if isinstance(opt_data, dict) else getattr(opt_data, 'method', '')
            expected_return = opt_data.get('expected_return', 0) if isinstance(opt_data, dict) else getattr(opt_data, 'expected_return', 0)
            expected_risk = opt_data.get('expected_risk', 0) if isinstance(opt_data, dict) else getattr(opt_data, 'expected_risk', 0)
            sharpe = opt_data.get('sharpe_ratio', 0) if isinstance(opt_data, dict) else getattr(opt_data, 'sharpe_ratio', 0)
            weights = opt_data.get('weights', {}) if isinstance(opt_data, dict) else getattr(opt_data, 'weights', {})
            risk_contribs = opt_data.get('risk_contributions', {}) if isinstance(opt_data, dict) else getattr(opt_data, 'risk_contributions', {})
            
            report += f"""
### 4.1 优化方案 ({method})

| 指标 | 数值 |
|:---|:---:|
| 预期年化收益 | {expected_return*100:.2f}% |
| 预期年化波动 | {expected_risk*100:.2f}% |
| 预期夏普比率 | {sharpe:.2f} |

### 4.2 建议权重

| 资产 | 建议权重 | 风险贡献 |
|:---|:---:|:---:|
"""
            for asset, weight in weights.items():
                rc = risk_contribs.get(asset, 'N/A') if risk_contribs else 'N/A'
                rc_str = f"{rc*100:.1f}%" if isinstance(rc, (int, float)) else 'N/A'
                report += f"| {asset} | {weight*100:.1f}% | {rc_str} |\n"
        
        report += f"""
---

## 五、操作建议

### 5.1 即时操作

"""
        
        # 添加操作建议
        if monitor.get('daily_summary', {}).get('key_actions'):
            for action in monitor['daily_summary']['key_actions']:
                report += f"- {action}\n"
        else:
            report += "- 维持当前配置，定期监控\n"
        
        report += f"""
### 5.2 中期规划

- **再平衡**: 建议季度检查，当前偏离度{'较高' if optimization.get('rebalance', {}).get('total_deviation', 0) > 0.05 else '可控'}
- **风险控制**: 最大回撤控制在{abs(self.config.SIGNAL_THRESHOLDS['max_drawdown_alert'])*100:.0f}%以内
- **收益目标**: 年化夏普比率 > 1.0

---

## 六、数据附录

- 数据来源: Tushare Pro
- 计算时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 免责声明: 本报告仅供参考，不构成投资建议

---

*报告由 KimiClaw 投研系统自动生成*
"""
        
        return report
    
    def _generate_daily_report(self, data: Dict) -> str:
        """生成每日简报"""
        monitor = data.get('monitor_results', {})
        summary = monitor.get('daily_summary', {})
        
        report = f"""# 每日监控简报

**日期**: {summary.get('date', datetime.now().strftime('%Y-%m-%d'))}  
**状态**: {summary.get('status', '未知')}

## 今日概览

| 指标 | 数值 |
|:---|:---:|
| 日收益率 | {summary.get('daily_return', 0)*100:+.2f}% |
| 当前回撤 | {summary.get('current_drawdown', 0)*100:.2f}% |
| 夏普比率 | {summary.get('sharpe_ratio', 0):.2f} |
| 告警数量 | {summary.get('alert_count', 0)} |

## 告警摘要

- 严重: {summary.get('alert_summary', {}).get('critical', 0)}
- 警告: {summary.get('alert_summary', {}).get('warning', 0)}
- 提示: {summary.get('alert_summary', {}).get('info', 0)}

## 关键行动

"""
        
        if summary.get('key_actions'):
            for action in summary['key_actions']:
                report += f"- {action}\n"
        else:
            report += "- 无即时操作\n"
        
        report += f"""
---
*自动生成的每日简报*
"""
        
        return report
    
    def _generate_risk_report(self, data: Dict) -> str:
        """生成风险专项报告"""
        risk = data.get('risk_results', {})
        
        report = f"""# 风险分析报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## 风险指标

| 指标 | 数值 | 阈值 | 状态 |
|:---|:---:|:---:|:---:|
| 最大回撤 | {risk.get('metrics', {}).get('max_drawdown', 0)*100:.2f}% | -10% | {'🔴 超限' if risk.get('metrics', {}).get('max_drawdown', 0) < -0.1 else '🟢 正常'} |
| 年化波动 | {risk.get('metrics', {}).get('annual_volatility', 0)*100:.2f}% | 30% | {'🔴 超限' if risk.get('metrics', {}).get('annual_volatility', 0) > 0.3 else '🟢 正常'} |
| VaR(95%) | {risk.get('var_analysis', {}).get('daily_var', {}).get('historical', 0)*100:.2f}% | - | - |
| 夏普比率 | {risk.get('metrics', {}).get('sharpe_ratio', 0):.2f} | >0 | {'🟢 正常' if risk.get('metrics', {}).get('sharpe_ratio', 0) > 0 else '🔴 负值'} |

## 回撤历史

"""
        
        # 添加回撤历史
        dd_analysis = risk.get('drawdown_analysis', {})
        if dd_analysis.get('dd_periods'):
            report += "| 开始日期 | 结束日期 | 持续天数 | 最大回撤 |\n"
            report += "|:---|:---|:---:|:---:|\n"
            for period in dd_analysis['dd_periods'][-5:]:  # 最近5次
                report += f"| {period.get('start_date', '')} | {period.get('end_date', '')} | {period.get('duration', 0)} | {period.get('max_dd', 0)*100:.2f}% |\n"
        
        return report
    
    def _generate_attribution_report(self, data: Dict) -> str:
        """生成归因专项报告"""
        attribution = data.get('attribution_results', {})
        
        report = f"""# 业绩归因报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Brison归因

"""
        
        if attribution.get('attribution'):
            attr = attribution['attribution']
            report += f"""
| 归因项 | 贡献 | 占比 |
|:---|:---:|:---:|
| 配置效应 | {attr.get('allocation_effect', 0)*100:+.2f}% | {attr.get('allocation_pct', 0)*100:.1f}% |
| 选股效应 | {attr.get('selection_effect', 0)*100:+.2f}% | {attr.get('selection_pct', 0)*100:.1f}% |
| 交互效应 | {attr.get('interaction_effect', 0)*100:+.2f}% | - |
| **总超额** | {attr.get('excess_return', 0)*100:+.2f}% | 100% |

### 个股替代效应

"""
            
            if attr.get('substitutions'):
                report += "| 替代方案 | ETF收益 | 个股收益 | 效应 |\n|:---|:---:|:---:|:---:|\n"
                for sub in attr['substitutions']:
                    report += f"| {sub.get('etf_code', '')} | {sub.get('etf_return', 0)*100:.2f}% | {sub.get('stock_portfolio_return', 0)*100:.2f}% | {sub.get('substitution_effect', 0)*100:+.2f}% |\n"
        
        return report
    
    def list_reports(self, days: int = 30) -> List[Dict]:
        """列出近期报告"""
        reports = []
        cutoff = datetime.now() - pd.Timedelta(days=days)
        
        for filename in os.listdir(self.reports_dir):
            if filename.endswith('.md'):
                filepath = os.path.join(self.reports_dir, filename)
                mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                
                if mtime > cutoff:
                    reports.append({
                        'filename': filename,
                        'path': filepath,
                        'created': mtime.isoformat(),
                        'type': filename.split('_')[0]
                    })
        
        return sorted(reports, key=lambda x: x['created'], reverse=True)


if __name__ == '__main__':
    # 测试
    import sys
    sys.path.append('/root/.openclaw/workspace/investment_system')
    from config.config import *
    
    agent = ReporterAgent(Config())
    
    # 测试数据
    test_data = {
        'portfolio_data': {'assets': {'A': {}, 'B': {}}},
        'risk_results': {
            'metrics': {
                'total_return': 0.05,
                'annual_volatility': 0.20,
                'max_drawdown': -0.08,
                'sharpe_ratio': 1.2,
                'calmar_ratio': 3.0
            }
        },
        'monitor_results': {
            'alerts': [],
            'daily_summary': {
                'date': '2026-03-21',
                'status': '🟢 正常',
                'daily_return': 0.01,
                'alert_count': 0
            }
        }
    }
    
    result = agent.run(test_data, report_type='full')
    print(f"报告已生成: {result['files'][0] if result['files'] else 'N/A'}")
