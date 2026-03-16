#!/usr/bin/env python3
"""
基金数据自动更新邮件推送模块
发送结果到139邮箱
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

class FundReportEmailSender:
    """基金报告邮件发送器"""
    
    # 139邮箱配置
    SMTP_SERVER = 'smtp.139.com'
    SMTP_PORT = 465
    SENDER_EMAIL = '18817205079@139.com'
    AUTH_CODE = 'ab96ed0b496fd94f6e00'
    RECIPIENT_EMAIL = '18817205079@139.com'  # 发送给自己
    
    def __init__(self):
        self.workspace = '/root/.openclaw/workspace'
    
    def create_email(self, subject, body, attachments=None):
        """
        创建邮件
        
        Args:
            subject: 邮件主题
            body: 邮件正文
            attachments: 附件列表 [(文件名, 文件路径), ...]
        """
        msg = MIMEMultipart()
        msg['From'] = self.SENDER_EMAIL
        msg['To'] = self.RECIPIENT_EMAIL
        msg['Subject'] = subject
        
        # 添加正文
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # 添加附件
        if attachments:
            for filename, filepath in attachments:
                if os.path.exists(filepath):
                    try:
                        with open(filepath, 'rb') as f:
                            attachment = MIMEBase('application', 'octet-stream')
                            attachment.set_payload(f.read())
                        
                        encoders.encode_base64(attachment)
                        attachment.add_header(
                            'Content-Disposition',
                            f'attachment; filename="{filename}"'
                        )
                        msg.attach(attachment)
                        print(f"  ✅ 附件已添加: {filename}")
                    except Exception as e:
                        print(f"  ⚠️ 添加附件失败 {filename}: {e}")
        
        return msg
    
    def send_email(self, subject, body, attachments=None):
        """
        发送邮件
        
        Args:
            subject: 邮件主题
            body: 邮件正文
            attachments: 附件列表
            
        Returns:
            bool: 是否发送成功
        """
        print(f"\n📧 准备发送邮件...")
        print(f"  收件人: {self.RECIPIENT_EMAIL}")
        print(f"  主题: {subject}")
        
        try:
            # 创建邮件
            msg = self.create_email(subject, body, attachments)
            
            # 连接SMTP服务器
            print(f"  连接服务器: {self.SMTP_SERVER}:{self.SMTP_PORT}")
            with smtplib.SMTP_SSL(self.SMTP_SERVER, self.SMTP_PORT) as server:
                print(f"  登录中...")
                server.login(self.SENDER_EMAIL, self.AUTH_CODE)
                
                print(f"  发送邮件...")
                server.sendmail(
                    self.SENDER_EMAIL,
                    [self.RECIPIENT_EMAIL],
                    msg.as_string()
                )
            
            print(f"  ✅ 邮件发送成功!")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"  ❌ 认证失败: {e}")
            return False
        except Exception as e:
            print(f"  ❌ 发送失败: {e}")
            return False
    
    def send_daily_report(self):
        """发送每日报告邮件"""
        date_str = datetime.now().strftime('%Y-%m-%d')
        
        # 先生成HTML报告
        try:
            from fund_report_html_generator import FundReportHtmlGenerator
            generator = FundReportHtmlGenerator()
            html_report = generator.generate_full_report()
            print(f"  ✅ HTML报告已生成")
        except Exception as e:
            print(f"  ⚠️ HTML生成失败: {e}")
            html_report = None
        
        # 读取通知内容
        notification_file = f'{self.workspace}/last_notification.txt'
        if not os.path.exists(notification_file):
            print(f"⚠️ 通知文件不存在: {notification_file}")
            return False
        
        with open(notification_file, 'r', encoding='utf-8') as f:
            body = f.read()
        
        # 准备附件 - 使用HTML格式
        attachments = []
        
        # 1. HTML完整报告（主要附件）
        if html_report and os.path.exists(html_report):
            attachments.append(('fund_daily_report.html', html_report))
        
        # 2. 执行日志（文本格式）
        log_file = f'{self.workspace}/auto_run_{datetime.now().strftime("%Y%m%d")}.log'
        if os.path.exists(log_file):
            attachments.append(('execution_log.txt', log_file))
        
        # 发送邮件
        subject = f'📊 基金数据日报 - {date_str}'
        success = self.send_email(subject, body, attachments)
        
        return success


def main():
    """测试邮件发送"""
    sender = FundReportEmailSender()
    
    # 检查是否有通知内容
    notification_file = '/root/.openclaw/workspace/last_notification.txt'
    if os.path.exists(notification_file):
        print("="*60)
        print("发送基金数据日报邮件")
        print("="*60)
        success = sender.send_daily_report()
        
        if success:
            print("\n✅ 日报邮件发送完成")
        else:
            print("\n❌ 日报邮件发送失败")
    else:
        print(f"⚠️ 未找到通知文件: {notification_file}")
        print("请先运行 fund_auto_runner.py 生成报告")


if __name__ == '__main__':
    main()
