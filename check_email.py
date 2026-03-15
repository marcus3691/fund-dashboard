#!/usr/bin/env python3
"""
检查139邮箱收件箱
"""
import imaplib
import email
from email.header import decode_header
import ssl

# 邮箱配置
IMAP_SERVER = "imap.139.com"
IMAP_PORT = 993
EMAIL = "18817205079@139.com"
PASSWORD = "ab96ed0b496fd94f6e00"

def decode_str(s):
    """解码邮件主题/发件人"""
    if s is None:
        return ""
    value, charset = decode_header(s)[0]
    if isinstance(value, bytes):
        try:
            return value.decode(charset or 'utf-8', errors='ignore')
        except:
            return value.decode('utf-8', errors='ignore')
    return value

def check_email():
    try:
        # 连接IMAP服务器
        print(f"正在连接 {IMAP_SERVER}:{IMAP_PORT}...")
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        
        # 登录
        print(f"正在登录 {EMAIL}...")
        mail.login(EMAIL, PASSWORD)
        print("登录成功！\n")
        
        # 选择收件箱
        mail.select("inbox")
        
        # 搜索所有邮件（最近10封）
        status, messages = mail.search(None, "ALL")
        if status != "OK":
            print("搜索邮件失败")
            return
        
        message_ids = messages[0].split()
        total = len(message_ids)
        print(f"收件箱共有 {total} 封邮件\n")
        
        # 查看最新10封
        recent_ids = message_ids[-10:] if total > 10 else message_ids
        recent_ids.reverse()  # 最新的在前
        
        print("=" * 60)
        print("最新邮件列表:")
        print("=" * 60)
        
        attachments = []
        
        for idx, msg_id in enumerate(recent_ids, 1):
            status, msg_data = mail.fetch(msg_id, "(RFC822)")
            if status != "OK":
                continue
            
            msg = email.message_from_bytes(msg_data[0][1])
            
            # 获取主题
            subject = decode_str(msg.get("Subject", ""))
            
            # 获取发件人
            from_addr = decode_str(msg.get("From", ""))
            
            # 获取日期
            date = msg.get("Date", "")
            
            # 检查是否有附件
            has_attach = False
            attach_names = []
            
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_disposition() == "attachment":
                        has_attach = True
                        filename = decode_str(part.get_filename())
                        attach_names.append(filename)
                        attachments.append({
                            'msg_id': msg_id,
                            'subject': subject,
                            'filename': filename,
                            'part': part
                        })
            
            attach_info = f" [附件: {', '.join(attach_names)}]" if has_attach else ""
            
            print(f"\n{idx}. 主题: {subject}")
            print(f"   发件人: {from_addr}")
            print(f"   日期: {date}{attach_info}")
        
        print("\n" + "=" * 60)
        
        # 如果有附件，询问是否下载
        if attachments:
            print(f"\n发现 {len(attachments)} 个附件")
            for att in attachments:
                print(f"  - {att['filename']} (来自: {att['subject']})")
                
                # 下载PDF附件
                if att['filename'].lower().endswith('.pdf'):
                    save_path = f"/root/.openclaw/workspace/{att['filename']}"
                    payload = att['part'].get_payload(decode=True)
                    with open(save_path, 'wb') as f:
                        f.write(payload)
                    print(f"    ↓ 已下载到: {save_path}")
        else:
            print("\n没有找到带附件的邮件")
        
        mail.logout()
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_email()
