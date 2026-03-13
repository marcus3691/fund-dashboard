import json
import pandas as pd
from datetime import datetime

# 读取基础数据
df = pd.read_csv('/root/.openclaw/workspace/fund_data/equity_selected_2025_deduplicated.csv')

# 读取持仓数据并分析
holdings_dir = '/root/.openclaw/workspace/fund_data/holdings'

stock_industry = {
    '601225.SH': '煤炭', '600938.SH': '石油', '000933.SZ': '煤炭',
    '600256.SH': '石油/天然气', '600348.SH': '煤炭', '601666.SH': '煤炭',
    '601088.SH': '煤炭', '601001.SH': '煤炭',
    '603993.SH': '有色', '600362.SH': '有色', '000630.SZ': '有色',
    '600259.SH': '有色/稀土', '000657.SZ': '有色', '600111.SH': '稀土',
    '000960.SZ': '有色', '601899.SH': '有色/黄金', '000408.SZ': '有色/锂矿',
    '603799.SH': '有色', '000807.SZ': '有色', '600595.SH': '有色',
    '600549.SH': '有色/稀土', '601600.SH': '有色',
    '601233.SH': '化工', '300487.SZ': '化工', '600426.SH': '化工',
    '002064.SZ': '化工', '600160.SH': '化工', '000830.SZ': '化工',
    '600141.SH': '化工', '603379.SH': '化工', '002493.SZ': '化工',
    '603225.SH': '化工', '000703.SZ': '化工', '600075.SH': '化工',
    '002028.SZ': '电网设备', '688599.SH': '光伏', '002459.SZ': '光伏',
    '300274.SZ': '光伏', '002049.SZ': '半导体', '0981.HK': '半导体',
    '601689.SH': '汽车零部件', '002050.SZ': '汽车零部件',
}

def get_match_score(code):
    import os
    file_path = f"{holdings_dir}/{code}_holdings.csv"
    if not os.path.exists(file_path):
        return 0, {}
    
    try:
        hdf = pd.read_csv(file_path)
        if 'quarter' in hdf.columns:
            hdf = hdf[hdf['quarter'] == hdf['quarter'].max()]
        
        industry_dist = {}
        for _, row in hdf.iterrows():
            symbol = row.get('symbol', '')
            ratio = row.get('stk_mkv_ratio', 0)
            ind = stock_industry.get(symbol, '其他')
            industry_dist[ind] = industry_dist.get(ind, 0) + ratio
        
        keywords = ['煤炭', '石油', '有色', '稀土', '化工', '电网', '光伏']
        match = sum(ratio for ind, ratio in industry_dist.items() 
                   if any(kw in ind for kw in keywords))
        return match, industry_dist
    except:
        return 0, {}

# 获取TOP50基金
top50 = df.nlargest(50, 'quality_score')

funds_list = []
for _, row in top50.iterrows():
    code = row['ts_code']
    match_score, ind_dist = get_match_score(code)
    
    funds_list.append({
        'code': code,
        'name': row['name'],
        'category': row['invest_type'],
        'return_1y': row['return_1y'],
        'sharpe': row['sharpe'],
        'quality_score': row['quality_score'],
        'match_score': match_score,
        'top_industries': list(ind_dist.keys())[:2] if ind_dist else ['其他']
    })

# 生成HTML
html = f'''&lt;!DOCTYPE html&gt;
&lt;html lang="zh-CN"&gt;
&lt;head&gt;
    &lt;meta charset="UTF-8"&gt;
    &lt;meta name="viewport" content="width=device-width, initial-scale=1.0"&gt;
    &lt;title&gt;基金产品库智能分析系统 V2&lt;/title&gt;
    &lt;style&gt;
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Microsoft YaHei', sans-serif; background: #f0f2f5; }}
        .header {{ background: linear-gradient(135deg, #1a237e 0%, #3949ab 100%); color: white; padding: 40px 20px; text-align: center; }}
        .header h1 {{ font-size: 32px; margin-bottom: 10px; }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
        .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin: 30px 0; }}
        .stat-card {{ background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); text-align: center; transition: transform 0.3s; }}
        .stat-card:hover {{ transform: translateY(-5px); }}
        .stat-card h3 {{ color: #1a237e; font-size: 36px; margin-bottom: 8px; }}
        .stat-card p {{ color: #666; font-size: 14px; }}
        .section {{ background: white; margin: 30px 0; padding: 30px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
        .section h2 {{ color: #1a237e; margin-bottom: 25px; padding-bottom: 15px; border-bottom: 3px solid #3949ab; display: flex; align-items: center; }}
        .section h2::before {{ content: ''; width: 4px; height: 24px; background: #3949ab; margin-right: 12px; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
        th {{ background: #f5f7fa; padding: 14px; text-align: left; font-weight: 600; color: #555; border-bottom: 2px solid #e8e8e8; }}
        td {{ padding: 14px; border-bottom: 1px solid #f0f0f0; }}
        tr:hover {{ background: #fafbfc; }}
        .tag {{ display: inline-block; padding: 4px 10px; border-radius: 4px; font-size: 12px; }}
        .tag-green {{ background: #e8f5e9; color: #2e7d32; }}
        .tag-orange {{ background: #fff3e0; color: #ef6c00; }}
        .tag-red {{ background: #ffebee; color: #c62828; }}
        .tag-blue {{ background: #e3f2fd; color: #1565c0; }}
        .score {{ font-weight: 700; font-size: 15px; }}
        .highlight {{ color: #d32f2f; font-weight: 600; }}
        .update-info {{ text-align: center; padding: 30px; color: #999; }}
        @media (max-width: 768px) {{ .stats {{ grid-template-columns: repeat(2, 1fr); }} }}
    &lt;/style&gt;
&lt;/head&gt;
&lt;body&gt;
    &lt;div class="header"&gt;
        &lt;h1&gt;基金产品库智能分析系统 V2&lt;/h1&gt;
        &lt;p&gt;基于AI驱动的公募基金智能筛选与持仓分析平台&lt;/p&gt;
    &lt;/div&gt;
    
    &lt;div class="container"&gt;
        &lt;div class="stats"&gt;
            &lt;div class="stat-card"&gt;
                &lt;h3&gt;{len(funds_list)}&lt;/h3&gt;
                &lt;p&gt;入库基金总数&lt;/p&gt;
            &lt;/div&gt;
            &lt;div class="stat-card"&gt;
                &lt;h3&gt;{sum(f['return_1y'] for f in funds_list)/len(funds_list):.1f}%&lt;/h3&gt;
                &lt;p&gt;平均年化收益&lt;/p&gt;
            &lt;/div&gt;
            &lt;div class="stat-card"&gt;
                &lt;h3&gt;{sum(f['match_score'] for f in funds_list)/len(funds_list):.1f}%&lt;/h3&gt;
                &lt;p&gt;平均纪要匹配度&lt;/p&gt;
            &lt;/div&gt;
            &lt;div class="stat-card"&gt;
                &lt;h3&gt;{len([f for f in funds_list if f['match_score'] &gt;= 30])}&lt;/h3&gt;
                &lt;p&gt;高度匹配基金(≥30%)&lt;/p&gt;
            &lt;/div&gt;
        &lt;/div&gt;
        
        &lt;div class="section"&gt;
            &lt;h2&gt;TOP20 高质量基金（按质量评分）&lt;/h2&gt;
            &lt;table&gt;
                &lt;thead&gt;
                    &lt;tr&gt;
                        &lt;th&gt;排名&lt;/th&gt;&lt;th&gt;基金代码&lt;/th&gt;&lt;th&gt;基金名称&lt;/th&gt;&lt;th&gt;类型&lt;/th&gt;
                        &lt;th&gt;1年收益&lt;/th&gt;&lt;th&gt;夏普&lt;/th&gt;&lt;th&gt;质量分&lt;/th&gt;&lt;th&gt;纪要匹配&lt;/th&gt;&lt;th&gt;核心行业&lt;/th&gt;
                    &lt;/tr&gt;
                &lt;/thead&gt;
                &lt;tbody&gt;
'''

# TOP20
for i, f in enumerate(funds_list[:20], 1):
    match = f['match_score']
    tag_class = 'tag-green' if match >= 30 else ('tag-orange' if match >= 15 else 'tag-red')
    ind_text = ' + '.join(f['top_industries'][:2])
    
    html += f'''                    &lt;tr&gt;
                        &lt;td&gt;{i}&lt;/td&gt;
                        &lt;td&gt;{f['code']}&lt;/td&gt;
                        &lt;td&gt;{f['name']}&lt;/td&gt;
                        &lt;td&gt;{f['category']}&lt;/td&gt;
                        &lt;td&gt;{f['return_1y']:.2f}%&lt;/td&gt;
                        &lt;td&gt;{f['sharpe']:.2f}&lt;/td&gt;
                        &lt;td class="highlight"&gt;{f['quality_score']:.1f}&lt;/td&gt;
                        &lt;td&gt;&lt;span class="tag {tag_class}"&gt;{match:.1f}%&lt;/span&gt;&lt;/td&gt;
                        &lt;td&gt;{ind_text}&lt;/td&gt;
                    &lt;/tr&gt;
'''

html += '''                &lt;/tbody&gt;
            &lt;/table&gt;
        &lt;/div&gt;
        
        &lt;div class="section"&gt;
            &lt;h2&gt;会议纪要方向匹配度排名（能源/有色/化工）&lt;/h2&gt;
            &lt;table&gt;
                &lt;thead&gt;
                    &lt;tr&gt;
                        &lt;th&gt;排名&lt;/th&gt;&lt;th&gt;基金代码&lt;/th&gt;&lt;th&gt;基金名称&lt;/th&gt;
                        &lt;th&gt;质量分&lt;/th&gt;&lt;th&gt;匹配度&lt;/th&gt;&lt;th&gt;核心行业&lt;/th&gt;&lt;th&gt;投资建议&lt;/th&gt;
                    &lt;/tr&gt;
                &lt;/thead&gt;
                &lt;tbody&gt;
'''

# 按匹配度排序
matched_sorted = sorted(funds_list, key=lambda x: x['match_score'], reverse=True)[:15]
for i, f in enumerate(matched_sorted, 1):
    match = f['match_score']
    score_class = 'highlight' if match >= 30 else ''
    ind_text = ' + '.join(f['top_industries'][:2])
    
    if match >= 35:
        advice = '&lt;span class="tag tag-green"&gt;重点配置&lt;/span&gt;'
    elif match >= 25:
        advice = '&lt;span class="tag tag-blue"&gt;可配置&lt;/span&gt;'
    elif match >= 15:
        advice = '&lt;span class="tag tag-orange"&gt;观察&lt;/span&gt;'
    else:
        advice = '&lt;span class="tag tag-red"&gt;谨慎&lt;/span&gt;'
    
    html += f'''                    &lt;tr&gt;
                        &lt;td&gt;{i}&lt;/td&gt;
                        &lt;td&gt;{f['code']}&lt;/td&gt;
                        &lt;td&gt;{f['name']}&lt;/td&gt;
                        &lt;td&gt;{f['quality_score']:.1f}&lt;/td&gt;
                        &lt;td class="{score_class}"&gt;{match:.1f}%&lt;/td&gt;
                        &lt;td&gt;{ind_text}&lt;/td&gt;
                        &lt;td&gt;{advice}&lt;/td&gt;
                    &lt;/tr&gt;
'''

# 新增基金
new_codes = ['023915.OF', '022572.OF', '022148.OF', '022327.OF', '024499.OF', 
             '021145.OF', '022269.OF', '022416.OF', '024168.OF', '023448.OF']

html += '''                &lt;/tbody&gt;
            &lt;/table&gt;
        &lt;/div&gt;
        
        &lt;div class="section"&gt;
            &lt;h2&gt;本次更新新增基金（持仓数据补充）&lt;/h2&gt;
            &lt;table&gt;
                &lt;thead&gt;
                    &lt;tr&gt;
                        &lt;th&gt;基金代码&lt;/th&gt;&lt;th&gt;基金名称&lt;/th&gt;
                        &lt;th&gt;质量分&lt;/th&gt;&lt;th&gt;纪要匹配&lt;/th&gt;&lt;th&gt;核心行业&lt;/th&gt;
                    &lt;/tr&gt;
                &lt;/thead&gt;
                &lt;tbody&gt;
'''

for code in new_codes:
    f = next((x for x in funds_list if x['code'] == code), None)
    if f:
        ind_text = ' + '.join(f['top_industries'][:2])
        html += f'''                    &lt;tr&gt;
                        &lt;td&gt;{f['code']}&lt;/td&gt;
                        &lt;td&gt;{f['name']}&lt;/td&gt;
                        &lt;td&gt;{f['quality_score']:.1f}&lt;/td&gt;
                        &lt;td&gt;{f['match_score']:.1f}%&lt;/td&gt;
                        &lt;td&gt;{ind_text}&lt;/td&gt;
                    &lt;/tr&gt;
'''

html += f'''                &lt;/tbody&gt;
            &lt;/table&gt;
        &lt;/div&gt;
        
        &lt;div class="update-info"&gt;
            &lt;p&gt;数据更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}&lt;/p&gt;
            &lt;p&gt;基金产品库智能分析系统 V2.0 | 新增10只基金持仓分析&lt;/p&gt;
        &lt;/div&gt;
    &lt;/div&gt;
&lt;/body&gt;
&lt;/html&gt;
'''

# 保存
output = '/root/.openclaw/workspace/fund_data/analysis/index_v2.html'
with open(output, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"✅ 网页已生成: {output}")
print(f"📊 包含 {len(funds_list)} 只基金")
print(f"🆕 新增10只基金持仓数据")
print(f"📈 平均纪要匹配度: {sum(f['match_score'] for f in funds_list)/len(funds_list):.1f}%")
print(f"⭐ 高度匹配基金(≥30%): {len([f for f in funds_list if f['match_score'] >= 30])} 只")
