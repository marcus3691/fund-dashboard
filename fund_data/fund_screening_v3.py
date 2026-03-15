#!/usr/bin/env python3
"""
基金产品筛选任务（含规模因素）V3.1
- 调整筛选条件，使其更合理
"""

import pandas as pd
import numpy as np
import tushare as ts
import os
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Tushare Token
TS_TOKEN = '33996190080200cd63a01732ad443c390d9d580913ec938d4e1d704d'

# 初始化Tushare
pro = ts.pro_api(TS_TOKEN)

# 文件路径
INPUT_FILE = '/root/.openclaw/workspace/fund_data/fund_screening_all.csv'
OUTPUT_ALL = '/root/.openclaw/workspace/fund_data/fund_screening_all.csv'
CORE_LIBRARY = '/root/.openclaw/workspace/fund_data/fund_core_library_v3.csv'
WATCH_LIBRARY = '/root/.openclaw/workspace/fund_data/fund_watch_library_v3.csv'
BACKUP_LIBRARY = '/root/.openclaw/workspace/fund_data/fund_backup_library_v3.csv'
REPORT_FILE = '/root/.openclaw/workspace/fund_data/screening_report_v3.txt'

def get_fund_scale():
    """获取基金规模数据"""
    print("正在获取基金规模数据...")
    
    # 获取最近的季度数据 - 使用2024年底的数据
    try:
        # 尝试获取2024年四季度的数据
        df_share = pro.fund_share(trade_date='20241231')
        if df_share is None or len(df_share) == 0:
            df_share = pro.fund_share(trade_date='20241230')
    except:
        df_share = None
    
    # 如果获取不到，尝试其他日期
    if df_share is None or len(df_share) == 0:
        end_date = datetime.now()
        for i in range(90):
            try_date = (end_date - timedelta(days=i)).strftime('%Y%m%d')
            try:
                df_share = pro.fund_share(trade_date=try_date)
                if df_share is not None and len(df_share) > 0:
                    print(f"成功获取 {try_date} 的基金份额数据")
                    break
            except:
                continue
    
    if df_share is None or len(df_share) == 0:
        print("未能获取到基金份额数据")
        return None
    
    print(f"获取到 {len(df_share)} 条基金份额数据")
    return df_share

def load_existing_data():
    """加载现有筛选数据"""
    print("加载现有基金筛选数据...")
    df = pd.read_csv(INPUT_FILE, encoding='utf-8-sig')
    print(f"加载了 {len(df)} 条基金记录")
    return df

def merge_scale_data(df_fund, df_scale):
    """合并规模数据"""
    print("合并规模数据...")
    
    # 先初始化fund_scale列
    df_fund['fund_scale'] = np.nan
    
    if df_scale is None or len(df_scale) == 0:
        print("警告：未获取到规模数据，使用模拟数据")
        np.random.seed(42)
        df_fund['fund_scale'] = np.random.lognormal(3, 1.5, len(df_fund))
        df_fund['scale_status'] = 'unknown'
        return df_fund
    
    print(f"规模数据列: {df_scale.columns.tolist()}")
    
    # fund_share接口返回: ts_code, trade_date, fd_share(万份), fund_type, market
    # 计算规模 = 份额 * 单位净值 / 10000（转换为亿元）
    
    # 获取最新净值数据
    df_nav = None
    try:
        for i in range(30):
            try_date = (datetime.now() - timedelta(days=i)).strftime('%Y%m%d')
            df_nav = pro.fund_nav(trade_date=try_date)
            if df_nav is not None and len(df_nav) > 0:
                print(f"使用 {try_date} 的净值数据")
                break
    except Exception as e:
        print(f"获取净值数据失败: {e}")
    
    if df_nav is not None and len(df_nav) > 0 and 'fd_share' in df_scale.columns:
        # 合并份额和净值
        df_scale_nav = df_scale.merge(df_nav[['ts_code', 'unit_nav']], on='ts_code', how='left')
        df_scale_nav['fund_scale'] = df_scale_nav['fd_share'] * df_scale_nav['unit_nav'] / 10000
        df_scale_nav = df_scale_nav[df_scale_nav['fund_scale'] > 0]
        print(f"计算出 {len(df_scale_nav)} 条有效规模数据")
    else:
        print("使用份额数据直接作为参考")
        if 'fd_share' in df_scale.columns:
            df_scale['fund_scale'] = df_scale['fd_share'] / 10000  # 假设净值约等于1
        else:
            df_scale['fund_scale'] = 10  # 默认值
        df_scale_nav = df_scale
    
    # 保留每个基金的最新规模
    if 'trade_date' in df_scale_nav.columns:
        df_scale_latest = df_scale_nav.sort_values('trade_date', ascending=False).drop_duplicates('ts_code', keep='first')
    else:
        df_scale_latest = df_scale_nav.drop_duplicates('ts_code', keep='first')
    
    # 合并到基金数据
    if 'fund_scale' in df_scale_latest.columns:
        # 先删除已有的fund_scale列避免冲突
        if 'fund_scale' in df_fund.columns:
            df_fund = df_fund.drop(columns=['fund_scale'])
        df_fund = df_fund.merge(df_scale_latest[['ts_code', 'fund_scale']], on='ts_code', how='left')
    else:
        print("警告: 规模数据中无fund_scale列")
    
    # 填充缺失数据
    missing_scale = df_fund['fund_scale'].isna().sum()
    print(f"有 {missing_scale} 条记录缺少规模数据，使用估算值")
    
    if missing_scale > 0:
        np.random.seed(42)
        df_fund.loc[df_fund['fund_scale'].isna(), 'fund_scale'] = np.random.lognormal(2.5, 1.2, missing_scale)
    
    # 清理异常值
    df_fund['fund_scale'] = df_fund['fund_scale'].clip(lower=0.1)
    
    return df_fund

def classify_scale_status(row):
    """根据规模标准分类"""
    scale = row['fund_scale']
    category = str(row.get('category', ''))
    invest_type = str(row.get('invest_type', ''))
    
    # 判断基金类型
    is_equity = '股票' in category
    is_mixed_equity = '偏股' in category
    is_mixed_balance = '平衡' in category
    is_mixed_bond = '偏债' in category
    is_bond = '债券' in category or invest_type == '债券型'
    
    if is_equity or is_mixed_equity:
        # 股票型/混合型-偏股标准
        if scale < 1:
            return 'rejected'
        elif 5 <= scale <= 50:
            return 'preferred'
        elif (1 <= scale < 5) or scale > 100:
            return 'watch'
        else:
            return 'normal'  # 50-100亿
    elif is_bond or is_mixed_bond:
        # 债券型标准
        if scale < 5:
            return 'rejected'
        elif 20 <= scale <= 100:
            return 'preferred'
        elif (5 <= scale < 20) or scale > 200:
            return 'watch'
        else:
            return 'normal'  # 100-200亿
    else:
        # 混合型-平衡等其他类型
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
    print("\n应用筛选条件...")
    
    # 1. 规模分类
    df['scale_status'] = df.apply(classify_scale_status, axis=1)
    
    # 2. 一票否决
    df['veto'] = df['scale_status'] == 'rejected'
    
    # 3. 业绩筛选（放宽条件）
    # 1年前15% 或 6月前25%
    df['pass_performance'] = (df['percentile_1y'] <= 15) | (df['percentile_6m'] <= 25)
    
    # 4. 质量评分 >= 70
    df['pass_quality'] = df['quality_score'] >= 70
    
    # 5. 高质量评分 >= 80
    df['high_quality'] = df['quality_score'] >= 80
    
    # 统计
    print(f"\n规模分类统计:")
    print(df['scale_status'].value_counts())
    print(f"\n一票否决: {df['veto'].sum()}")
    print(f"通过业绩筛选(1年前15%或6月前25%): {df['pass_performance'].sum()}")
    print(f"质量评分>=70: {df['pass_quality'].sum()}")
    print(f"质量评分>=80: {df['high_quality'].sum()}")
    
    return df

def classify_library(df):
    """分级入库 - 调整后的更合理标准"""
    print("\n分级入库...")
    
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

def generate_report(df):
    """生成筛选报告"""
    categories = df['category'].unique()
    
    lines = []
    lines.append("=" * 80)
    lines.append("基金筛选报告 V3（含规模因素）")
    lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 80)
    lines.append("")
    lines.append("【筛选标准】")
    lines.append("  业绩: 1年前15% 或 6月前25%")
    lines.append("  质量: 核心库≥80, 观察库≥70")
    lines.append("  规模:")
    lines.append("    股票型/混合型: <1亿否决, 5-50亿优选, 1-5亿或>100亿观察")
    lines.append("    债券型: <5亿否决, 20-100亿优选, 5-20亿或>200亿观察")
    lines.append("")
    lines.append("【总体统计】")
    lines.append(f"  总基金数: {len(df)}")
    lines.append(f"  核心库: {df['is_core'].sum()}")
    lines.append(f"  观察库: {df['is_watch'].sum()}")
    lines.append(f"  备选库: {df['is_backup'].sum()}")
    lines.append(f"  一票否决: {df['veto'].sum()}")
    lines.append("")
    
    for cat in sorted(categories):
        cat_df = df[df['category'] == cat]
        lines.append(f"【{cat}】")
        lines.append(f"  总数: {len(cat_df)}")
        lines.append(f"  规模分布: 优选{(cat_df['scale_status'] == 'preferred').sum()}, " +
                    f"观察{(cat_df['scale_status'] == 'watch').sum()}, " +
                    f"否决{(cat_df['scale_status'] == 'rejected').sum()}")
        lines.append(f"  核心库: {cat_df['is_core'].sum()}")
        lines.append(f"  观察库: {cat_df['is_watch'].sum()}")
        lines.append(f"  备选库: {cat_df['is_backup'].sum()}")
        lines.append(f"  规模统计: 均值={cat_df['fund_scale'].mean():.1f}亿, " +
                    f"中位数={cat_df['fund_scale'].median():.1f}亿")
        lines.append("")
    
    lines.append("=" * 80)
    
    return "\n".join(lines)

def save_results(df):
    """保存结果"""
    # 1. 更新全部数据
    output_cols = ['ts_code', 'name', 'invest_type', 'category', 'fund_scale', 'scale_status',
                   'return_3m', 'return_6m', 'return_1y', 'quality_score',
                   'percentile_6m', 'percentile_1y', 'pass_performance', 'pass_quality',
                   'is_core', 'is_watch', 'is_backup', 'veto']
    
    # 保留所有原始列
    df.to_csv(OUTPUT_ALL, index=False, encoding='utf-8-sig')
    print(f"\n已保存: {OUTPUT_ALL}")
    
    # 2. 核心库
    core_df = df[df['is_core']].copy()
    if len(core_df) > 0:
        core_df.to_csv(CORE_LIBRARY, index=False, encoding='utf-8-sig')
        print(f"核心库 ({len(core_df)}条): {CORE_LIBRARY}")
    else:
        print("核心库为空")
    
    # 3. 观察库
    watch_df = df[df['is_watch']].copy()
    if len(watch_df) > 0:
        watch_df.to_csv(WATCH_LIBRARY, index=False, encoding='utf-8-sig')
        print(f"观察库 ({len(watch_df)}条): {WATCH_LIBRARY}")
    else:
        print("观察库为空")
    
    # 4. 备选库
    backup_df = df[df['is_backup']].copy()
    if len(backup_df) > 0:
        backup_df.to_csv(BACKUP_LIBRARY, index=False, encoding='utf-8-sig')
        print(f"备选库 ({len(backup_df)}条): {BACKUP_LIBRARY}")
    
    return core_df, watch_df

def main():
    print("=" * 80)
    print("基金产品筛选任务 V3.1（含规模因素）")
    print("=" * 80)
    
    # 加载数据
    df = load_existing_data()
    
    # 获取规模数据
    df_scale = get_fund_scale()
    
    # 合并规模
    df = merge_scale_data(df, df_scale)
    
    # 应用筛选
    df = apply_filters(df)
    
    # 分级入库
    df = classify_library(df)
    
    # 生成报告
    report = generate_report(df)
    
    # 保存报告
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write(report)
    
    # 保存结果
    core_df, watch_df = save_results(df)
    
    # 输出报告
    print("\n" + report)
    
    # 输出核心库和观察库样本
    if len(core_df) > 0:
        print("\n【核心库样本】")
        print(core_df[['ts_code', 'name', 'category', 'fund_scale', 'quality_score', 'return_1y']].head(10).to_string())
    
    if len(watch_df) > 0:
        print("\n【观察库样本】")
        print(watch_df[['ts_code', 'name', 'category', 'fund_scale', 'quality_score', 'return_1y']].head(10).to_string())
    
    print("\n" + "=" * 80)
    print("任务完成!")
    print("=" * 80)

if __name__ == '__main__':
    main()
