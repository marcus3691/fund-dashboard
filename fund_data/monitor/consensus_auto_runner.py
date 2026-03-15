#!/usr/bin/env python3
"""
基金经理共识信号报告自动化执行脚本
整合信号生成、报告生成、邮件发送全流程
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, '/root/.openclaw/workspace/fund_data/monitor')

def log_message(message: str, log_file=None):
    """输出日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    if log_file:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_line + '\n')

def run_automation(report_type: str = 'daily', recipient: str = None, 
                   skip_signal: bool = False, skip_email: bool = False) -> bool:
    """
    执行完整的自动化流程
    
    Args:
        report_type: 'daily' 或 'weekly'
        recipient: 收件人邮箱
        skip_signal: 是否跳过信号生成
        skip_email: 是否跳过邮件发送
    
    Returns:
        是否全部成功
    """
    # 路径配置
    monitor_dir = '/root/.openclaw/workspace/fund_data/monitor'
    log_dir = os.path.join(monitor_dir, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    date_str = datetime.now().strftime('%Y%m%d')
    log_file = os.path.join(log_dir, f"auto_{report_type}_{date_str}.log")
    
    log_message("="*60, log_file)
    log_message(f"开始执行{report_type}报告自动化任务", log_file)
    log_message("="*60, log_file)
    
    success = True
    
    # 步骤1: 生成共识信号
    if not skip_signal:
        log_message("\n[步骤1] 生成共识信号...", log_file)
        try:
            from consensus_signal_generator import ManagerConsensusSignal
            generator = ManagerConsensusSignal()
            signals = generator.generate_signals()
            generator.save_signals()
            log_message(f"✓ 信号生成完成: {len(signals)}个信号", log_file)
        except Exception as e:
            log_message(f"✗ 信号生成失败: {e}", log_file)
            success = False
    else:
        log_message("[步骤1] 跳过信号生成", log_file)
    
    # 步骤2: 生成报告
    log_message("\n[步骤2] 生成HTML报告...", log_file)
    try:
        from consensus_report_generator import ConsensusReportGenerator
        report_gen = ConsensusReportGenerator(report_type=report_type)
        report_path, html_content = report_gen.generate_and_save()
        if report_path:
            log_message(f"✓ 报告生成完成: {report_path}", log_file)
        else:
            log_message("✗ 报告生成失败", log_file)
            success = False
    except Exception as e:
        log_message(f"✗ 报告生成失败: {e}", log_file)
        success = False
    
    # 步骤3: 发送邮件
    if not skip_email:
        log_message("\n[步骤3] 发送邮件...", log_file)
        try:
            from consensus_email_sender import ConsensusEmailSender
            sender = ConsensusEmailSender(recipient_email=recipient)
            email_success = sender.send_report(report_type)
            if email_success:
                log_message("✓ 邮件发送成功", log_file)
            else:
                log_message("✗ 邮件发送失败", log_file)
                success = False
        except Exception as e:
            log_message(f"✗ 邮件发送失败: {e}", log_file)
            success = False
    else:
        log_message("[步骤3] 跳过邮件发送", log_file)
    
    log_message("\n" + "="*60, log_file)
    if success:
        log_message("✅ 自动化任务全部完成", log_file)
    else:
        log_message("⚠️ 自动化任务部分完成，有错误发生", log_file)
    log_message("="*60, log_file)
    log_message("", log_file)
    
    return success

def main():
    """
    命令行入口
    """
    parser = argparse.ArgumentParser(
        description='基金经理共识信号报告自动化执行',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s daily                    # 执行日报流程
  %(prog)s weekly                   # 执行周报流程
  %(prog)s daily --skip-signal      # 跳过信号生成
  %(prog)s daily --skip-email       # 跳过邮件发送
  %(prog)s weekly --to user@139.com # 发送到指定邮箱
        """
    )
    
    parser.add_argument(
        'type',
        choices=['daily', 'weekly'],
        help='报告类型: daily(日报) 或 weekly(周报)'
    )
    parser.add_argument(
        '--to', '-t',
        help='收件人邮箱地址'
    )
    parser.add_argument(
        '--skip-signal',
        action='store_true',
        help='跳过信号生成步骤(使用现有数据)'
    )
    parser.add_argument(
        '--skip-email',
        action='store_true',
        help='跳过邮件发送步骤'
    )
    
    args = parser.parse_args()
    
    success = run_automation(
        report_type=args.type,
        recipient=args.to,
        skip_signal=args.skip_signal,
        skip_email=args.skip_email
    )
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
