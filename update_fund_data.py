import json
import pandas as pd
import os

# 读取现有数据
with open('/root/.openclaw/workspace/fund_data/analysis/data.json', 'r') as f:
    existing_data = json.load(f)

# 读取基金基础数据
df = pd.read_csv('/root/.openclaw/workspace/fund_data/equity_selected_2025_deduplicated.csv')

# 新增基金代码
new_codes = ['023915.OF', '022572.OF', '022148.OF', '022327.OF', '024499.OF', 
             '021145.OF', '022269.OF', '022416.OF', '024168.OF', '023448.OF']

holdings_dir = '/root/.openclaw/workspace/fund_data/holdings'

# 股票行业映射
stock_industry = {
    # 能源
    '601225.SH': '煤炭', '600938.SH': '石油', '000933.SZ': '煤炭',
    '600256.SH': '石油/天然气', '600348.SH': '煤炭', '601666.SH': '煤炭',
    '601088.SH': '煤炭', '601001.SH': '煤炭',
    
    # 有色/稀土
    '603993.SH': '有色', '600362.SH': '有色', '000630.SZ': '有色',
    '600259.SH': '有色/稀土', '000657.SZ': '有色', '600111.SH': '稀土',
    '000960.SZ': '有色', '601899.SH': '有色/黄金', '000408.SZ': '有色/锂矿',
    '603799.SH': '有色', '000807.SZ': '有色', '600595.SH': '有色',
    '600549.SH': '有色/稀土', '601600.SH': '有色',
    
    # 化工
    '601233.SH': '化工', '300487.SZ': '化工', '600426.SH': '化工',
    '002064.SZ': '化工', '600160.SH': '化工', '000830.SZ': '化工',
    '600141.SH': '化工', '603379.SH': '化工', '002493.SZ': '化工',
    '603225.SH': '化工', '000703.SZ': '化工', '600075.SH': '化工',
    
    # 电网/电力设备
    '002028.SZ': '电网设备', '600406.SH': '电网设备', '601669.SH': '电力',
    '600900.SH': '水电', '603191.SH': '电网设备',
    
    # 光伏/新能源
    '688599.SH': '光伏', '002459.SZ': '光伏', '300274.SZ': '光伏',
    '600438.SH': '光伏', '300014.SZ': '锂电池', '300750.SZ': '锂电池',
    '000408.SZ': '锂矿', '002466.SZ': '天齐锂业',
    
    # 半导体/科技
    '002049.SZ': '半导体', '688981.SH': '半导体', '603501.SH': '半导体',
    '688012.SH': '半导体设备', '688017.SH': '机器人', '688378.SH': '半导体设备',
    '0981.HK': '半导体',
    
    # 汽车/制造
    '601689.SH': '汽车零部件', '002050.SZ': '汽车零部件',
    '002176.SZ': '电机', '601058.SH': '汽车零部件', '600686.SH': '汽车',
    '002342.SZ': '机械', '920037.BJ': '其他',
    
    # 银行/金融
    '002142.SZ': '银行', '600036.SH': '招商银行', '601398.SH': '工商银行',
    '601318.SH': '中国平安', '600919.SH': '银行',
    
    # 白酒/消费
    '600519.SH': '白酒', '000568.SZ': '白酒', '000858.SZ': '五粮液',
    
    # 航运/其他
    '600026.SH': '航运', '601872.SH': '航运', '600760.SH': '军工',
    '601989.SH': '军工', '301503.SZ': '其他', '688355.SH': '其他',
    '600051.SH': '其他', '301065.SZ': '其他', '688517.SH': '其他',
}

# 会议纪要方向匹配
def calculate_match_score(industry_dist):
    """计算与会议纪要方向的匹配度"""
    meeting_keywords = {
        "能源安全": ["煤炭", "石油", "天然气"],
        "有色/稀土": ["有色", "稀土"],
        "化工": ["化工"],
        "电网设备": ["电网设备"],
        "光伏": ["光伏"],
        "半导体": ["半导体"],
    }
    
    matched_ratio = 0
    for direction, keywords in meeting_keywords.items():
        for ind, ratio in industry_dist.items():
            if any(kw in ind for kw in keywords):
                matched_ratio += ratio
    
    return matched_ratio

# 为每只新基金生成数据
for code in new_codes:
    fund_info = df[df['ts_code'] == code]
    if fund_info.empty:
        continue
    
    holdings_file = f"{holdings_dir}/{code}_holdings.csv"
    if not os.path.exists(holdings_file):
        continue
    
    try:
        holdings_df = pd.read_csv(holdings_file)
        
        # 获取最新季度
        if 'quarter' in holdings_df.columns:
            latest_q = holdings_df['quarter'].max()
            holdings_df = holdings_df[holdings_df['quarter'] == latest_q]
        
        # 分析行业分布
        industry_dist = {}
        for _, row in holdings_df.iterrows():
            symbol = row.get('symbol', '')
            ratio = row.get('stk_mkv_ratio', 0)
            industry = stock_industry.get(symbol, '其他')
            industry_dist[industry] = industry_dist.get(industry, 0) + ratio
        
        # 计算匹配度
        match_score = calculate_match_score(industry_dist)
        
        # 构建数据
        fund_data = {
            "name": fund_info.iloc[0]['name'],
            "code": code,
            "category": fund_info.iloc[0]['invest_type'],
            "annual_return": float(fund_info.iloc[0]['return_1y']),
            "sharpe": float(fund_info.iloc[0]['sharpe']),
            "volatility": float(fund_info.iloc[0]['volatility']),
            "max_drawdown": float(fund_info.iloc[0]['max_drawdown']),
            "quality_score": float(fund_info.iloc[0]['quality_score']),
            "match_score": round(match_score, 1),
            "industry_distribution": dict(sorted(industry_dist.items(), key=lambda x: x[1], reverse=True)),
            "top_holdings": holdings_df[['symbol', 'stk_mkv_ratio']].head(10).to_dict('records')
        }
        
        existing_data[code] = fund_data
        print(f"✅ 已添加: {code} {fund_data['name']} - 匹配度: {match_score:.1f}%")
        
    except Exception as e:
        print(f"❌ 处理 {code} 失败: {e}")

# 保存更新后的数据
with open('/root/.openclaw/workspace/fund_data/analysis/data.json', 'w', encoding='utf-8') as f:
    json.dump(existing_data, f, ensure_ascii=False, indent=2)

print(f"\n✅ 数据更新完成！当前基金总数: {len(existing_data)}")
