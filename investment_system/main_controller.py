#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main Controller - 主控系统
功能：任务调度、Agent编排、流程控制
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd
import numpy as np

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import *
from agents.data_miner import DataMinerAgent
from agents.risk_calc import RiskCalcAgent
from agents.attribution_analyzer import AttributionAgent
from agents.portfolio_optimizer import PortfolioAgent
from agents.signal_monitor import SignalMonitorAgent
from agents.report_generator import ReporterAgent

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('MainController')


class InvestmentResearchSystem:
    """
    KimiClaw 投研系统主控
    协调五大Agent完成完整投研流程
    """
    
    def __init__(self):
        self.config = Config()
        self._init_agents()
        self.execution_log = []
        
    def _init_agents(self):
        """初始化所有Agent"""
        logger.info("正在初始化Agent...")
        
        self.agents = {
            'data_miner': DataMinerAgent(self.config),
            'risk_calc': RiskCalcAgent(self.config),
            'attribution': AttributionAgent(self.config),
            'portfolio': PortfolioAgent(self.config),
            'signal_monitor': SignalMonitorAgent(self.config),
            'reporter': ReporterAgent(self.config)
        }
        
        logger.info("✓ 所有Agent初始化完成")
    
    def run_full_analysis(self, task_input: Dict) -> Dict:
        """
        执行完整投研分析流程
        
        task_input: {
            'start_date': '20260101',
            'end_date': '20260320',
            'analysis_type': 'full',  # full / daily / risk_only
            'report_type': 'full'     # full / daily / risk
        }
        """
        start_time = datetime.now()
        self.execution_log = []
        
        logger.info("="*60)
        logger.info("启动完整投研分析流程")
        logger.info("="*60)
        
        results = {
            'status': 'success',
            'start_time': start_time.isoformat(),
            'steps': {}
        }
        
        try:
            # Step 1: 数据抓取
            logger.info("\n【Step 1/6】数据抓取...")
            step1_result = self._step_data_collection(task_input)
            results['steps']['data_collection'] = step1_result
            
            # Step 2: 组合收益计算
            logger.info("\n【Step 2/6】组合收益计算...")
            step2_result = self._step_portfolio_calculation(step1_result)
            results['steps']['portfolio_calc'] = step2_result
            
            # Step 3: 风险测算
            logger.info("\n【Step 3/6】风险测算...")
            step3_result = self._step_risk_analysis(step2_result)
            results['steps']['risk_analysis'] = step3_result
            
            # Step 4: 业绩归因
            logger.info("\n【Step 4/6】业绩归因...")
            step4_result = self._step_attribution(step1_result, step2_result)
            results['steps']['attribution'] = step4_result
            
            # Step 5: 资产配置优化
            logger.info("\n【Step 5/6】资产配置优化...")
            step5_result = self._step_portfolio_optimization(step2_result)
            results['steps']['optimization'] = step5_result
            
            # Step 6: 信号监控
            logger.info("\n【Step 6/6】信号监控...")
            step6_result = self._step_signal_monitoring(
                step2_result, step3_result, step5_result
            )
            results['steps']['signal_monitor'] = step6_result
            
            # Step 7: 报告生成
            logger.info("\n【Step 7/7】报告生成...")
            step7_result = self._step_report_generation(
                task_input.get('report_type', 'full'),
                results['steps']
            )
            results['steps']['report'] = step7_result
            
            # 完成
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            results['end_time'] = end_time.isoformat()
            results['duration_seconds'] = duration
            results['execution_log'] = self.execution_log
            
            logger.info("="*60)
            logger.info(f"✓ 分析完成，耗时 {duration:.1f} 秒")
            logger.info("="*60)
            
        except Exception as e:
            logger.error(f"✗ 分析流程失败: {e}")
            results['status'] = 'failed'
            results['error'] = str(e)
        
        return results
    
    def _step_data_collection(self, task_input: Dict) -> Dict:
        """Step 1: 数据收集"""
        codes = list(self.config.PORTFOLIO_CONFIG.keys())
        start_date = task_input.get('start_date', '20260101')
        end_date = task_input.get('end_date', datetime.now().strftime('%Y%m%d'))
        
        result = self.agents['data_miner'].run({
            'codes': codes,
            'start_date': start_date,
            'end_date': end_date,
            'data_types': ['price', 'benchmark'],
            'use_mock': False  # 使用真实数据
        })
        
        self._log_step('data_collection', result)
        return result
    
    def _step_portfolio_calculation(self, data_result: Dict) -> Dict:
        """Step 2: 计算组合收益"""
        weights = {
            code: cfg['weight'] 
            for code, cfg in self.config.PORTFOLIO_CONFIG.items()
        }
        
        returns_df = self.agents['data_miner'].calculate_portfolio_returns(
            data_result, weights
        )
        
        # 计算现金收益
        cash_daily_return = self.config.CASH_ANNUAL_RETURN / 252
        returns_df['portfolio_return'] += self.config.CASH_WEIGHT * cash_daily_return
        returns_df['nav'] = (1 + returns_df['portfolio_return']).cumprod()
        
        result = {
            'returns_df': returns_df,
            'weights': weights,
            'total_return': returns_df['cum_return'].iloc[-1],
            'data': data_result
        }
        
        self._log_step('portfolio_calc', {'status': 'success', 'records': len(returns_df)})
        return result
    
    def _step_risk_analysis(self, portfolio_result: Dict) -> Dict:
        """Step 3: 风险分析"""
        returns_df = portfolio_result['returns_df']
        
        result = self.agents['risk_calc'].run({
            'returns': returns_df['portfolio_return'],
            'nav': returns_df['nav'],
            'dates': returns_df['date'].tolist()
        }, tests=['drawdown', 'var', 'risk_metrics', 'signals'])
        
        self._log_step('risk_analysis', result)
        return result
    
    def _step_attribution(self, data_result: Dict, portfolio_result: Dict) -> Dict:
        """Step 4: 业绩归因"""
        # 构造归因数据
        portfolio_data = data_result.get('data', {})
        
        port_weights = portfolio_result['weights']
        port_returns = {}
        
        for code in port_weights.keys():
            if code in portfolio_data and 'price' in portfolio_data[code]:
                price_df = portfolio_data[code]['price']
                total_return = (price_df['close'].iloc[-1] / price_df['close'].iloc[0]) - 1
                port_returns[code] = total_return
        
        # 基准收益
        benchmark_data = data_result.get('benchmarks', {})
        bench_returns = {}
        bench_weights = {'000300.SH': 0.5, '000906.SH': 0.5}  # 简化假设
        
        for code in bench_weights.keys():
            if code in benchmark_data:
                bench_df = benchmark_data[code]
                bench_returns[code] = (bench_df['close'].iloc[-1] / bench_df['close'].iloc[0]) - 1
        
        # 个股替代效应分析
        substitution_data = {
            'substitutions': [{
                'etf_code': '515880.SH',
                'etf_return': -0.6570,  # 通信设备ETF
                'etf_weight': 0.12,
                'stock_codes': ['300394.SZ', '688195.SH'],
                'stock_weights': [0.04, 0.08],
                'stock_returns': [0.5324, 0.3382]
            }]
        }
        
        # 执行归因
        brison_result = self.agents['attribution'].run({
            'portfolio': {'weights': port_weights, 'returns': port_returns},
            'benchmark': {'weights': bench_weights, 'returns': bench_returns}
        }, method='brison')
        
        sector_result = self.agents['attribution'].run({
            'portfolio': {'weights': port_weights, 'returns': port_returns},
            'benchmark': {'weights': bench_weights, 'returns': bench_returns}
        }, method='sector')
        
        sub_result = self.agents['attribution'].run(substitution_data, method='substitution')
        
        result = {
            'brison': brison_result,
            'sector': sector_result,
            'substitution': sub_result
        }
        
        self._log_step('attribution', {'status': 'success', 'methods': 3})
        return result
    
    def _step_portfolio_optimization(self, portfolio_result: Dict) -> Dict:
        """Step 5: 资产配置优化 - 使用SMART框架"""
        from agents.smart_portfolio_model import SMARTPortfolioModel, SMARTConfig
        
        # 使用SMART模型计算配置
        smart_model = SMARTPortfolioModel(SMARTConfig())
        target_weights, cash_weight = smart_model.calculate_weights()
        
        # 生成报告
        report_content = smart_model.generate_report(target_weights, cash_weight)
        
        # 保存SMART配置报告
        report_path = os.path.join(self.config.REPORTS_DIR, f'smart_config_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        result = {
            'method': 'SMART',
            'weights': target_weights,
            'cash_weight': cash_weight,
            'report_path': report_path,
            'report_content': report_content
        }
        
        self._log_step('optimization', {'status': 'success', 'method': 'SMART'})
        return result
    
    def _step_signal_monitoring(self, portfolio_result: Dict, risk_result: Dict, 
                                 optimization_result: Dict) -> Dict:
        """Step 6: 信号监控"""
        # 构造监控数据
        current_weights = portfolio_result['weights']
        
        # 获取SMART配置权重作为目标权重
        target_weights = optimization_result.get('weights', current_weights)
        
        monitor_data = {
            'portfolio_metrics': risk_result.get('metrics', {}),
            'asset_metrics': {
                code: {'current_weight': w, 'target_weight': target_weights.get(code, w)}
                for code, w in current_weights.items()
            },
            'current_weights': current_weights,
            'target_weights': target_weights,
            'last_rebalance_date': '2026-01-01'  # 假设
        }
        
        result = self.agents['signal_monitor'].run(monitor_data, check_type='full')
        
        self._log_step('signal_monitor', result)
        return result
    
    def _step_report_generation(self, report_type: str, all_results: Dict) -> Dict:
        """Step 7: 报告生成"""
        report_data = {
            'portfolio_data': all_results.get('portfolio_calc', {}),
            'risk_results': all_results.get('risk_analysis', {}),
            'attribution_results': all_results.get('attribution', {}).get('brison', {}),
            'optimization_results': all_results.get('optimization', {}),
            'monitor_results': all_results.get('signal_monitor', {})
        }
        
        result = self.agents['reporter'].run(report_data, report_type=report_type)
        
        # 如果有SMART配置报告，附加到结果中
        smart_report = all_results.get('optimization', {}).get('report_path')
        if smart_report:
            result['smart_report'] = smart_report
        
        self._log_step('report_generation', result)
        return result
    
    def _log_step(self, step_name: str, result: Dict):
        """记录执行日志"""
        status = result.get('status', 'unknown')
        log_entry = f"{step_name}: {status}"
        self.execution_log.append(log_entry)
        
        if status == 'success':
            logger.info(f"✓ {log_entry}")
        else:
            logger.warning(f"⚠ {log_entry}")
    
    def run_daily_monitor(self) -> Dict:
        """每日监控快捷入口"""
        return self.run_full_analysis({
            'start_date': (datetime.now() - timedelta(days=30)).strftime('%Y%m%d'),
            'end_date': datetime.now().strftime('%Y%m%d'),
            'analysis_type': 'daily',
            'report_type': 'daily'
        })


# 主入口
if __name__ == '__main__':
    print("="*60)
    print("KimiClaw 投研系统")
    print("="*60)
    
    # 创建系统实例
    system = InvestmentResearchSystem()
    
    # 执行完整分析
    result = system.run_full_analysis({
        'start_date': '20260101',
        'end_date': '20260320',
        'analysis_type': 'full',
        'report_type': 'full'
    })
    
    # 输出结果
    print("\n" + "="*60)
    print("执行结果")
    print("="*60)
    print(f"状态: {result['status']}")
    print(f"耗时: {result.get('duration_seconds', 0):.1f} 秒")
    print(f"\n执行步骤:")
    for log in result.get('execution_log', []):
        print(f"  - {log}")
    
    if result['status'] == 'success':
        print("\n✓ 分析完成，报告已生成")
        report_path = result.get('steps', {}).get('report', {}).get('files', [])
        if report_path:
            print(f"  报告路径: {report_path[0]}")
    else:
        print(f"\n✗ 失败: {result.get('error', 'Unknown error')}")
