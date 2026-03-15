#!/usr/bin/env python3
"""
基金经理共识信号报告邮件发送器
支持定时发送周报/日报
"""

import os
import sys
import json
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path

sys.path.insert(0, '/root/.openclaw/workspace/fund_data/monitor')


class ConsensusEmailSender:
    """
    共识信号报告邮件发送器
    使用139邮箱SMTP服务
    """
    
    # 邮件配置 - 139邮箱
    SMTP_SERVER = 'smtp.139.com'
    SMTP_PORT = 465  # SSL端口
    SENDER_EMAIL = '18817205079@139.com'
    AUTH_CODE = 'ab96ed0b496fd94f6e00'
    
    def __init__(self, recipient_email: str = None):
        """
        初始化邮件发送器
        
        Args:
            recipient_email: 收件人邮箱，默认为发件人自己
        """
        self.recipient = recipient_email or self.SENDER_EMAIL
        self.data_dir = '/root/.openclaw/workspace/fund_data/monitor'
        self.reports_dir = os.path.join(self.data_dir, 'reports')
        
    def _load_report(self, report_type: str = 'weekly', date_str: str = None) -> tuple:
        """
        加载报告文件
        
        Args:
            report_type: 'weekly' 或 'daily'
            date_str: 日期字符串 YYYYMMDD，默认为今天
        
        Returns:
            (报告路径, HTML内容)
        """
        if date_str is None:
            date_str = datetime.now().strftime('%Y%m%d')
        
        report_filename = f"consensus_report_{report_type}_{date_str}.html"
        report_path = os.path.join(self.reports_dir, report_filename)
        
        if not os.path.exists(report_path):
            print(f"错误: 报告文件不存在: {report_path}")
            # 尝试查找最新的报告
            print("正在查找最新报告...")
            if os.path.exists(self.reports_dir):
                reports = [f for f in os.listdir(self.reports_dir) 
                          if f.startswith(f'consensus_report_{report_type}_')]
                if reports:
                    reports.sort(reverse=True)
                    report_path = os.path.join(self.reports_dir, reports[0])
                    print(f"找到最新报告: {report_path}")
                else:
                    return None, None
            else:
                return None, None
        
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return report_path, content
        except Exception as e:
            print(f"错误: 无法读取报告: {e}")
            return None, None
    
    def _load_signals_summary(self) -> dict:
        """加载信号摘要用于邮件正文"""
        signal_file = os.path.join(self.data_dir, 'manager_consensus_signals.json')
        try:
            with open(signal_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            signals = data.get('signals', [])
            
            # 统计各类信号
            stock_signals = [s for s in signals if s.get('type') == 'stock_consensus']
            sector_signals = [s for s in signals if s.get('type') == 'sector_consensus']
            perf_signals = [s for s in signals if s.get('type') == 'performance_consensus']
            
            # TOP5股票
            stock_signals.sort(key=lambda x: x.get('consensus_count', 0), reverse=True)
            top5_stocks = stock_signals[:5]
            
            # 热门行业
            sector_signals.sort(key=lambda x: x.get('consensus_count', 0), reverse=True)
            top3_sectors = sector_signals[:3]
            
            # 情绪
            sentiment = perf_signals[0] if perf_signals else {'sentiment': 'neutral', 'avg_return': 0}
            
            return {
                'total_managers': data.get('total_managers', 0),
                'generated_at': data.get('generated_at', ''),
                'top_stocks': top5_stocks,
                'top_sectors': top3_sectors,
                'sentiment': sentiment
            }
        except Exception as e:
            print(f"警告: 无法加载信号摘要: {e}")
            return None
    
    def _create_email_subject(self, report_type: str) -> str:
        """创建邮件主题"""
        now = datetime.now()
        if report_type == 'weekly':
            return f"【基金经理共识周报】第{now.strftime('%W')}周市场信号 - {now.strftime('%m月%d日')}"
        else:
            return f"【基金经理共识日报】{now.strftime('%m月%d日')}市场信号"
    
    def _create_email_body(self, report_type: str, summary: dict) -> str:
        """创建邮件正文(HTML格式)"""
        now = datetime.now()
        
        if report_type == 'weekly':
            period = f"第{now.strftime('%W')}周"
        else:
            period = now.strftime('%Y年%m月%d日')
        
        # 情绪表情
        sentiment = summary.get('sentiment', {})
        sentiment_type = sentiment.get('sentiment', 'neutral')
        sentiment_emoji = '😊' if sentiment_type == 'positive' else '😰' if sentiment_type == 'negative' else '😐'
        sentiment_text = '积极' if sentiment_type == 'positive' else '谨慎' if sentiment_type == 'negative' else '中性'
        
        # TOP股票表格
        top_stocks = summary.get('top_stocks', [])
        stocks_html = ""
        for i, stock in enumerate(top_stocks, 1):
            code = stock.get('code', '')
            count = stock.get('consensus_count', 0)
            ratio = stock.get('avg_holding_ratio', 0)
            stocks_html += f"""
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;">#{i}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>{code}</strong></td>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;">{count}人</td>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;">{ratio}%</td>
                </tr>
"""
        
        # 热门行业
        top_sectors = summary.get('top_sectors', [])
        sectors_html = ""
        for sector in top_sectors:
            name = sector.get('sector', '')
            count = sector.get('consensus_count', 0)
            sectors_html += f"""
                <span style="display: inline-block; background: #667eea; color: white; padding: 5px 12px; 
                             border-radius: 20px; margin: 3px; font-size: 14px;">
                    {name} ({count}人)
                </span>
"""
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif; 
               line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; 
                   padding: 30px; border-radius: 12px; text-align: center; margin-bottom: 20px; }}
        .header h1 {{ margin: 0; font-size: 24px; }}
        .header p {{ margin: 10px 0 0; opacity: 0.9; }}
        .section {{ background: #f8f9fa; padding: 20px; border-radius: 12px; margin-bottom: 20px; }}
        .section h2 {{ margin-top: 0; color: #667eea; font-size: 18px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ text-align: left; padding: 10px; color: #666; font-weight: normal; border-bottom: 2px solid #ddd; }}
        .sentiment-box {{ text-align: center; padding: 20px; background: white; border-radius: 8px; }}
        .sentiment-emoji {{ font-size: 48px; }}
        .sentiment-score {{ font-size: 36px; font-weight: bold; color: #667eea; margin: 10px 0; }}
        .btn {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; 
                text-decoration: none; border-radius: 25px; margin-top: 20px; }}
        .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 基金经理共识信号报告</h1>
        <p>{period} | 覆盖{summary.get('total_managers', 0)}位基金经理</p>
    </div>
    
    <div class="section">
        <h2>📊 市场情绪</h2>
        <div class="sentiment-box">
            <div class="sentiment-emoji">{sentiment_emoji}</div>
            <div class="sentiment-score">{sentiment.get('avg_return', 0)}%</div>
            <p>平均收益率 | {sentiment_text}</p>
        </div>
    </div>
    
    <div class="section">
        <h2>🏆 共识股票 TOP5</h2>
        <table>
            <thead>
                <tr>
                    <th>排名</th>
                    <th>股票代码</th>
                    <th>共识人数</th>
                    <th>平均持仓</th>
                </tr>
            </thead>
            <tbody>
                {stocks_html}
            </tbody>
        </table>
    </div>
    
    <div class="section">
        <h2>🔥 热门行业</h2>
        {sectors_html}
    </div>
    
    <div style="text-align: center;">
        <a href="#" class="btn">查看完整报告</a>
    </div>
    
    <div class="footer">
        <p>基金经理共识信号系统 | 数据仅供参考，不构成投资建议</p>
        <p>生成时间: {summary.get('generated_at', '')[:19]}</p>
    </div>
</body>
</html>
"""
        return html
    
    def send_report(self, report_type: str = 'weekly', date_str: str = None) -> bool:
        """
        发送报告邮件
        
        Args:
            report_type: 'weekly' 或 'daily'
            date_str: 日期字符串 YYYYMMDD
        
        Returns:
            是否发送成功
        """
        print(f"\n{'='*80}")
        print(f"开始发送{'周报' if report_type == 'weekly' else '日报'}邮件...")
        print(f"{'='*80}\n")
        
        # 加载报告
        report_path, report_html = self._load_report(report_type, date_str)
        if not report_path:
            print("❌ 无法加载报告文件")
            return False
        
        # 加载摘要
        summary = self._load_signals_summary()
        if not summary:
            print("⚠️ 无法加载信号摘要")
        
        # 创建邮件
        msg = MIMEMultipart('alternative')
        msg['From'] = self.SENDER_EMAIL
        msg['To'] = self.recipient
        msg['Subject'] = self._create_email_subject(report_type)
        
        # 邮件正文
        if summary:
            body_html = self._create_email_body(report_type, summary)
        else:
            body_html = f"""
            <html><body>
            <p>基金经理共识信号{'周报' if report_type == 'weekly' else '日报'}已生成</p>
            <p>请查看附件中的完整报告</p>
            </body></html>
            """
        
        # 添加正文
        msg.attach(MIMEText(body_html, 'html', 'utf-8'))
        
        # 添加附件
        try:
            with open(report_path, 'rb') as f:
                attachment = MIMEBase('application', 'octet-stream')
                attachment.set_payload(f.read())
            
            encoders.encode_base64(attachment)
            filename = os.path.basename(report_path)
            attachment.add_header(
                'Content-Disposition',
                f'attachment; filename="{filename}"'
            )
            msg.attach(attachment)
            print(f"✅ 附件已添加: {filename}")
        except Exception as e:
            print(f"⚠️ 添加附件失败: {e}")
        
        # 发送邮件
        try:
            print(f"正在连接SMTP服务器: {self.SMTP_SERVER}:{self.SMTP_PORT}")
            with smtplib.SMTP_SSL(self.SMTP_SERVER, self.SMTP_PORT) as server:
                print("正在登录...")
                server.login(self.SENDER_EMAIL, self.AUTH_CODE)
                print("正在发送邮件...")
                server.sendmail(self.SENDER_EMAIL, [self.recipient], msg.as_string())
            
            print(f"\n{'='*80}")
            print(f"✅ 邮件发送成功!")
            print(f"{'='*80}")
            print(f"收件人: {self.recipient}")
            print(f"主题: {msg['Subject']}")
            print(f"附件: {filename}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"\n❌ 邮件发送失败: 认证错误")
            print(f"   请检查邮箱和授权码是否正确")
            return False
        except smtplib.SMTPException as e:
            print(f"\n❌ 邮件发送失败: SMTP错误 - {e}")
            return False
        except Exception as e:
            print(f"\n❌ 邮件发送失败: {e}")
            return False
    
    def send_daily_report(self) -> bool:
        """发送日报"""
        return self.send_report('daily')
    
    def send_weekly_report(self) -> bool:
        """发送周报"""
        return self.send_report('weekly')


def main():
    """
    命令行入口
    用法: 
        python consensus_email_sender.py weekly
        python consensus_email_sender.py daily
        python consensus_email_sender.py test [recipient@email.com]
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='基金经理共识信号报告邮件发送器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s weekly                    # 发送周报
  %(prog)s daily                     # 发送日报
  %(prog)s weekly --to user@139.com  # 发送到指定邮箱
  %(prog)s test                      # 发送测试邮件
        """
    )
    
    parser.add_argument(
        'action',
        choices=['weekly', 'daily', 'test'],
        help='发送类型: weekly(周报), daily(日报), test(测试)'
    )
    parser.add_argument(
        '--to', '-t',
        help='收件人邮箱地址'
    )
    parser.add_argument(
        '--date', '-d',
        help='报告日期 (YYYYMMDD)，默认为今天'
    )
    
    args = parser.parse_args()
    
    # 创建发送器
    sender = ConsensusEmailSender(recipient_email=args.to)
    
    # 执行发送
    if args.action == 'test':
        print("发送测试邮件...")
        sender.recipient = args.to or sender.SENDER_EMAIL
        success = sender.send_report('daily', args.date)
    elif args.action == 'weekly':
        success = sender.send_report('weekly', args.date)
    else:  # daily
        success = sender.send_report('daily', args.date)
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
