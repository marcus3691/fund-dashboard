#!/usr/bin/env python3
"""
生成去重后的基金报告（用于网页展示）
"""

import pandas as pd
import json
import sys

def generate_deduplicated_reports():
    # 读取去重后的数据
    df = pd.read_csv('equity_selected_2025_deduplicated.csv')
    
    # 构建报告字典
    reports = {}
    
    for _, row in df.iterrows():
        code = row['ts_code']
        
        # 构建报告结构
        report = {
            "name": row['name'],
            "code": code,
            "manager": row.get('manager', '未知'),  # 如果有基金经理数据
            "category": row['category'],
            "score": round(row['quality_score'], 1),
            "rating": "★" * int(row['quality_score'] / 20) + "☆" * (5 - int(row['quality_score'] / 20)),
            "quality": "优秀" if row['quality_score'] >= 85 else "良好" if row['quality_score'] >= 75 else "中等偏上" if row['quality_score'] >= 65 else "中等",
            "merged_info": {
                "share_count": int(row.get('share_count', 1)),
                "selected_share": row.get('selected_share', 'X'),
                "merged_shares": row.get('merged_shares', code),
                "merged_names": row.get('merged_names', row['name'])
            },
            "performance": {
                "return_1y": round(row['return_1y'], 2),
                "return_6m": round(row['return_6m'], 2),
                "volatility": round(row['volatility'], 2),
                "max_drawdown": round(row['max_drawdown'], 2),
                "sharpe": round(row['sharpe'], 2)
            },
            "ranking": {
                "rank_1y": int(row['rank_1y']),
                "percentile_1y": round(row['percentile_1y'], 1)
            }
        }
        
        reports[code] = report
    
    # 保存JSON
    output_file = 'analysis/fund_reports_deduplicated.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(reports, f, ensure_ascii=False, indent=2)
    
    print(f"去重后的报告已生成: {output_file}")
    print(f"  共 {len(reports)} 只基金")
    
    return reports

if __name__ == '__main__':
    generate_deduplicated_reports()
