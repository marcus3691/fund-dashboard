#!/usr/bin/env python3
"""
ETF调仓信号邮件通知系统
发送信号推送到139邮箱
"""

import json
import smtplib
import os
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

# 139邮箱配置
SMTP_SERVER = "smtp.139.com"
SMTP_PORT = 465
SENDER_EMAIL = "18817205079@139.com"
# 使用授权码（不是登录密码）
# 用户需要从139邮箱设置中获取授权码
SENDER_PASSWORD = os.environ.get('EMAIL_AUTH_CODE', 'your_auth_code_here')
RECIPIENT_EMAIL = "18817205079@139.com"

def send_signal_email(signal, test_mode=False):
    """
    发送调仓信号邮件
    """
    # 构建邮件内容
    subject = f"【ETF策略信号】{signal['type']} - {signal['action']['direction']} {signal['priority']}"
    
    # HTML格式的邮件正文
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; background: #f5f5f5; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
            .header {{ background: {'#f85149' if signal['priority'] == 'high' else '#d29922' if signal['priority'] == 'medium' else '#3fb950'}; color: white; padding: 20px; }}
            .header h1 {{ margin: 0; font-size: 20px; }}
            .header .time {{ font-size: 12px; opacity: 0.9; margin-top: 8px; }}
            .content {{ padding: 20px; }}
            .section {{ margin-bottom: 20px; }}
            .section h3 {{ color: #333; font-size: 14px; margin-bottom: 10px; border-left: 3px solid #58a6ff; padding-left: 10px; }}
            .section p {{ color: #666; font-size: 13px; line-height: 1.6; margin: 5px 0; }}
            .highlight {{ background: #fff3cd; padding: 2px 6px; border-radius: 3px; font-weight: bold; color: #856404; }}
            .action-box {{ background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 6px; padding: 15px; margin: 15px 0; }}
            .action-box .label {{ color: #8b949e; font-size: 12px; margin-bottom: 5px; }}
            .action-box .value {{ color: #333; font-size: 16px; font-weight: bold; }}
            .footer {{ background: #f8f9fa; padding: 15px 20px; font-size: 11px; color: #8b949e; text-align: center; }}
            .badge {{ display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 11px; margin-left: 10px; }}
            .badge-high {{ background: #f85149; color: white; }}
            .badge-medium {{ background: #d29922; color: white; }}
            .badge-low {{ background: #3fb950; color: white; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>ETF策略调仓信号</h1>
                <div class="time">信号时间: {signal['timestamp']} <span class="badge badge-{signal['priority']}">{signal['priority'].upper()}</span></div>
            </div>
            <div class="content">
                <div class="section">
                    <h3>📍 触发事件</h3>
                    <p><strong>{signal['trigger']['event']}</strong></p>
                    <p>当前值: <span class="highlight">{signal['trigger']['current_value']}</span></p>
                    <p>触发阈值: {signal['trigger']['threshold']}</p>
                    <p>数据来源: {signal['trigger']['source']}</p>
                </div>
                
                <div class="action-box">
                    <div style="display: flex; justify-content: space-between;">
                        <div>
                            <div class="label">建议操作</div>
                            <div class="value" style="color: {'#3fb950' if signal['action']['direction'] == '加仓' else '#f85149'};">
                                {signal['action']['direction']} {signal['action']['suggested_weight']}%
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <div class="label">目标ETF</div>
                            <div class="value">{signal['action']['target']}</div>
                        </div>
                    </div>
                </div>
                
                <div class="section">
                    <h3>💡 调仓逻辑</h3>
                    <p>{signal['action']['rationale']}</p>
                </div>
                
                <div class="section">
                    <h3>⚠️ 风险提示</h3>
                    <p>1. 本信号仅供参考，不构成投资建议</p>
                    <p>2. 请根据自身风险承受能力决策</p>
                    <p>3. 市场有风险，投资需谨慎</p>
                </div>
            </div>
            <div class="footer">
                <p>基金产品库智能分析系统 - ETF策略库 V2.0</p>
                <p>信号ID: {signal['id']} | 有效期至: {signal.get('expires_at', '无')}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # 创建邮件对象
    msg = MIMEMultipart('alternative')
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECIPIENT_EMAIL
    
    # 添加HTML内容
    html_part = MIMEText(html_content, 'html', 'utf-8')
    msg.attach(html_part)
    
    try:
        if test_mode:
            print(f"\n{'='*60}")
            print("【测试模式】邮件内容预览：")
            print(f"{'='*60}")
            print(f"收件人: {RECIPIENT_EMAIL}")
            print(f"主题: {subject}")
            print(f"{'='*60}\n")
            return True
            
        # 连接SMTP服务器
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        
        # 发送邮件
        server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        server.quit()
        
        print(f"✅ 邮件发送成功！")
        print(f"📧 收件人: {RECIPIENT_EMAIL}")
        print(f"📝 主题: {subject}")
        return True
        
    except Exception as e:
        print(f"❌ 邮件发送失败: {str(e)}")
        return False

def check_and_notify():
    """
    检查信号并发送通知
    """
    # 加载信号数据
    signals_file = os.path.join(os.path.dirname(__file__), '..', 'etf_signals.json')
    
    with open(signals_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    active_signals = data.get('active_signals', [])
    
    if not active_signals:
        print("当前无活跃信号")
        return
    
    print(f"发现 {len(active_signals)} 个活跃信号\n")
    
    for signal in active_signals:
        # 只发送高优先级信号
        if signal['priority'] in ['high', 'critical']:
            print(f"处理信号: {signal['id']} - {signal['trigger']['event']}")
            send_signal_email(signal)
            print()

def send_daily_digest():
    """
    发送每日信号汇总
    """
    signals_file = os.path.join(os.path.dirname(__file__), '..', 'etf_signals.json')
    
    with open(signals_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    active_signals = data.get('active_signals', [])
    pending_signals = data.get('pending_signals', [])
    
    subject = f"【ETF策略日报】{datetime.now().strftime('%Y-%m-%d')} 信号汇总"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; background: #f5f5f5; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
            .header {{ background: #58a6ff; color: white; padding: 20px; }}
            .header h1 {{ margin: 0; font-size: 20px; }}
            .content {{ padding: 20px; }}
            .summary {{ background: #f8f9fa; padding: 15px; border-radius: 6px; margin-bottom: 20px; }}
            .summary-item {{ display: flex; justify-content: space-between; margin: 8px 0; }}
            .signal-list {{ margin-top: 20px; }}
            .signal-item {{ border-left: 3px solid #58a6ff; padding-left: 15px; margin: 15px 0; }}
            .signal-item.high {{ border-color: #f85149; }}
            .signal-item.medium {{ border-color: #d29922; }}
            .footer {{ background: #f8f9fa; padding: 15px 20px; font-size: 11px; color: #8b949e; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>ETF策略日报</h1>
                <div style="font-size: 12px; opacity: 0.9; margin-top: 8px;">{datetime.now().strftime('%Y年%m月%d日')}</div>
            </div>
            <div class="content">
                <div class="summary">
                    <div class="summary-item">
                        <span>活跃信号</span>
                        <span style="font-weight: bold; color: #3fb950;">{len(active_signals)}个</span>
                    </div>
                    <div class="summary-item">
                        <span>待复核信号</span>
                        <span style="font-weight: bold; color: #d29922;">{len(pending_signals)}个</span>
                    </div>
                </div>
                
                <div class="signal-list">
                    <h3 style="color: #333; font-size: 16px; margin-bottom: 15px;">📍 活跃信号详情</h3>
                    {''.join([f"""
                    <div class="signal-item {s['priority']}">
                        <div style="font-weight: bold; color: #333;">{s['trigger']['event']}</div>
                        <div style="font-size: 12px; color: #666; margin-top: 5px;">
                            {s['action']['direction']} {s['action']['target']} {s['action']['suggested_weight']}%
                        </div>
                    </div>
                    """ for s in active_signals[:5]])}
                </div>
            </div>
            <div class="footer">
                <p>基金产品库智能分析系统</p>
                <p>查看完整信号请访问：https://marcus3691.github.io/fund-dashboard/etf_strategy.html</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECIPIENT_EMAIL
    msg.attach(MIMEText(html_content, 'html', 'utf-8'))
    
    try:
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        server.quit()
        print(f"✅ 日报发送成功！")
        return True
    except Exception as e:
        print(f"❌ 日报发送失败: {str(e)}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--daily":
        # 发送日报
        send_daily_digest()
    elif len(sys.argv) > 1 and sys.argv[1] == "--test":
        # 测试模式
        test_signal = {
            "id": "TEST_001",
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "type": "test",
            "priority": "high",
            "trigger": {
                "event": "测试信号",
                "threshold": "测试阈值",
                "current_value": "测试值",
                "source": "测试来源"
            },
            "action": {
                "layer": "core",
                "target": "515220.SH",
                "direction": "加仓",
                "suggested_weight": 5,
                "rationale": "这是测试邮件，验证邮件发送功能是否正常"
            },
            "expires_at": "2026-12-31T23:59:59"
        }
        send_signal_email(test_signal, test_mode=True)
    else:
        # 检查并发送高优先级信号
        check_and_notify()
