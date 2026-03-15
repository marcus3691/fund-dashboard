import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# 邮件配置
smtp_server = "smtp.139.com"
smtp_port = 465
sender_email = "18817205079@139.com"
sender_password = "ab96ed0b496fd94f6e00"
receiver_email = "18817205079@139.com"

# 创建邮件
msg = MIMEMultipart()
msg['From'] = sender_email
msg['To'] = receiver_email
msg['Subject'] = "基金策略增强版报告 - 2026.03.13 (带附件)"

# 邮件正文
body = """您好，

附件是基金产品库策略增强版报告（PDF格式）。

报告内容：
1. TOP50基金会议纪要方向匹配度排名
2. 能源/有色/化工方向持仓筛选  
3. 新增10只基金持仓数据
4. 投资建议标签

核心发现：
- 化工板块最匹配（宏利40.8%、中信保诚40.6%）
- 传统能源银华甄选40.4%
- 永赢价值发现质量分96.2但匹配度仅10.4%

如有问题请随时联系。
"""

msg.attach(MIMEText(body, 'plain', 'utf-8'))

# 添加附件
pdf_path = "/root/.openclaw/workspace/fund_data/analysis/基金策略增强版报告_20260313.pdf"
filename = "基金策略增强版报告_20260313.pdf"

with open(pdf_path, "rb") as attachment:
    part = MIMEBase("application", "pdf")
    part.set_payload(attachment.read())

encoders.encode_base64(part)
part.add_header(
    "Content-Disposition",
    f'attachment; filename="{filename}"',
)
msg.attach(part)

# 发送邮件
try:
    server = smtplib.SMTP_SSL(smtp_server, smtp_port)
    server.login(sender_email, sender_password)
    server.send_message(msg)
    server.quit()
    print("✅ 邮件发送成功！")
    print(f"   文件大小: {os.path.getsize(pdf_path)} bytes")
except Exception as e:
    print(f"❌ 发送失败: {e}")
