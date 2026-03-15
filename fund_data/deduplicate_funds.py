#!/usr/bin/env python3
"""
基金去重脚本 - 按主代码合并多类份额
规则：
1. 提取主代码（去掉份额后缀）
2. 同主代码的基金分组
3. 选择代表份额（优先级：A类 > C类 > 其他）
4. 记录合并信息
"""

import pandas as pd
import re
import sys

def extract_master_code(ts_code):
    """提取基金主代码（去掉份额后缀）"""
    # 去掉.OF后缀
    code = ts_code.replace('.OF', '').replace('.SZ', '').replace('.SH', '')
    # 去掉末尾字母（A/B/C/D/E等份额标识）
    master_code = re.sub(r'[A-Z]$', '', code)
    return master_code

def get_share_class(ts_code):
    """获取份额类别"""
    code = ts_code.replace('.OF', '').replace('.SZ', '').replace('.SH', '')
    match = re.search(r'([A-Z])$', code)
    return match.group(1) if match else 'X'  # X表示无明确份额标识

def select_representative(group):
    """
    从同一基金的多份额中选择代表份额
    优先级：A类 > C类 > B类 > D类 > E类 > 其他
    """
    # 定义优先级
    priority = {'A': 1, 'C': 2, 'B': 3, 'D': 4, 'E': 5, 'X': 6}
    
    # 为每个基金添加份额类别和优先级
    group = group.copy()
    group['share_class'] = group['ts_code'].apply(get_share_class)
    group['priority'] = group['share_class'].map(priority)
    
    # 按优先级排序
    group = group.sort_values('priority')
    
    # 选择优先级最高的
    selected = group.iloc[0].copy()
    
    # 添加合并信息
    selected['merged_shares'] = ','.join(group['ts_code'].tolist())
    selected['share_count'] = len(group)
    selected['selected_share'] = selected['share_class']
    
    return selected

def deduplicate_funds(input_file, output_file):
    """主去重函数"""
    print(f"读取数据: {input_file}")
    df = pd.read_csv(input_file)
    print(f"原始基金数量: {len(df)}")
    
    # 提取主代码
    df['master_code'] = df['ts_code'].apply(extract_master_code)
    
    # 按主代码分组并选择代表份额
    print("开始去重...")
    groups = df.groupby('master_code')
    
    deduplicated = []
    merge_stats = {'merged': 0, 'single': 0}
    
    for master_code, group in groups:
        selected = select_representative(group)
        deduplicated.append(selected)
        
        if len(group) > 1:
            merge_stats['merged'] += 1
            print(f"  合并 {master_code}: {group['ts_code'].tolist()} -> 保留 {selected['ts_code']}")
        else:
            merge_stats['single'] += 1
    
    # 创建去重后的DataFrame
    result = pd.DataFrame(deduplicated)
    
    # 删除临时列
    result = result.drop(columns=['master_code', 'share_class', 'priority'], errors='ignore')
    
    # 保存结果
    result.to_csv(output_file, index=False)
    
    print(f"\n去重完成!")
    print(f"  原始基金: {len(df)} 只")
    print(f"  去重后: {len(result)} 只")
    print(f"  合并组数: {merge_stats['merged']} 组")
    print(f"  独立基金: {merge_stats['single']} 只")
    print(f"  输出文件: {output_file}")
    
    return result

if __name__ == '__main__':
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'equity_selected_2025.csv'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'equity_selected_2025_deduplicated.csv'
    
    deduplicate_funds(input_file, output_file)
