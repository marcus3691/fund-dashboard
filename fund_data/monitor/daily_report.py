#!/usr/bin/env python3
"""
每日舆情汇总报告生成
每日18:00发送汇总邮件
"""

import json
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

# 邮件配置
SMTP_SERVER = "smtp.139.com"
SMTP_PORT = 465
SENDER_EMAIL = "18817205079@139.com"
SENDER_PASSWORD = "ab96ed0f496fd94f6e00"
RECEIVER_EMAIL = "18817205079@139.com"

def send_daily_report(summary_data: dict):
    """发送每日汇总邮件"""
    
    # 创建邮件
    msg = MIMEMultipart('alternative')
    msg['Subject'] = Header(f"【舆情日报】{datetime.now().strftime('%Y年%m月%d日')} 市场舆情汇总", 'utf-8')
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    
    # HTML内容
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', sans-serif; line-height: 1.6; color: #333; }}
            .header {{ background: #1a73e8; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; }}
            .section {{ margin-bottom: 30px; }}
            .section-title {{ font-size: 18px; font-weight: bold; color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 10px; margin-bottom: 15px; }}
            .metric {{ display: inline-block; margin: 10px 20px 10px 0; padding: 15px; background: #f5f5f5; border-radius: 8px; }}
            .metric-value {{ font-size: 24px; font-weight: bold; color: #1a73e8; }}
            .metric-label {{ font-size: 12px; color: #666; }}
            .signal {{ padding: 15px; margin: 10px 0; border-left: 4px solid #1a73e8; background: #f8f9fa; }}
            .signal-high {{ border-left-color: #dc3545; }}
            .signal-medium {{ border-left-color: #ffc107; }}
            .signal-low {{ border-left-color: #28a745; }}
            .footer {{ text-align: center; padding: 20px; color: #999; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 智能舆情监控系统</h1>
            <p>每日市场舆情汇总报告 | {datetime.now().strftime('%Y年%m月%d日')}</p>
        </div>
        
        <div class="content">
            <div class="section">
                <div class="section-title">📈 今日概况</div>
                <div class="metric">
                    <div class="metric-value">{summary_data.get('total_count', 0)}</div>
                    <div class="metric-label">监控新闻数</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{summary_data.get('signals_count', 0)}</div>
                    <div class="metric-label">生成信号数</div>
                </div>
            </div>
            
            <div class="section">
                <div class="section-title">🎯 情感分布</div>
                <p>正面: {summary_data.get('sentiment_distribution', {}).get('positive', 0)} | 
                   负面: {summary_data.get('sentiment_distribution', {}).get('negative', 0)} | 
                   中性: {summary_data.get('sentiment_distribution', {}).get('neutral', 0)}</p>
            </div>
            
            <div class="section">
                <div class="section-title">🔥 热门关键词</div>
                <p>{', '.join([kw[0] for kw in summary_data.get('top_keywords', [])[:10]])}</p>
            </div>
            
            <div class="section">
                <div class="section-title">⚡ 重要信号</div>
    """
    
    # 添加信号
    signals = summary_data.get('signals', [])
    if signals:
        for signal in signals[:5]:  # 最多显示5个
            priority = signal.get('priority', 'low')
            signal_class = f"signal-{priority}"
            html_content += f"""
                <div class="signal {signal_class}">
                    <strong>[{signal.get('type', '未知').upper()}]</strong> 
                    {signal.get('trigger', '')}<br>
                    <small>建议: {signal.get('action', '')}</small>
                </div>
            """
    else:
        html_content += "<p>今日未生成重要信号</p>"
    
    html_content += """
            </div>
        </div>
        
        <div class="footer">
            <p>本报告由智能舆情监控系统自动生成</p>
            <p>如需更多信息，请访问ETF策略库</p>
        </div>
    </body>
    </html>
    """
    
    # 添加HTML内容
    msg.attach(MIMEText(html_content, 'html', 'utf-8'))
    
    try:
        # 发送邮件
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        
        print(f"✅ 每日汇总邮件发送成功！")
        return True
        
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")
        return False

def generate_and_send_report():
    """生成并发送报告"""
    import sys
    sys.path.insert(0, '/root/.openclaw/workspace')
    from fund_data.monitor.database import news_db
    
    # 获取今日汇总
    summary = news_db.get_daily_summary()
    
    # 获取未处理新闻生成的信号
    unprocessed = news_db.find_unprocessed()
    signals = []
    for news in unprocessed:
        signals.extend(news.get('extracted_signals', []))
    
    summary['signals'] = signals
    summary['signals_count'] = len(signals)
    
    # 发送邮件
    send_daily_report(summary)

if __name__ == "__main__":
    generate_and_send_report()
