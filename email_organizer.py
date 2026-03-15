#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
139邮箱邮件整理工具 - POP3版本
"""
import poplib
import email
from email.header import decode_header
import socket

def decode_str(s):
    """解码邮件头"""
    if s is None:
        return ""
    try:
        value, charset = decode_header(s)[0]
        if isinstance(value, bytes):
            try:
                return value.decode(charset or 'utf-8')
            except:
                return value.decode('gbk', errors='ignore')
        return value
    except:
        return str(s)

def fetch_emails_pop3(email_addr, password, limit=30):
    """使用POP3获取邮件"""
    socket.setdefaulttimeout(15)
    pop = None
    
    try:
        print("正在连接 139 邮箱...")
        pop = poplib.POP3_SSL('pop.139.com', 995)
        
        print("正在登录...")
        pop.user(email_addr)
        pop.pass_(password)
        
        count, size = pop.stat()
        print(f"📧 邮箱中共有 {count} 封邮件\n")
        
        emails = []
        # 获取最近的几封邮件
        start = max(1, count - limit + 1)
        
        for i in range(count, start - 1, -1):
            try:
                # 只获取邮件头信息
                response, lines, octets = pop.top(i, 0)
                msg_content = b'\n'.join(lines)
                msg = email.message_from_bytes(msg_content)
                
                subject = decode_str(msg["Subject"]) or "(无主题)"
                from_addr = decode_str(msg["From"]) or "未知发件人"
                date_str = msg["Date"] or "未知时间"
                
                emails.append({
                    "id": count - i + 1,
                    "subject": subject,
                    "from": from_addr,
                    "date": date_str
                })
                
                if len(emails) >= limit:
                    break
                    
            except Exception as e:
                continue
        
        return emails, count
        
    except Exception as e:
        print(f"错误: {e}")
        return [], 0
    finally:
        if pop:
            try:
                pop.quit()
            except:
                pass
        socket.setdefaulttimeout(None)

def categorize_emails(emails):
    """对邮件进行简单分类"""
    categories = {
        "推广/营销": [],
        "通知/提醒": [],
        "社交/通讯": [],
        "工作/商务": [],
        "其他": []
    }
    
    promo_keywords = ["优惠", "促销", "折扣", "活动", "限时", "免费", "抽奖", "红包", "优惠券", "sale", "discount", "promo", "offer", "京东", "淘宝", "天猫", "拼多多", "美团", "饿了么", "唯品会", "苏宁"]
    notify_keywords = ["验证码", "通知", "提醒", "确认", "成功", "失败", "账单", "支付", "code", "verification", "alert", "notification", "银行", "支付宝", "微信", "交易", "订单", "物流", "快递"]
    social_keywords = ["微信", "微博", "好友", "关注", "评论", "私信", "邀请", "friend", "follow", "social", "QQ", "抖音", "小红书"]
    work_keywords = ["工作", "项目", "会议", "报告", "合同", "客户", "业务", "work", "project", "meeting", "job", "office", "简历", "招聘", "面试", "offer"]
    
    for email in emails:
        subject_lower = email["subject"].lower()
        from_lower = email["from"].lower()
        text_to_check = subject_lower + " " + from_lower
        
        if any(kw in text_to_check for kw in promo_keywords):
            categories["推广/营销"].append(email)
        elif any(kw in text_to_check for kw in notify_keywords):
            categories["通知/提醒"].append(email)
        elif any(kw in text_to_check for kw in social_keywords):
            categories["社交/通讯"].append(email)
        elif any(kw in text_to_check for kw in work_keywords):
            categories["工作/商务"].append(email)
        else:
            categories["其他"].append(email)
    
    return categories

if __name__ == "__main__":
    EMAIL = "18817205079@139.com"
    PASSWORD = "ab96ed0b496fd94f6e00"
    
    print("=" * 60)
    print("📧 139邮箱邮件整理")
    print("=" * 60 + "\n")
    
    emails, total = fetch_emails_pop3(EMAIL, PASSWORD, limit=30)
    
    if not emails:
        print("\n未能获取邮件")
        exit(1)
    
    # 分类
    categories = categorize_emails(emails)
    
    # 输出整理结果
    print("=" * 60)
    print("📊 邮件分类整理结果")
    print("=" * 60)
    
    for category, items in categories.items():
        if items:
            print(f"\n【{category}】({len(items)} 封)")
            print("-" * 50)
            for email in items[:10]:  # 每类最多显示10封
                print(f"  {email['id']:2}. {email['subject'][:45]}")
                print(f"      来自: {email['from'][:35]}")
            if len(items) > 10:
                print(f"      ... 还有 {len(items) - 10} 封")
    
    # 统计
    print("\n" + "=" * 60)
    print("📈 统计概览")
    print("=" * 60)
    for category, items in categories.items():
        count = len(items)
        if count > 0:
            bar = "█" * min(count, 20)
            print(f"  {category:12} {bar} {count} 封")
    
    print(f"\n已分析: {len(emails)} 封 | 邮箱总计: {total} 封")
    print("=" * 60)