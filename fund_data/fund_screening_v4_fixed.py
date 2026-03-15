#!/usr/bin/env python3
"""
基金产品库筛选任务 - V4修复版（全量数据获取）
- 分批获取464只灵活配置型基金的季度持仓数据（每批20只）
- 单只基金获取失败时重试3次
- 计算每只基金近4季度平均股票仓位
- 筛选平均仓位>60%的基金，归入"混合型-偏股"
- 重新执行三级筛选（业绩+质量+规模）
- 分级入库（核心库/观察库/备选库）
"""

import pandas as pd
import numpy as np
import tushare as ts
import os
import time
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
CORE_LIBRARY_V4 = os.path.join(WORKSPACE, 'fund_core_library_v4_fixed.csv')
WATCH_LIBRARY_V4 = os.path.join(WORKSPACE, 'fund_watch_library_v4_fixed.csv')
BACKUP_LIBRARY_V4 = os.path.join(WORKSPACE, 'fund_backup_library_v4_fixed.csv')
SCREENING_REPORT = os.path.join(WORKSPACE, 'screening_report_v4_fixed.txt')

# 创建holdings目录
os.makedirs(HOLDINGS_DIR, exist_ok=True)

def load_fund_data():
    """加载基金筛选数据"""
    print("="*80)
    print("加载基金筛选数据...")
    df = pd.read_csv(INPUT_FILE, encoding='utf-8-sig')
    print(f"加载了 {len(df)} 条基金记录")
    return df

def get_flexible_funds(df):
    """获取所有灵活配置型基金"""
    flexible_funds = df[df['invest_type'] == '灵活配置型'].copy()
    print(f"\n找到 {len(flexible_flexible_funds)} 只灵活配置型基金")
    return flexible_funds

def fetch_fund_holdings_with_retry(ts_code, max_retries=3):
    """
    获取基金持仓数据，带重试机制
    返回: (成功标志, 数据DataFrame或错误信息)
    """
    for attempt in range(max_retries):
        try:
            # 获取基金持仓数据
            df = pro.fund_portfolio(ts_code=ts_code)
            if df is not None and len(df) > 0:
                return True, df
            else:
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                return False, "无数据"
        except Exception as e:
            error_msg = str(e)
            if "每分钟最多访问" in error_msg or "limit" in error_msg.lower():
                # 遇到限流，等待更长时间
                wait_time = 5 * (attempt + 1)
                print(f"    限流，等待{wait_time}秒...")
                time.sleep(wait_time)
            elif attempt < max_retries - 1:
                time.sleep(2)
            else:
                return False, error_msg
    
    return False, "重试次数耗尽"

def batch_fetch_holdings(flexible_funds, batch_size=20):
    """
    分批获取基金持仓数据
    每批20只基金，避免超时和限流
    """
    print("\n" + "="*80)
    print("【步骤1】分批获取灵活配置型基金持仓数据")
    print("="*80)
    
    ts_codes = flexible_funds['ts_code'].tolist()
    total = len(ts_codes)
    
    # 检查已有数据的基金
    existing_codes = []
    missing_codes = []
    
    for code in ts_codes:
        holdings_file = os.path.join(HOLDINGS_DIR, f"{code}_holdings.csv")
        if os.path.exists(holdings_file):
            existing_codes.append(code)
        else:
            missing_codes.append(code)
    
    print(f"已有持仓数据的基金: {len(existing_codes)}/{total}")
    print(f"需要获取的基金: {len(missing_codes)}/{total}")
    
    # 统计
    success_count = len(existing_codes)
    failed_codes = []
    
    # 分批获取缺失的数据
    if len(missing_codes) > 0:
        batches = [missing_codes[i:i+batch_size] for i in range(0, len(missing_codes), batch_size)]
        
        print(f"\n共{batch_size}只/批，共{len(batches)}批")
        print("-"*80)
        
        for batch_idx, batch in enumerate(batches):
            print(f"\n处理第 {batch_idx+1}/{len(batches)} 批 ({len(batch)}只基金)...")
            batch_start_time = time.time()
            
            for code in batch:
                holdings_file = os.path.join(HOLDINGS_DIR, f"{code}_holdings.csv")
                
                # 尝试获取数据
                success, result = fetch_fund_holdings_with_retry(code, max_retries=3)
                
                if success:
                    # 保存数据
                    df = result
                    df.to_csv(holdings_file, index=False, encoding='utf-8-sig')
                    success_count += 1
                    print(f"  ✓ {code}: {len(df)}条记录")
                else:
                    failed_codes.append({
                        'ts_code': code,
                        'name': flexible_funds[flexible_funds['ts_code']==code]['name'].values[0] if len(flexible_funds[flexible_funds['ts_code']==code]) > 0 else 'Unknown',
                        'error': result
                    })
                    print(f"  ✗ {code}: 获取失败 - {result}")
                
                # 小延迟，避免限流
                time.sleep(0.3)
            
            batch_time = time.time() - batch_start_time
            print(f"  本批耗时: {batch_time:.1f}秒")
            
            # 批次间延迟
            if batch_idx < len(batches) - 1:
                time.sleep(1)
    
    # 统计结果
    success_rate = success_count / total * 100 if total > 0 else 0
    
    print("\n" + "-"*80)
    print("【数据获取统计】")
    print(f"  总基金数: {total}")
    print(f"  成功获取: {success_count}")
    print(f"  获取失败: {len(failed_codes)}")
    print(f"  成功率: {success_rate:.1f}%")
    
    if failed_codes:
        print(f"\n获取失败的基金 ({len(failed_codes)}只):")
        for item in failed_codes:
            print(f"  {item['ts_code']} {item['name']}: {item['error']}")
    
    return success_count, failed_codes, success_rate

def get_quarter_from_end_date(end_date):
    """根据end_date判断所属季度"""
    try:
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
        else:
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
        
        # 检查必要的列
        required_cols = ['end_date', 'stk_mkv_ratio']
        for col in required_cols:
            if col not in df.columns:
                print(f"  {ts_code}: 缺少列 {col}")
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
            
            # 对于每个季度，取最新end_date的数据
            latest_end_date = q_df['end_date'].max()
            q_df = q_df[q_df['end_date'] == latest_end_date]
            
            # 计算该季度的股票仓位
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
        
        return avg_ratio, len(recent_4q)
    
    except Exception as e:
        print(f"计算 {ts_code} 股票仓位时出错: {e}")
        return None, 0

def calculate_all_stock_ratios(flexible_funds):
    """
    计算所有灵活配置型基金的股票仓位
    """
    print("\n" + "="*80)
    print("【步骤2-3】计算灵活配置型基金近4季度平均股票仓位")
    print("="*80)
    
    stock_ratios = []
    processed_count = 0
    total = len(flexible_funds)
    
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
            print(f"  已处理 {processed_count}/{total} 只基金...")
    
    ratio_df = pd.DataFrame(stock_ratios)
    
    # 统计
    valid_ratios = ratio_df[ratio_df['avg_stock_ratio'].notna()]
    print(f"\n成功计算 {len(valid_ratios)}/{total} 只基金的股票仓位")
    
    if len(valid_ratios) > 0:
        print(f"\n股票仓位统计:")
        print(f"  均值: {valid_ratios['avg_stock_ratio'].mean():.2f}%")
        print(f"  中位数: {valid_ratios['avg_stock_ratio'].median():.2f}%")
        print(f"  最大值: {valid_ratios['avg_stock_ratio'].max():.2f}%")
        print(f"  最小值: {valid_ratios['avg_stock_ratio'].min():.2f}%")
        
        # 统计各区间
        ranges = [(0, 30), (30, 50), (50, 60), (60, 80), (80, 100)]
        for r_min, r_max in ranges:
            count = len(valid_ratios[(valid_ratios['avg_stock_ratio'] >= r_min) & 
                                      (valid_ratios['avg_stock_ratio'] < r_max)])
            print(f"  仓位{r_min}-{r_max}%: {count}只")
        
        # 显示高仓位基金
        high_stock = valid_ratios[valid_ratios['avg_stock_ratio'] > 60].sort_values('avg_stock_ratio', ascending=False)
        print(f"\n仓位>60%的基金 ({len(high_stock)}只):")
        for idx, row in high_stock.head(20).iterrows():
            print(f"  {row['ts_code']} {row['name']}: {row['avg_stock_ratio']:.1f}%")
        if len(high_stock) > 20:
            print(f"  ... 还有 {len(high_stock)-20} 只")
    
    return ratio_df

def update_fund_categories(df, ratio_df):
    """
    更新基金类别：将平均仓位>60%的灵活配置型基金归入"混合型-偏股"
    """
    print("\n" + "="*80)
    print("【步骤4】更新基金类别（仓位>60%归入混合型-偏股）")
    print("="*80)
    
    df_modified = df.copy()
    
    # 筛选平均仓位>60%的基金
    high_stock_ratio = ratio_df[
        (ratio_df['avg_stock_ratio'].notna()) & 
        (ratio_df['avg_stock_ratio'] > 60)
    ].copy()
    
    print(f"平均股票仓位>60%的灵活配置型基金: {len(high_stock_ratio)} 只")
    
    # 更新原始数据框中的类别
    modified_count = 0
    
    for idx, row in high_stock_ratio.iterrows():
        ts_code = row['ts_code']
        mask = df_modified['ts_code'] == ts_code
        if mask.any():
            old_category = df_modified.loc[mask, 'category'].values[0]
            df_modified.loc[mask, 'category'] = '混合型-偏股'
            df_modified.loc[mask, 'stock_ratio_4q_avg'] = row['avg_stock_ratio']
            modified_count += 1
    
    # 为所有灵活配置型基金添加股票仓位列
    for idx, row in ratio_df.iterrows():
        ts_code = row['ts_code']
        mask = df_modified['ts_code'] == ts_code
        if mask.any() and pd.notna(row['avg_stock_ratio']):
            df_modified.loc[mask, 'stock_ratio_4q_avg'] = row['avg_stock_ratio']
    
    print(f"已将 {modified_count} 只基金类别更新为'混合型-偏股'")
    
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
        if scale < 1:
            return 'rejected'
        elif 5 <= scale <= 50:
            return 'preferred'
        elif (1 <= scale < 5) or scale > 100:
            return 'watch'
        else:
            return 'normal'
    else:
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
    print("【步骤5】应用筛选条件")
    print("="*80)
    
    # 1. 规模分类
    df['scale_status'] = df.apply(classify_scale_status, axis=1)
    
    # 2. 一票否决
    df['veto'] = df['scale_status'] == 'rejected'
    
    # 3. 业绩筛选（严格条件）
    df['pass_performance'] = (df['percentile_1y'] <= 10) | (df['percentile_6m'] <= 20)
    
    # 4. 质量评分 >= 70
    df['pass_quality'] = df['quality_score'] >= 70
    
    # 5. 高质量评分 >= 80
    df['high_quality'] = df['quality_score'] >= 80
    
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
    print("【步骤6】分级入库")
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
    
    core_count = df['is_core'].sum()
    watch_count = df['is_watch'].sum()
    backup_count = df['is_backup'].sum()
    veto_count = df['veto'].sum()
    
    print(f"\n入库统计:")
    print(f"  总基金数: {len(df)}")
    print(f"  核心库: {core_count}")
    print(f"  观察库: {watch_count}")
    print(f"  备选库: {backup_count}")
    print(f"  一票否决: {veto_count}")
    
    return df

def save_results(df):
    """保存结果"""
    print("\n" + "="*80)
    print("【步骤7】保存结果")
    print("="*80)
    
    output_cols = ['ts_code', 'name', 'invest_type', 'category', 'fund_scale', 
                  'scale_status', 'return_3m', 'return_6m', 'return_1y', 
                  'quality_score', 'percentile_6m', 'percentile_1y',
                  'stock_ratio_4q_avg', 'is_core', 'is_watch', 'is_backup']
    
    # 核心库
    core_df = df[df['is_core']].copy()
    if len(core_df) > 0:
        for col in output_cols:
            if col not in core_df.columns:
                core_df[col] = None
        core_df[output_cols].to_csv(CORE_LIBRARY_V4, index=False, encoding='utf-8-sig')
        print(f"核心库 ({len(core_df)}条): {CORE_LIBRARY_V4}")
    else:
        print("核心库为空")
        core_df = pd.DataFrame()
    
    # 观察库
    watch_df = df[df['is_watch']].copy()
    if len(watch_df) > 0:
        for col in output_cols:
            if col not in watch_df.columns:
                watch_df[col] = None
        watch_df[output_cols].to_csv(WATCH_LIBRARY_V4, index=False, encoding='utf-8-sig')
        print(f"观察库 ({len(watch_df)}条): {WATCH_LIBRARY_V4}")
    else:
        print("观察库为空")
    
    # 备选库
    backup_df = df[df['is_backup']].copy()
    if len(backup_df) > 0:
        for col in output_cols:
            if col not in backup_df.columns:
                backup_df[col] = None
        backup_df[output_cols].to_csv(BACKUP_LIBRARY_V4, index=False, encoding='utf-8-sig')
        print(f"备选库 ({len(backup_df)}条): {BACKUP_LIBRARY_V4}")
    else:
        print("备选库为空")
    
    return core_df, watch_df, backup_df

def generate_report(df, flexible_funds, ratio_df, high_stock_funds, 
                   success_count, failed_codes, success_rate):
    """生成筛选报告"""
    print("\n" + "="*80)
    print("【生成筛选报告】")
    print("="*80)
    
    lines = []
    lines.append("="*80)
    lines.append("基金产品库筛选报告 V4.0 - 修复版（全量数据）")
    lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("="*80)
    lines.append("")
    
    # 数据获取统计
    lines.append("【数据获取统计】")
    lines.append(f"  灵活配置型基金总数: {len(flexible_funds)}")
    lines.append(f"  成功获取持仓数据: {success_count}")
    lines.append(f"  获取失败: {len(failed_codes)}")
    lines.append(f"  成功率: {success_rate:.1f}%")
    lines.append("")
    
    # 股票仓位统计
    valid_ratios = ratio_df[ratio_df['avg_stock_ratio'].notna()]
    if len(valid_ratios) > 0:
        lines.append("【股票仓位统计】")
        lines.append(f"  成功计算仓位: {len(valid_ratios)}/{len(flexible_funds)}")
        lines.append(f"  均值: {valid_ratios['avg_stock_ratio'].mean():.2f}%")
        lines.append(f"  中位数: {valid_ratios['avg_stock_ratio'].median():.2f}%")
        lines.append(f"  最大值: {valid_ratios['avg_stock_ratio'].max():.2f}%")
        lines.append(f"  最小值: {valid_ratios['avg_stock_ratio'].min():.2f}%")
        lines.append("")
        
        # 仓位分布
        lines.append("【仓位分布】")
        ranges = [(0, 30, '低仓位'), (30, 50, '中低仓位'), (50, 60, '中等仓位'), 
                  (60, 80, '偏高仓位'), (80, 100, '高仓位')]
        for r_min, r_max, label in ranges:
            count = len(valid_ratios[(valid_ratios['avg_stock_ratio'] >= r_min) & 
                                      (valid_ratios['avg_stock_ratio'] < r_max)])
            lines.append(f"  {label} ({r_min}-{r_max}%): {count}只")
        lines.append("")
    
    # 类别调整
    lines.append("【类别调整】")
    lines.append(f"  平均仓位>60%的基金数: {len(high_stock_funds)}")
    lines.append(f"  已归入'混合型-偏股': {len(high_stock_funds)} 只")
    lines.append("")
    
    # 入库统计
    core_count = df['is_core'].sum()
    watch_count = df['is_watch'].sum()
    backup_count = df['is_backup'].sum()
    
    lines.append("【入库统计】")
    lines.append(f"  总基金数: {len(df)}")
    lines.append(f"  核心库: {core_count}")
    lines.append(f"  观察库: {watch_count}")
    lines.append(f"  备选库: {backup_count}")
    lines.append(f"  一票否决: {df['veto'].sum()}")
    lines.append("")
    
    # 验证南方君信A
    nanfang = df[df['name'].str.contains('南方君信', na=False)]
    if len(nanfang) > 0:
        lines.append("【南方君信A验证】")
        for idx, row in nanfang.iterrows():
            lines.append(f"  基金代码: {row['ts_code']}")
            lines.append(f"  基金名称: {row['name']}")
            lines.append(f"  当前类别: {row['category']}")
            lines.append(f"  投资类型: {row['invest_type']}")
            lines.append(f"  平均仓位: {row.get('stock_ratio_4q_avg', 'N/A')}")
            lines.append(f"  是否在核心库: {row['is_core']}")
            lines.append(f"  是否在观察库: {row['is_watch']}")
        lines.append("")
    
    # 核心库列表
    core_df = df[df['is_core']].copy()
    if len(core_df) > 0:
        lines.append("【核心库基金列表】")
        for idx, row in core_df.iterrows():
            lines.append(f"  {row['ts_code']} {row['name']}")
            lines.append(f"    类别: {row['category']}")
            lines.append(f"    规模: {row['fund_scale']:.2f}亿")
            lines.append(f"    质量分: {row['quality_score']}")
            lines.append(f"    1年收益: {row['return_1y']:.2f}% (排名{row['percentile_1y']:.1f}%)")
            if pd.notna(row.get('stock_ratio_4q_avg')):
                lines.append(f"    股票仓位: {row['stock_ratio_4q_avg']:.1f}%")
            lines.append("")
    
    # 获取失败的基金
    if failed_codes:
        lines.append("【获取失败的基金】")
        for item in failed_codes:
            lines.append(f"  {item['ts_code']} {item['name']}: {item['error']}")
        lines.append("")
    
    lines.append("="*80)
    lines.append("报告结束")
    lines.append("="*80)
    
    report = "\n".join(lines)
    
    with open(SCREENING_REPORT, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"报告已保存: {SCREENING_REPORT}")
    return report

def main():
    print("="*80)
    print("基金产品库筛选任务 V4.0 - 修复版（全量数据获取）")
    print("="*80)
    start_time = time.time()
    
    # 1. 加载数据
    df = load_fund_data()
    
    # 2. 获取所有灵活配置型基金
    flexible_funds = df[df['invest_type'] == '灵活配置型'].copy()
    print(f"找到 {len(flexible_funds)} 只灵活配置型基金")
    
    # 3. 分批获取持仓数据
    success_count, failed_codes, success_rate = batch_fetch_holdings(flexible_funds, batch_size=20)
    
    # 检查成功率
    if success_rate < 90:
        print(f"\n警告: 数据获取成功率仅{success_rate:.1f}%，低于90%目标")
        print("建议重新运行任务")
    
    # 4. 计算所有基金的股票仓位
    ratio_df = calculate_all_stock_ratios(flexible_funds)
    
    # 5. 更新基金类别
    df_modified, high_stock_funds = update_fund_categories(df, ratio_df)
    
    # 6. 应用筛选条件
    df_filtered = apply_filters(df_modified)
    
    # 7. 分级入库
    df_classified = classify_library(df_filtered)
    
    # 8. 保存结果
    core_df, watch_df, backup_df = save_results(df_classified)
    
    # 9. 生成报告
    report = generate_report(df_classified, flexible_funds, ratio_df, 
                           high_stock_funds, success_count, failed_codes, success_rate)
    
    # 输出结果摘要
    elapsed_time = time.time() - start_time
    print("\n" + "="*80)
    print("【任务完成摘要】")
    print("="*80)
    print(f"运行时间: {elapsed_time/60:.1f} 分钟")
    print(f"灵活配置型基金: {len(flexible_funds)} 只")
    print(f"数据获取成功率: {success_rate:.1f}%")
    print(f"高仓位基金(>60%): {len(high_stock_funds)} 只")
    print(f"核心库: {len(core_df)} 只")
    print(f"观察库: {len(watch_df)} 只")
    print(f"备选库: {len(backup_df)} 只")
    
    # 验证南方君信A
    nanfang = df_classified[df_classified['name'].str.contains('南方君信', na=False)]
    if len(nanfang) > 0:
        print("\n【南方君信A验证】")
        for idx, row in nanfang.iterrows():
            print(f"  代码: {row['ts_code']}")
            print(f"  名称: {row['name']}")
            print(f"  类别: {row['category']}")
            print(f"  仓位: {row.get('stock_ratio_4q_avg', 'N/A')}")
            print(f"  核心库: {row['is_core']}")
            print(f"  观察库: {row['is_watch']}")
    
    print("\n" + "="*80)
    print("任务完成!")
    print("="*80)
    
    return df_classified, core_df, watch_df, backup_df

if __name__ == '__main__':
    main()
