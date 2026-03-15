#!/usr/bin/env python3
"""
基金产品库重新筛选任务 V4.2
- 修正季度归属计算（根据end_date而非quarter字段）
- 加入灵活配置型基金（平均股票仓位>60%）并入混合型-偏股
- 重新执行三级筛选
"""

import pandas as pd
import numpy as np
import tushare as ts
import os
import glob
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Tushare Token
TS_TOKEN = '33996190080200cd63a01732ad443c390d9d580913ec938d4e1d704d'

# 初始化Tushare
pro = ts.pro_api(TS_TOKEN)

# 文件路径
WORKSPACE = '/root/.openclaw/workspace/fund_data'
HOLDINGS_DIR = os.path.join(WORKSPACE, 'holdings')
INPUT_FILE = os.path.join(WORKSPACE, 'fund_screening_all.csv')

# 输出文件
CORE_LIBRARY_V4 = os.path.join(WORKSPACE, 'fund_core_library_v4.csv')
WATCH_LIBRARY_V4 = os.path.join(WORKSPACE, 'fund_watch_library_v4.csv')
BACKUP_LIBRARY_V4 = os.path.join(WORKSPACE, 'fund_backup_library_v4.csv')
COMPARISON_REPORT = os.path.join(WORKSPACE, 'screening_comparison_report.txt')

def load_fund_data():
    """加载基金筛选数据"""
    print("加载基金筛选数据...")
    df = pd.read_csv(INPUT_FILE, encoding='utf-8-sig')
    print(f"加载了 {len(df)} 条基金记录")
    return df

def get_quarter_from_end_date(end_date):
    """根据end_date判断所属季度"""
    try:
        # 处理整数格式的日期 (如 20240331)
        if isinstance(end_date, (int, np.integer)):
            date_str = str(int(end_date))
        else:
            date_str = str(end_date)
        
        year = int(date_str[:4])
        month = int(date_str[4:6])
        
        if month in [1, 2, 3]:
            return f"{year}Q1"
        elif month in [4, 5, 6]:
            return f"{year}Q2"
        elif month in [7, 8, 9]:
            return f"{year}Q3"
        else:  # 10, 11, 12
            return f"{year}Q4"
    except:
        return None

def calculate_stock_ratio_from_holdings(ts_code):
    """
    从持仓数据计算基金的股票仓位
    根据end_date判断季度归属，取每个季度最新的数据
    返回近4个季度的平均股票仓位
    """
    holdings_file = os.path.join(HOLDINGS_DIR, f"{ts_code}_holdings.csv")
    
    if not os.path.exists(holdings_file):
        return None, 0
    
    try:
        df = pd.read_csv(holdings_file, encoding='utf-8-sig')
        if len(df) == 0:
            return None, 0
        
        # 根据end_date计算真实季度
        df['true_quarter'] = df['end_date'].apply(get_quarter_from_end_date)
        
        # 按季度分组，计算每个季度的股票仓位
        quarters = df['true_quarter'].unique()
        quarter_ratios = []
        
        for q in quarters:
            if q is None:
                continue
            q_df = df[df['true_quarter'] == q].copy()
            
            # 对于每个季度，取最新end_date的数据（通常是该季度末）
            latest_end_date = q_df['end_date'].max()
            q_df = q_df[q_df['end_date'] == latest_end_date]
            
            # 计算该季度的股票仓位（stk_mkv_ratio 的总和）
            # stk_mkv_ratio 单位是%，已经直接可用
            total_ratio = q_df['stk_mkv_ratio'].sum()
            quarter_ratios.append({
                'quarter': q,
                'stock_ratio': total_ratio,
                'end_date': latest_end_date,
                'stock_count': len(q_df)
            })
        
        if len(quarter_ratios) == 0:
            return None, 0
        
        quarter_df = pd.DataFrame(quarter_ratios)
        
        # 获取最近4个季度的数据
        def quarter_sort_key(q):
            try:
                year, q_num = q.split('Q')
                return int(year) * 10 + int(q_num)
            except:
                return 0
        
        quarter_df['sort_key'] = quarter_df['quarter'].apply(quarter_sort_key)
        quarter_df = quarter_df.sort_values('sort_key', ascending=False)
        
        # 取最近4个季度
        recent_4q = quarter_df.head(4)
        avg_ratio = recent_4q['stock_ratio'].mean()
        
        # 调试信息
        if len(recent_4q) > 0:
            print(f"  {ts_code}: 近{len(recent_4q)}季度仓位: {recent_4q['stock_ratio'].tolist()}, 平均={avg_ratio:.1f}%")
        
        return avg_ratio, len(recent_4q)
    
    except Exception as e:
        print(f"计算 {ts_code} 股票仓位时出错: {e}")
        import traceback
        traceback.print_exc()
        return None, 0

def process_flexible_config_funds(df):
    """
    处理灵活配置型基金：
    1. 找出所有灵活配置型基金
    2. 计算股票仓位
    3. 将平均仓位>60%的基金类别改为"混合型-偏股"
    """
    print("\n" + "="*80)
    print("【步骤1-3】处理灵活配置型基金")
    print("="*80)
    
    # 找出灵活配置型基金
    flexible_funds = df[df['invest_type'] == '灵活配置型'].copy()
    print(f"找到 {len(flexible_funds)} 只灵活配置型基金")
    
    if len(flexible_funds) == 0:
        print("没有找到灵活配置型基金")
        return df, pd.DataFrame()
    
    # 首先检查哪些基金有持仓数据
    available_holdings = []
    for idx, row in flexible_funds.iterrows():
        ts_code = row['ts_code']
        holdings_file = os.path.join(HOLDINGS_DIR, f"{ts_code}_holdings.csv")
        if os.path.exists(holdings_file):
            available_holdings.append(ts_code)
    
    print(f"其中 {len(available_holdings)} 只基金有持仓数据")
    
    # 计算每只股票仓位
    stock_ratios = []
    processed_count = 0
    
    for idx, row in flexible_funds.iterrows():
        ts_code = row['ts_code']
        avg_ratio, q_count = calculate_stock_ratio_from_holdings(ts_code)
        
        stock_ratios.append({
            'ts_code': ts_code,
            'name': row['name'],
            'original_category': row['category'],
            'avg_stock_ratio': avg_ratio,
            'quarters_count': q_count
        })
        
        processed_count += 1
        if processed_count % 50 == 0:
            print(f"  已处理 {processed_count}/{len(flexible_funds)} 只基金...")
    
    ratio_df = pd.DataFrame(stock_ratios)
    
    # 统计
    valid_ratios = ratio_df[ratio_df['avg_stock_ratio'].notna()]
    print(f"\n成功计算 {len(valid_ratios)}/{len(flexible_funds)} 只基金的股票仓位")
    
    if len(valid_ratios) > 0:
        print(f"股票仓位统计:")
        print(f"  均值: {valid_ratios['avg_stock_ratio'].mean():.2f}%")
        print(f"  中位数: {valid_ratios['avg_stock_ratio'].median():.2f}%")
        print(f"  最大值: {valid_ratios['avg_stock_ratio'].max():.2f}%")
        print(f"  最小值: {valid_ratios['avg_stock_ratio'].min():.2f}%")
        
        # 显示所有有数据的基金
        print(f"\n所有有持仓数据的灵活配置型基金:")
        for idx, row in valid_ratios.sort_values('avg_stock_ratio', ascending=False).iterrows():
            print(f"  {row['ts_code']} {row['name']}: {row['avg_stock_ratio']:.1f}%")
    
    # 筛选平均仓位>60%的基金
    high_stock_ratio = ratio_df[
        (ratio_df['avg_stock_ratio'].notna()) & 
        (ratio_df['avg_stock_ratio'] > 60)
    ].copy()
    
    print(f"\n平均股票仓位>60%的基金: {len(high_stock_ratio)} 只")
    
    # 更新原始数据框中的类别
    df_modified = df.copy()
    modified_count = 0
    
    for idx, row in high_stock_ratio.iterrows():
        ts_code = row['ts_code']
        mask = df_modified['ts_code'] == ts_code
        if mask.any():
            old_category = df_modified.loc[mask, 'category'].values[0]
            df_modified.loc[mask, 'category'] = '混合型-偏股'
            df_modified.loc[mask, 'stock_ratio_4q_avg'] = row['avg_stock_ratio']
            modified_count += 1
            print(f"  更新 {ts_code} {row['name']}: {old_category} -> 混合型-偏股 (仓位{row['avg_stock_ratio']:.1f}%)")
    
    # 为所有灵活配置型基金添加股票仓位列
    for idx, row in ratio_df.iterrows():
        ts_code = row['ts_code']
        mask = df_modified['ts_code'] == ts_code
        if mask.any() and pd.notna(row['avg_stock_ratio']):
            df_modified.loc[mask, 'stock_ratio_4q_avg'] = row['avg_stock_ratio']
    
    print(f"\n已将 {modified_count} 只基金类别更新为'混合型-偏股'")
    
    return df_modified, high_stock_ratio

def classify_scale_status(row):
    """根据规模标准分类"""
    scale = row.get('fund_scale', 10)
    if pd.isna(scale):
        scale = 10
    category = str(row.get('category', ''))
    invest_type = str(row.get('invest_type', ''))
    
    # 判断基金类型
    is_equity = '股票' in invest_type or '主动股票型' in category
    is_mixed_equity = '偏股' in category
    is_flexible_high_stock = invest_type == '灵活配置型' and '混合型-偏股' in category
    
    if is_equity or is_mixed_equity or is_flexible_high_stock:
        # 股票型/混合型-偏股/高仓位灵活配置型标准
        if scale < 1:
            return 'rejected'
        elif 5 <= scale <= 50:
            return 'preferred'
        elif (1 <= scale < 5) or scale > 100:
            return 'watch'
        else:
            return 'normal'  # 50-100亿
    else:
        # 其他类型（包括低仓位灵活配置型）
        if scale < 1:
            return 'rejected'
        elif 5 <= scale <= 50:
            return 'preferred'
        elif (1 <= scale < 5) or scale > 100:
            return 'watch'
        else:
            return 'normal'

def apply_filters(df):
    """应用所有筛选条件"""
    print("\n" + "="*80)
    print("【步骤4】应用筛选条件")
    print("="*80)
    
    # 1. 规模分类
    df['scale_status'] = df.apply(classify_scale_status, axis=1)
    
    # 2. 一票否决
    df['veto'] = df['scale_status'] == 'rejected'
    
    # 3. 业绩筛选（严格条件）
    # 1年前10% 或 6月前20%
    df['pass_performance'] = (df['percentile_1y'] <= 10) | (df['percentile_6m'] <= 20)
    
    # 4. 质量评分 >= 70
    df['pass_quality'] = df['quality_score'] >= 70
    
    # 5. 高质量评分 >= 80
    df['high_quality'] = df['quality_score'] >= 80
    
    # 统计
    print(f"\n筛选统计:")
    print(f"  规模分类: 优选={(df['scale_status'] == 'preferred').sum()}, " +
          f"正常={(df['scale_status'] == 'normal').sum()}, " +
          f"观察={(df['scale_status'] == 'watch').sum()}, " +
          f"否决={(df['scale_status'] == 'rejected').sum()}")
    print(f"  一票否决: {df['veto'].sum()}")
    print(f"  通过业绩筛选(1年前10%或6月前20%): {df['pass_performance'].sum()}")
    print(f"  质量评分>=70: {df['pass_quality'].sum()}")
    print(f"  质量评分>=80: {df['high_quality'].sum()}")
    
    return df

def classify_library(df):
    """分级入库"""
    print("\n" + "="*80)
    print("【步骤5】分级入库")
    print("="*80)
    
    # 核心库：业绩优秀 + 质量高 + 规模合适 + 无否决
    df['is_core'] = (
        df['pass_performance'] & 
        df['high_quality'] & 
        (~df['veto']) &
        (df['scale_status'].isin(['preferred', 'normal']))
    )
    
    # 观察库：业绩合格 + 质量合格 + 无否决（核心库除外）
    df['is_watch'] = (
        df['pass_quality'] & 
        (~df['is_core']) & 
        (~df['veto'])
    )
    
    # 备选库：业绩或质量有一项合格 + 规模观察 + 无否决
    df['is_backup'] = (
        (df['pass_performance'] | df['pass_quality']) &
        (df['scale_status'] == 'watch') &
        (~df['is_core']) &
        (~df['is_watch']) &
        (~df['veto'])
    )
    
    # 统计
    core_count = df['is_core'].sum()
    watch_count = df['is_watch'].sum()
    backup_count = df['is_backup'].sum()
    veto_count = df['veto'].sum()
    
    print(f"\n入库统计:")
    print(f"  核心库: {core_count}")
    print(f"  观察库: {watch_count}")
    print(f"  备选库: {backup_count}")
    print(f"  一票否决: {veto_count}")
    
    return df

def save_results(df):
    """保存结果"""
    print("\n" + "="*80)
    print("【步骤6】保存结果")
    print("="*80)
    
    # 1. 核心库
    core_df = df[df['is_core']].copy()
    if len(core_df) > 0:
        # 选择输出列
        output_cols = ['ts_code', 'name', 'invest_type', 'category', 'fund_scale', 
                      'scale_status', 'return_3m', 'return_6m', 'return_1y', 
                      'quality_score', 'percentile_6m', 'percentile_1y',
                      'stock_ratio_4q_avg', 'is_core', 'is_watch', 'is_backup']
        
        # 确保所有列都存在
        for col in output_cols:
            if col not in core_df.columns:
                core_df[col] = None
        
        core_df[output_cols].to_csv(CORE_LIBRARY_V4, index=False, encoding='utf-8-sig')
        print(f"核心库 ({len(core_df)}条): {CORE_LIBRARY_V4}")
    else:
        print("核心库为空")
        core_df = pd.DataFrame()
    
    # 2. 观察库
    watch_df = df[df['is_watch']].copy()
    if len(watch_df) > 0:
        output_cols = ['ts_code', 'name', 'invest_type', 'category', 'fund_scale', 
                      'scale_status', 'return_3m', 'return_6m', 'return_1y', 
                      'quality_score', 'percentile_6m', 'percentile_1y',
                      'stock_ratio_4q_avg', 'is_core', 'is_watch', 'is_backup']
        
        for col in output_cols:
            if col not in watch_df.columns:
                watch_df[col] = None
        
        watch_df[output_cols].to_csv(WATCH_LIBRARY_V4, index=False, encoding='utf-8-sig')
        print(f"观察库 ({len(watch_df)}条): {WATCH_LIBRARY_V4}")
    else:
        print("观察库为空")
        watch_df = pd.DataFrame()
    
    # 3. 备选库
    backup_df = df[df['is_backup']].copy()
    if len(backup_df) > 0:
        output_cols = ['ts_code', 'name', 'invest_type', 'category', 'fund_scale', 
                      'scale_status', 'return_3m', 'return_6m', 'return_1y', 
                      'quality_score', 'percentile_6m', 'percentile_1y',
                      'stock_ratio_4q_avg', 'is_core', 'is_watch', 'is_backup']
        
        for col in output_cols:
            if col not in backup_df.columns:
                backup_df[col] = None
        
        backup_df[output_cols].to_csv(BACKUP_LIBRARY_V4, index=False, encoding='utf-8-sig')
        print(f"备选库 ({len(backup_df)}条): {BACKUP_LIBRARY_V4}")
    else:
        print("备选库为空")
        backup_df = pd.DataFrame()
    
    return core_df, watch_df, backup_df

def generate_comparison_report(df, v3_core_file, new_flexible_funds):
    """生成筛选前后对比报告"""
    print("\n" + "="*80)
    print("【生成对比报告】")
    print("="*80)
    
    lines = []
    lines.append("="*80)
    lines.append("基金产品库筛选对比报告 V4.0（含灵活配置型）")
    lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("="*80)
    lines.append("")
    
    # 筛选标准说明
    lines.append("【筛选标准】")
    lines.append("  业绩: 1年前10% 或 6月前20%")
    lines.append("  质量: 核心库≥80, 观察库≥70")
    lines.append("  规模:")
    lines.append("    股票型/混合型-偏股/灵活配置型(仓位>60%): <1亿否决, 5-50亿优选")
    lines.append("  一票否决: 规模<1亿、经理任职<6个月")
    lines.append("")
    
    # V3 版本数据（如果存在）
    v3_core_count = 0
    v3_core_codes = set()
    if v3_core_file and os.path.exists(v3_core_file):
        try:
            v3_df = pd.read_csv(v3_core_file, encoding='utf-8-sig')
            v3_core_count = len(v3_df)
            v3_core_codes = set(v3_df['ts_code'].tolist())
        except Exception as e:
            print(f"读取V3核心库失败: {e}")
            v3_core_count = 0
    
    # V4 版本数据
    v4_core_df = df[df['is_core']].copy()
    v4_core_count = len(v4_core_df)
    v4_core_codes = set(v4_core_df['ts_code'].tolist())
    v4_watch_count = df['is_watch'].sum()
    v4_backup_count = df['is_backup'].sum()
    
    lines.append("【核心库变化对比】")
    lines.append(f"  V3版本核心库: {v3_core_count} 只")
    lines.append(f"  V4版本核心库: {v4_core_count} 只")
    lines.append(f"  变化: {v4_core_count - v3_core_count:+d} 只")
    lines.append("")
    
    # 新增和移除的基金
    added_codes = v4_core_codes - v3_core_codes
    removed_codes = v3_core_codes - v4_core_codes
    
    if added_codes:
        lines.append("【新增入核心库的基金】")
        for code in added_codes:
            fund_row = v4_core_df[v4_core_df['ts_code'] == code]
            if len(fund_row) > 0:
                name = fund_row['name'].values[0]
                cat = fund_row['category'].values[0]
                lines.append(f"  + {code} {name} ({cat})")
        lines.append("")
    
    if removed_codes:
        lines.append("【从核心库移除的基金】")
        for code in removed_codes:
            lines.append(f"  - {code}")
        lines.append("")
    
    # 新增的灵活配置型基金
    lines.append("【新增灵活配置型基金（平均仓位>60%，归入混合型-偏股）】")
    lines.append(f"  符合条件的基金数: {len(new_flexible_funds)} 只")
    
    if len(new_flexible_funds) > 0:
        lines.append("")
        lines.append("  详细列表:")
        for idx, row in new_flexible_funds.iterrows():
            ratio = row['avg_stock_ratio']
            ratio_str = f"{ratio:.1f}%" if pd.notna(ratio) else "N/A"
            lines.append(f"    {row['ts_code']} {row['name']} - 平均仓位: {ratio_str}")
    
    lines.append("")
    
    # 入库统计
    lines.append("【V4版本入库统计】")
    lines.append(f"  总基金数: {len(df)}")
    lines.append(f"  核心库: {v4_core_count}")
    lines.append(f"  观察库: {v4_watch_count}")
    lines.append(f"  备选库: {v4_backup_count}")
    lines.append(f"  一票否决: {df['veto'].sum()}")
    lines.append("")
    
    # 分类别统计
    lines.append("【分类别统计】")
    categories = df['category'].unique()
    for cat in sorted(categories):
        cat_df = df[df['category'] == cat]
        lines.append(f"  {cat}:")
        lines.append(f"    总数: {len(cat_df)}")
        lines.append(f"    核心库: {cat_df['is_core'].sum()}")
        lines.append(f"    观察库: {cat_df['is_watch'].sum()}")
    
    lines.append("")
    
    # V4核心库详细列表
    if len(v4_core_df) > 0:
        lines.append("【V4核心库基金详细列表】")
        for idx, row in v4_core_df.iterrows():
            lines.append(f"  {row['ts_code']} {row['name']}")
            lines.append(f"    类别: {row['category']}")
            lines.append(f"    规模: {row['fund_scale']:.2f}亿 ({row['scale_status']})")
            lines.append(f"    质量分: {row['quality_score']}")
            lines.append(f"    1年收益: {row['return_1y']:.2f}% (排名{row['percentile_1y']:.1f}%)")
            lines.append(f"    6月收益: {row['return_6m']:.2f}% (排名{row['percentile_6m']:.1f}%)")
            if pd.notna(row.get('stock_ratio_4q_avg')):
                lines.append(f"    股票仓位: {row['stock_ratio_4q_avg']:.1f}%")
            lines.append("")
    
    lines.append("="*80)
    lines.append("报告结束")
    lines.append("="*80)
    
    report = "\n".join(lines)
    
    # 保存报告
    with open(COMPARISON_REPORT, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"对比报告已保存: {COMPARISON_REPORT}")
    
    return report

def main():
    print("="*80)
    print("基金产品库重新筛选任务 V4.2（加入灵活配置型-季度修正版）")
    print("="*80)
    
    # 1. 加载数据
    df = load_fund_data()
    
    # 2. 处理灵活配置型基金
    df_modified, new_flexible_funds = process_flexible_config_funds(df)
    
    # 3. 应用筛选条件
    df_filtered = apply_filters(df_modified)
    
    # 4. 分级入库
    df_classified = classify_library(df_filtered)
    
    # 5. 保存结果
    core_df, watch_df, backup_df = save_results(df_classified)
    
    # 6. 生成对比报告
    v3_core_file = os.path.join(WORKSPACE, 'fund_core_library_v3.csv')
    report = generate_comparison_report(df_classified, v3_core_file, new_flexible_funds)
    
    # 输出核心库信息
    print("\n" + "="*80)
    print("【V4版本核心库基金】")
    print("="*80)
    
    if len(core_df) > 0:
        display_cols = ['ts_code', 'name', 'category', 'fund_scale', 'quality_score', 'return_1y']
        for col in display_cols:
            if col not in core_df.columns:
                core_df[col] = None
        print(core_df[display_cols].to_string(index=False))
        print(f"\n共 {len(core_df)} 只基金")
    else:
        print("核心库为空")
    
    # 输出报告
    print("\n" + report)
    
    print("\n" + "="*80)
    print("任务完成!")
    print("="*80)

if __name__ == '__main__':
    main()
