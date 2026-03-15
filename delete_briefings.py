#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
139邮箱 - 删除重复财经简报 - 快速版
"""
import poplib
import email
from email.header import decode_header
import socket
import re

def decode_str(s):
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

def delete_briefings(email_addr, password):
    socket.setdefaulttimeout(15)
    pop = None
    
    try:
        print("连接 139 邮箱...")
        pop = poplib.POP3_SSL('pop.139.com', 995)
        pop.user(email_addr)
        pop.pass_(password)
        
        count, size = pop.stat()
        print(f"📧 共 {count} 封邮件\n")
        
        briefing_patterns = ['早间财经简报', '券商观点整合早报', '财经简报']
        to_delete = []
        
        # 只扫描最近50封
        scan_count = 0
        for i in range(count, max(0, count - 50), -1):
            scan_count += 1
            if scan_count % 10 == 0:
                print(f"  已扫描 {scan_count} 封...", end='\r')
            
            try:
                response, lines, octets = pop.top(i, 0)
                msg = email.message_from_bytes(b'\n'.join(lines))
                
                subject = decode_str(msg["Subject"]) or ""
                from_addr = decode_str(msg["From"]) or ""
                
                if email_addr in from_addr and any(p in subject for p in briefing_patterns):
                    to_delete.append({"num": i, "subject": subject[:45]})
            except:
                continue
        
        print(f"\n\n找到 {len(to_delete)} 封财经简报")
        
        if not to_delete:
            return
        
        for item in to_delete[:5]:
            print(f"  • {item['subject']}")
        if len(to_delete) > 5:
            print(f"  ... 还有 {len(to_delete) - 5} 封")
        
        # 执行删除
        print(f"\n正在删除...")
        deleted = 0
        for item in to_delete:
            try:
                pop.dele(item['num'])
                deleted += 1
            except:
                pass
        
        print(f"✓ 已删除 {deleted} 封邮件")
        
    except Exception as e:
        print(f"错误: {e}")
    finally:
        if pop:
            try:
                pop.quit()
            except:
                pass

if __name__ == "__main__":
    delete_briefings("18817205079@139.com", "ab96ed0b496fd94f6e00")