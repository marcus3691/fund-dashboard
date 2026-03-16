#!/usr/bin/env python3
"""
基金数据自动更新与策略执行脚本
本地执行 + 飞书推送结果
"""

import os
import sys
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目路径
sys.path.insert(0, '/root/.openclaw/workspace')
sys.path.insert(0, '/root/.openclaw/workspace/fund_data/monitor')

class FundDataAutoRunner:
    """基金数据自动运行器"""
    
    def __init__(self):
        self.workspace = '/root/.openclaw/workspace'
        self.log_file = f'{self.workspace}/auto_run_{datetime.now().strftime("%Y%m%d")}.log'
        self.results = {}
        
    def log(self, message):
        """记录日志"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_line = f"[{timestamp}] {message}"
        print(log_line)
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_line + '\n')
    
    def run_consensus_signals(self):
        """1. 运行基金经理共识信号生成"""
        self.log("\n" + "="*60)
        self.log("【任务1】生成基金经理共识信号...")
        
        try:
            from consensus_signal_generator import ManagerConsensusSignal
            
            generator = ManagerConsensusSignal()
            signals = generator.generate_signals()
            generator.save_signals()
            
            # 提取关键信息
            stock_signals = [s for s in signals if s.get('type') == 'stock_consensus']
            stock_signals.sort(key=lambda x: x.get('consensus_count', 0), reverse=True)
            
            top5 = stock_signals[:5] if stock_signals else []
            
            self.results['consensus_signals'] = {
                'status': 'success',
                'total_managers': generator.total_managers,
                'total_signals': len(signals),
                'top5_stocks': [
                    {
                        'code': s.get('code'),
                        'consensus_count': s.get('consensus_count'),
                        'avg_holding': s.get('avg_holding_ratio', 0)
                    }
                    for s in top5
                ]
            }
            
            self.log(f"  ✅ 成功生成 {len(signals)} 个信号")
            self.log(f"  📊 覆盖 {generator.total_managers} 位基金经理")
            
        except Exception as e:
            self.log(f"  ❌ 失败: {e}")
            self.results['consensus_signals'] = {'status': 'error', 'message': str(e)}
    
    def run_trump_strategy(self):
        """2. 运行特朗普访华策略分析"""
        self.log("\n" + "="*60)
        self.log("【任务2】执行特朗普访华策略分析...")
        
        try:
            # 导入策略模块
            from trump_visit_strategy_v2 import TrumpVisitStrategy
            
            strategy = TrumpVisitStrategy()
            report = strategy.generate_report()
            
            # 提取关键信息
            scenarios = report.get('scenarios', {})
            
            self.results['trump_strategy'] = {
                'status': 'success',
                'expected_return': report.get('expected_return'),
                'portfolio_count': len(report.get('portfolio', [])),
                'scenarios_summary': {
                    name: {
                        'probability': data.get('probability'),
                        'return': f"{data.get('portfolio_return', 0)*100:+.2f}%"
                    }
                    for name, data in scenarios.items()
                }
            }
            
            self.log(f"  ✅ 策略分析完成")
            self.log(f"  📈 加权预期收益: {report.get('expected_return')}")
            
        except Exception as e:
            self.log(f"  ❌ 失败: {e}")
            self.results['trump_strategy'] = {'status': 'error', 'message': str(e)}
    
    def run_fund_screening(self):
        """3. 运行基金筛选（可选，耗时较长）"""
        self.log("\n" + "="*60)
        self.log("【任务3】基金产品库监控...")
        
        try:
            # 读取当前产品库状态
            import pandas as pd
            
            core_file = f'{self.workspace}/fund_data/fund_core_library_final.csv'
            watch_file = f'{self.workspace}/fund_data/fund_watch_library_final.csv'
            
            summary = {}
            
            if os.path.exists(core_file):
                df = pd.read_csv(core_file)
                summary['core_count'] = len(df)
                summary['core_avg_return'] = df['return_1y'].mean() if 'return_1y' in df.columns else 0
                summary['core_avg_quality'] = df['quality_score'].mean() if 'quality_score' in df.columns else 0
            
            if os.path.exists(watch_file):
                df = pd.read_csv(watch_file)
                summary['watch_count'] = len(df)
            
            self.results['fund_screening'] = {
                'status': 'success',
                'summary': summary
            }
            
            self.log(f"  ✅ 产品库状态: 核心库{summary.get('core_count', 0)}只, 观察库{summary.get('watch_count', 0)}只")
            
        except Exception as e:
            self.log(f"  ❌ 失败: {e}")
            self.results['fund_screening'] = {'status': 'error', 'message': str(e)}
    
    def generate_summary(self):
        """生成执行摘要"""
        summary = {
            'run_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'tasks_completed': 0,
            'tasks_failed': 0,
            'key_findings': []
        }
        
        for task_name, result in self.results.items():
            if result.get('status') == 'success':
                summary['tasks_completed'] += 1
            else:
                summary['tasks_failed'] += 1
        
        # 提取关键发现
        if 'consensus_signals' in self.results and self.results['consensus_signals'].get('status') == 'success':
            top_stocks = self.results['consensus_signals'].get('top5_stocks', [])
            if top_stocks:
                summary['key_findings'].append(f"基金经理共识TOP1: {top_stocks[0].get('code')} ({top_stocks[0].get('consensus_count')}人)")
        
        if 'trump_strategy' in self.results and self.results['trump_strategy'].get('status') == 'success':
            summary['key_findings'].append(f"特朗普策略预期收益: {self.results['trump_strategy'].get('expected_return')}")
        
        return summary
    
    def send_feishu_notification(self):
        """发送飞书通知"""
        self.log("\n" + "="*60)
        self.log("【推送】生成飞书通知...")
        
        summary = self.generate_summary()
        
        # 构建消息内容
        message_lines = [
            f"📊 **基金数据自动更新完成**",
            f"",
            f"⏰ 执行时间: {summary['run_time']}",
            f"✅ 成功任务: {summary['tasks_completed']}",
            f"❌ 失败任务: {summary['tasks_failed']}",
            f"",
            f"**📌 关键发现:**",
        ]
        
        for finding in summary['key_findings']:
            message_lines.append(f"• {finding}")
        
        # 添加详细信息
        message_lines.append(f"")
        message_lines.append(f"**📈 详细结果:**")
        
        # 共识信号
        if 'consensus_signals' in self.results and self.results['consensus_signals'].get('status') == 'success':
            cs = self.results['consensus_signals']
            message_lines.append(f"")
            message_lines.append(f"**基金经理共识信号:**")
            message_lines.append(f"• 覆盖经理: {cs.get('total_managers')}人")
            message_lines.append(f"• 生成信号: {cs.get('total_signals')}个")
            
            top5 = cs.get('top5_stocks', [])
            if top5:
                message_lines.append(f"• TOP5共识股:")
                for i, stock in enumerate(top5[:3], 1):
                    message_lines.append(f"  {i}. {stock.get('code')} ({stock.get('consensus_count')}人)")
        
        # 特朗普策略
        if 'trump_strategy' in self.results and self.results['trump_strategy'].get('status') == 'success':
            ts = self.results['trump_strategy']
            message_lines.append(f"")
            message_lines.append(f"**特朗普访华策略:**")
            message_lines.append(f"• 组合ETF: {ts.get('portfolio_count')}只")
            message_lines.append(f"• 预期收益: {ts.get('expected_return')}")
            
            scenarios = ts.get('scenarios_summary', {})
            if scenarios:
                message_lines.append(f"• 情景分析:")
                for name, data in scenarios.items():
                    message_lines.append(f"  - {name} ({data.get('probability')}): {data.get('return')}")
        
        # 产品库状态
        if 'fund_screening' in self.results and self.results['fund_screening'].get('status') == 'success':
            fs = self.results['fund_screening'].get('summary', {})
            message_lines.append(f"")
            message_lines.append(f"**产品库状态:**")
            message_lines.append(f"• 核心库: {fs.get('core_count', 0)}只")
            message_lines.append(f"• 观察库: {fs.get('watch_count', 0)}只")
            if fs.get('core_avg_return'):
                message_lines.append(f"• 核心库平均收益: {fs.get('core_avg_return'):.2f}%")
        
        message_lines.append(f"")
        message_lines.append(f"📧 详细报告已发送至: 18817205079@139.com")
        message_lines.append(f"📁 本地文件: /root/.openclaw/workspace/")
        
        message = '\n'.join(message_lines)
        
        # 保存消息到文件
        message_file = f'{self.workspace}/last_notification.txt'
        with open(message_file, 'w', encoding='utf-8') as f:
            f.write(message)
        
        self.log(f"  ✅ 飞书通知内容已生成")
        
        return message
    
    def send_email_notification(self):
        """发送邮件通知"""
        self.log("\n" + "="*60)
        self.log("【推送】生成HTML报告并发送邮件...")
        
        try:
            # 先生成HTML报告
            from fund_report_html_generator import FundReportHtmlGenerator
            generator = FundReportHtmlGenerator()
            html_file = generator.generate_full_report()
            self.log(f"  ✅ HTML报告已生成: {html_file}")
            
            # 再发送邮件
            from fund_report_email_sender import FundReportEmailSender
            sender = FundReportEmailSender()
            success = sender.send_daily_report()
            
            if success:
                self.log(f"  ✅ 邮件发送成功（含HTML报告附件）")
            else:
                self.log(f"  ❌ 邮件发送失败")
            
            return success
            
        except Exception as e:
            self.log(f"  ❌ 邮件模块错误: {e}")
            return False
    
    def run_all(self):
        """运行所有任务"""
        self.log("="*60)
        self.log("基金数据自动更新开始")
        self.log("="*60)
        self.log(f"工作目录: {self.workspace}")
        self.log(f"日志文件: {self.log_file}")
        
        # 执行各项任务
        self.run_consensus_signals()
        self.run_trump_strategy()
        self.run_fund_screening()
        
        # 生成并保存摘要
        summary = self.generate_summary()
        summary_file = f'{self.workspace}/auto_run_summary_{datetime.now().strftime("%Y%m%d")}.json'
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump({
                'summary': summary,
                'details': self.results
            }, f, ensure_ascii=False, indent=2)
        
        self.log(f"\n摘要已保存: {summary_file}")
        
        # 生成飞书通知
        notification = self.send_feishu_notification()
        
        # 发送邮件通知
        self.send_email_notification()
        
        self.log("\n" + "="*60)
        self.log("基金数据自动更新完成")
        self.log("="*60)
        
        return notification


def main():
    """主函数"""
    runner = FundDataAutoRunner()
    notification = runner.run_all()
    
    # 输出通知内容（可以被调用者捕获）
    print("\n" + "="*60)
    print("飞书通知内容:")
    print("="*60)
    print(notification)
    
    return notification


if __name__ == '__main__':
    main()
