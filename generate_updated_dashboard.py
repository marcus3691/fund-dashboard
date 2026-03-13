import json
import pandas as pd
from datetime import datetime

# 读取数据
with open('/root/.openclaw/workspace/fund_data/analysis/data.json', 'r') as f:
    fund_data = json.load(f)

# 转换为列表并排序
funds = []
for code, data in fund_data.items():
    data['code'] = code
    funds.append(data)

# 按质量分排序
top_funds = sorted(funds, key=lambda x: x.get('quality_score', 0), reverse=True)[:20]

# 按匹配度排序
top_matched = sorted(funds, key=lambda x: x.get('match_score', 0), reverse=True)[:15]

# 生成HTML
html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>基金产品库智能分析系统 - 更新版</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', sans-serif; background: #f5f7fa; color: #333; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .header p {{ opacity: 0.9; }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .stat-card {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); text-align: center; }}
        .stat-card h3 {{ color: #667eea; font-size: 32px; margin-bottom: 5px; }}
        .stat-card p {{ color: #666; }}
        .section {{ background: white; margin: 20px 0; padding: 25px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .section h2 {{ color: #333; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #667eea; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f8f9fa; font-weight: 600; color: #555; }}
        tr:hover {{ background: #f8f9fa; }}
        .tag {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 500; }}
        .tag-high {{ background: #e8f5e9; color: #2e7d32; }}
        .tag-medium {{ background: #fff3e0; color: #ef6c00; }}
        .tag-low {{ background: #ffebee; color: #c62828; }}
        .score {{ font-weight: 600; }}
        .score-high {{ color: #2e7d32; }}
        .score-medium {{ color: #ef6c00; }}
        .score-low {{ color: #c62828; }}
        .update-time {{ text-align: center; color: #999; margin-top: 30px; padding: 20px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>基金产品库智能分析系统</h1>
        <p>基于AI驱动的公募基金智能筛选与持仓分析平台</p>
    </div>
    
    <div class="container">
        <!-- 统计卡片 -->
        <div class="stats">
            <div class="stat-card">
                <h3>{len(funds)}</h3>
                <p>入库基金总数</p>
            </div>
            <div class="stat-card">
                <h3>{sum(f['annual_return'] for f in funds)/len(funds):.1f}%</h3>
                <p>平均年化收益</p>
            </div>
            <div class="stat-card">
                <h3>{sum(f.get('match_score', 0) for f in funds)/len(funds):.1f}%</h3>
                <p>平均纪要匹配度</p>
            </div>
            <div class="stat-card">
                <h3>{len([f for f in funds if f.get('match_score', 0) >= 30])}</h3>
                <p>高度匹配基金</p>
            </div>
        </div>
        
        <!-- TOP20质量分基金 -->
        <div class="section">
            <h2>🏆 TOP20 高质量基金（按质量评分）</h2>
            <table>
                <thead>
                    <tr>
                        <th>排名</th>
                        <th>基金代码</th>
                        <th>基金名称</th>
                        <th>类型</th>
                        <th>1年收益</th>
                        <th>夏普比率</th>
                        <th>质量分</th>
                        <th>纪要匹配</th>
                    </tr>
                </thead>
                <tbody>
'''

# 添加TOP20基金
for i, f in enumerate(top_funds, 1):
    match_score = f.get('match_score', 0)
    match_class = 'tag-high' if match_score >= 30 else ('tag-medium' if match_score >= 15 else 'tag-low')
    match_text = f'{match_score:.1f}%'
    
    html_content += f'''
                    <tr>
                        <td>{i}</td>
                        <td>{f['code']}</td>
                        <td>{f['name']}</td>
                        <td>{f.get('category', '混合型')}</td>
                        <td>{f['annual_return']:.2f}%</td>
                        <td>{f['sharpe']:.2f}</td>
                        <td class="score score-high">{f['quality_score']:.1f}</td>
                        <td><span class="tag {match_class}">{match_text}</span></td>
                    </tr>
'''

html_content += '''
                </tbody>
            </table>
        </div>
        
        <!-- 纪要匹配度排名 -->
        <div class="section">
            <h2>📊 会议纪要方向匹配度排名（能源/有色/化工）</h2>
            <table>
                <thead>
                    <tr>
                        <th>排名</th>
                        <th>基金代码</th>
                        <th>基金名称</th>
                        <th>质量分</th>
                        <th>匹配度</th>
                        <th>核心持仓方向</th>
                        <th>建议</th>
                    </tr>
                </thead>
                <tbody>
'''

# 添加匹配度排名
for i, f in enumerate(top_matched, 1):
    match_score = f.get('match_score', 0)
    match_class = 'score-high' if match_score >= 30 else ('score-medium' if match_score >= 15 else 'score-low')
    
    # 获取主要行业
    industries = f.get('industry_distribution', {})
    top_ind = list(industries.keys())[:2] if industries else ['其他']
    ind_text = ' + '.join(top_ind)
    
    # 建议
    if match_score >= 35:
        advice = '<span class="tag tag-high">重点配置</span>'
    elif match_score >= 25:
        advice = '<span class="tag tag-medium">可配置</span>'
    elif match_score >= 15:
        advice = '<span class="tag tag-medium">观察</span>'
    else:
        advice = '<span class="tag tag-low">谨慎</span>'
    
    html_content += f'''
                    <tr>
                        <td>{i}</td>
                        <td>{f['code']}</td>
                        <td>{f['name']}</td>
                        <td>{f['quality_score']:.1f}</td>
                        <td class="score {match_class}">{match_score:.1f}%</td>
                        <td>{ind_text}</td>
                        <td>{advice}</td>
                    </tr>
'''

html_content += f'''
                </tbody>
            </table>
        </div>
        
        <!-- 新增基金展示 -->
        <div class="section">
            <h2>🆕 本次更新新增基金（10只）</h2>
            <table>
                <thead>
                    <tr>
                        <th>基金代码</th>
                        <th>基金名称</th>
                        <th>质量分</th>
                        <th>纪要匹配度</th>
                        <th>核心行业</th>
                    </tr>
                </thead>
                <tbody>
'''

# 新增基金
new_codes = ['023915.OF', '022572.OF', '022148.OF', '022327.OF', '024499.OF', 
             '021145.OF', '022269.OF', '022416.OF', '024168.OF', '023448.OF']

for code in new_codes:
    f = fund_data.get(code, {})
    if not f:
        continue
    
    match_score = f.get('match_score', 0)
    industries = f.get('industry_distribution', {})
    top_ind = list(industries.keys())[:2] if industries else ['其他']
    ind_text = ' + '.join(top_ind)
    
    html_content += f'''
                    <tr>
                        <td>{code}</td>
                        <td>{f.get('name', '')}</td>
                        <td>{f.get('quality_score', 0):.1f}</td>
                        <td>{match_score:.1f}%</td>
                        <td>{ind_text}</td>
                    </tr>
'''

html_content += f'''
                </tbody>
            </table>
        </div>
        
        <div class="update-time">
            <p>数据更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>基金产品库智能分析系统 V2.0</p>
        </div>
    </div>
</body>
</html>
'''

# 保存HTML
output_file = '/root/.openclaw/workspace/fund_data/analysis/index_updated_v2.html'
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"✅ 网页已生成: {output_file}")
print(f"📊 包含 {len(funds)} 只基金数据")
print(f"🆕 新增 10 只基金持仓分析")
