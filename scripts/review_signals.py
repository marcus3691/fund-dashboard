#!/usr/bin/env python3
"""
ETF信号人工复核与发布工具
用于将 pending_signals 审核后发布到 active_signals
"""

import json
import os
import sys
from datetime import datetime

def load_signals():
    """加载信号数据"""
    signals_file = os.path.join(os.path.dirname(__file__), '..', 'etf_signals.json')
    with open(signals_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_signals(data):
    """保存信号数据"""
    signals_file = os.path.join(os.path.dirname(__file__), '..', 'etf_signals.json')
    with open(signals_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def list_pending_signals():
    """列出待复核信号"""
    data = load_signals()
    pending = data.get('pending_signals', [])
    
    if not pending:
        print("\n✅ 当前没有待复核信号")
        return []
    
    print(f"\n{'='*80}")
    print(f"待复核信号列表 (共{len(pending)}个)")
    print(f"{'='*80}\n")
    
    for i, signal in enumerate(pending, 1):
        print(f"[{i}] {signal['id']}")
        print(f"    类型: {signal['type']} | 优先级: {signal['priority']}")
        print(f"    事件: {signal['trigger']['event']}")
        print(f"    建议: {signal['action']['direction']} {signal['action']['target']} {signal['action']['suggested_weight']}%")
        print(f"    来源: {signal['trigger']['source']}")
        print(f"    抓取时间: {signal['timestamp']}")
        print()
    
    return pending

def review_signal(signal_id, action, reviewer="manual"):
    """
    复核单个信号
    action: approve / reject / modify
    """
    data = load_signals()
    pending = data.get('pending_signals', [])
    
    # 查找信号
    signal = None
    for s in pending:
        if s['id'] == signal_id:
            signal = s
            break
    
    if not signal:
        print(f"❌ 未找到信号: {signal_id}")
        return False
    
    if action == "approve":
        # 批准发布
        signal['status'] = 'active'
        signal['review_status'] = 'approved'
        signal['reviewer'] = reviewer
        signal['review_time'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        
        # 移动到活跃信号
        data['active_signals'].append(signal)
        data['pending_signals'].remove(signal)
        
        save_signals(data)
        print(f"✅ 信号已批准并发布: {signal_id}")
        return True
        
    elif action == "reject":
        # 拒绝
        signal['status'] = 'rejected'
        signal['review_status'] = 'rejected'
        signal['reviewer'] = reviewer
        signal['review_time'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        
        data['pending_signals'].remove(signal)
        save_signals(data)
        print(f"❌ 信号已拒绝: {signal_id}")
        return True
        
    elif action == "modify":
        # 修改后发布（需要交互式输入）
        print(f"\n📝 修改信号: {signal_id}")
        print(f"当前建议: {signal['action']['direction']} {signal['action']['suggested_weight']}%")
        
        # 这里可以添加交互式修改逻辑
        # 简化版本：直接批准
        return review_signal(signal_id, "approve", reviewer)
    
    else:
        print(f"❌ 未知操作: {action}")
        return False

def review_all_pending():
    """交互式复核所有待处理信号"""
    pending = list_pending_signals()
    
    if not pending:
        return
    
    print("\n复核选项:")
    print("  a - 批准全部")
    print("  r - 拒绝全部")
    print("  数字 - 复核单个 (如: 1)")
    print("  q - 退出")
    print()
    
    choice = input("请选择操作: ").strip().lower()
    
    if choice == 'a':
        confirm = input("确认批准全部? (y/n): ").strip().lower()
        if confirm == 'y':
            for signal in pending[:]:
                review_signal(signal['id'], 'approve')
    
    elif choice == 'r':
        confirm = input("确认拒绝全部? (y/n): ").strip().lower()
        if confirm == 'y':
            for signal in pending[:]:
                review_signal(signal['id'], 'reject')
    
    elif choice == 'q':
        print("退出复核")
    
    elif choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(pending):
            signal = pending[idx]
            print(f"\n正在复核: {signal['id']}")
            print(f"事件: {signal['trigger']['event']}")
            print(f"逻辑: {signal['action']['rationale']}")
            
            action = input("操作 (a-批准/r-拒绝/m-修改): ").strip().lower()
            if action in ['a', 'r', 'm']:
                review_signal(signal['id'], 
                              'approve' if action == 'a' else 'reject' if action == 'r' else 'modify')
        else:
            print("❌ 无效序号")
    
    else:
        print("❌ 无效选项")

def expire_old_signals():
    """清理过期信号"""
    data = load_signals()
    now = datetime.now()
    
    # 清理过期的活跃信号
    active = data.get('active_signals', [])
    expired = []
    
    for signal in active[:]:
        expire_time = datetime.fromisoformat(signal.get('expires_at', '2099-12-31'))
        if now > expire_time:
            expired.append(signal)
            active.remove(signal)
    
    if expired:
        save_signals(data)
        print(f"🗑️ 已清理 {len(expired)} 个过期信号")
    else:
        print("✅ 没有过期信号")

def show_stats():
    """显示信号统计"""
    data = load_signals()
    
    active = len(data.get('active_signals', []))
    pending = len(data.get('pending_signals', []))
    
    print(f"\n{'='*60}")
    print(f"信号统计")
    print(f"{'='*60}")
    print(f"活跃信号: {active}个")
    print(f"待复核:   {pending}个")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\nETF信号复核工具")
        print("\n用法:")
        print("  python review_signals.py list      # 列出待复核信号")
        print("  python review_signals.py review    # 交互式复核")
        print("  python review_signals.py approve ID  # 批准指定信号")
        print("  python review_signals.py reject ID   # 拒绝指定信号")
        print("  python review_signals.py expire    # 清理过期信号")
        print("  python review_signals.py stats     # 显示统计")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "list":
        list_pending_signals()
    elif cmd == "review":
        review_all_pending()
    elif cmd == "approve" and len(sys.argv) > 2:
        review_signal(sys.argv[2], "approve")
    elif cmd == "reject" and len(sys.argv) > 2:
        review_signal(sys.argv[2], "reject")
    elif cmd == "expire":
        expire_old_signals()
    elif cmd == "stats":
        show_stats()
    else:
        print(f"❌ 未知命令: {cmd}")
