#!/usr/bin/env python3
"""
生成去重后的基金产品库网页
"""

import json
import pandas as pd

def generate_html():
    # 读取去重后的报告数据
    with open('fund_reports_deduplicated.json', 'r', encoding='utf-8') as f:
        fund_reports = json.load(f)
    
    # 转换为列表并计算统计数据
    funds = list(fund_reports.values())
    total_funds = len(funds)
    
    # 计算合并统计
    merged_funds = [f for f in funds if f['merged_info']['share_count'] > 1]
    total_merged = len(merged_funds)
    
    # 分类统计
    categories = {}
    for fund in funds:
        cat = fund['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(fund)
    
    # 计算指标
    avg_return = sum(f['performance']['return_1y'] for f in funds) / len(funds)
    avg_sharpe = sum(f['performance']['sharpe'] for f in funds) / len(funds)
    avg_volatility = sum(f['performance']['volatility'] for f in funds) / len(funds)
    avg_drawdown = sum(f['performance']['max_drawdown'] for f in funds) / len(funds)
    
    # 生成基金数据JS
    fund_data_js = json.dumps(fund_reports, ensure_ascii=False)
    
    # 生成HTML
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>基金产品库智能分析系统（已去重）</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif; background: #0d1117; color: #c9d1d9; line-height: 1.6; }}
        .navbar {{ background: #161b22; padding: 15px 30px; border-bottom: 1px solid #30363d; position: sticky; top: 0; z-index: 100; display: flex; align-items: center; justify-content: space-between; }}
        .navbar h1 {{ font-size: 18px; color: #58a6ff; display: inline-block; }}
        .dedup-badge {{ background: #238636; color: white; font-size: 11px; padding: 2px 8px; border-radius: 10px; margin-left: 10px; vertical-align: middle; }}
        .navbar-left {{ display: flex; align-items: center; gap: 20px; flex: 1; }}
        .search-box {{ position: relative; width: 300px; }}
        .search-box input {{ width: 100%; padding: 8px 35px 8px 15px; background: #0d1117; border: 1px solid #30363d; border-radius: 6px; color: #c9d1d9; font-size: 14px; }}
        .search-box input:focus {{ outline: none; border-color: #58a6ff; }}
        .search-box .search-icon {{ position: absolute; right: 10px; top: 50%; transform: translateY(-50%); color: #8b949e; }}
        .nav-links {{ display: flex; align-items: center; gap: 25px; }}
        .nav-links a {{ color: #8b949e; text-decoration: none; margin-left: 25px; font-size: 14px; cursor: pointer; }}
        .nav-links a:hover, .nav-links a.active {{ color: #58a6ff; }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 30px; }}
        .section {{ display: none; }}
        .section.active {{ display: block; overflow-x: hidden; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(6, 1fr); gap: 15px; margin-bottom: 30px; }}
        .metric-card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; text-align: center; }}
        .metric-card .value {{ font-size: 28px; font-weight: 600; color: #58a6ff; margin: 10px 0; }}
        .metric-card .value.small {{ font-size: 20px; }}
        .metric-card .label {{ font-size: 12px; color: #8b949e; }}
        .category-section {{ margin: 30px 0; }}
        .category-section h2 {{ font-size: 16px; margin-bottom: 20px; color: #e6edf3; }}
        .category-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 30px; }}
        .category-card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; cursor: pointer; transition: all 0.3s; }}
        .category-card:hover {{ border-color: #58a6ff; transform: translateY(-2px); box-shadow: 0 4px 12px rgba(88,166,255,0.15); }}
        .category-card h3 {{ font-size: 14px; color: #e6edf3; margin-bottom: 15px; }}
        .category-card .count {{ font-size: 32px; font-weight: 600; color: #58a6ff; margin-bottom: 10px; }}
        .category-card .stats {{ font-size: 12px; color: #8b949e; }}
        .category-card .stats span {{ display: block; margin: 3px 0; }}
        .table-container {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; overflow-x: auto; margin-top: 20px; -webkit-overflow-scrolling: touch; position: relative; }}
        table {{ width: 100%; border-collapse: collapse; min-width: 800px; }}
        th {{ background: #21262d; padding: 12px 15px; text-align: left; font-size: 12px; color: #8b949e; font-weight: 500; }}
        td {{ padding: 12px 15px; border-bottom: 1px solid #30363d; font-size: 13px; }}
        tr:hover {{ background: #21262d; }}
        tr.clickable {{ cursor: pointer; }}
        .fund-name {{ font-weight: 500; color: #e6edf3; display: flex; align-items: center; gap: 8px; }}
        .fund-code {{ font-size: 11px; color: #8b949e; }}
        .share-badge {{ background: #30363d; color: #8b949e; font-size: 10px; padding: 1px 6px; border-radius: 4px; }}
        .share-badge.merged {{ background: #238636; color: white; }}
        .share-tooltip {{ position: relative; cursor: help; }}
        .share-tooltip:hover::after {{ content: attr(data-shares); position: absolute; bottom: 100%; left: 50%; transform: translateX(-50%); background: #21262d; border: 1px solid #30363d; padding: 8px 12px; border-radius: 6px; font-size: 11px; white-space: nowrap; z-index: 100; color: #e6edf3; }}
        .rating {{ color: #ffd700; letter-spacing: 2px; }}
        .score {{ font-weight: 600; color: #58a6ff; }}
        .positive {{ color: #3fb950; }}
        .negative {{ color: #f85149; }}
        .modal-overlay {{ position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.8); z-index: 1000; display: none; align-items: center; justify-content: center; padding: 20px; }}
        .modal-overlay.active {{ display: flex; }}
        .modal-content {{ background: #161b22; border: 1px solid #30363d; border-radius: 12px; width: 100%; max-width: 900px; max-height: 90vh; overflow: hidden; display: flex; flex-direction: column; }}
        .modal-header {{ padding: 20px; border-bottom: 1px solid #30363d; display: flex; justify-content: space-between; align-items: flex-start; }}
        .modal-header h2 {{ font-size: 18px; color: #e6edf3; margin-bottom: 5px; }}
        .modal-header .subtitle {{ font-size: 12px; color: #8b949e; }}
        .modal-close {{ background: none; border: none; color: #8b949e; font-size: 24px; cursor: pointer; padding: 0; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; border-radius: 6px; }}
        .modal-close:hover {{ background: #30363d; color: #e6edf3; }}
        .modal-body {{ padding: 20px; overflow-y: auto; flex: 1; }}
        .modal-section {{ margin-bottom: 24px; }}
        .modal-section h3 {{ font-size: 14px; color: #58a6ff; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid #30363d; }}
        .modal-section p {{ font-size: 13px; line-height: 1.8; color: #c9d1d9; }}
        .modal-section ul {{ list-style: none; padding: 0; }}
        .modal-section li {{ font-size: 13px; padding: 6px 0; padding-left: 16px; position: relative; color: #c9d1d9; }}
        .modal-section li::before {{ content: "•"; color: #58a6ff; position: absolute; left: 0; }}
        .merged-info-box {{ background: rgba(35, 134, 54, 0.1); border: 1px solid #238636; border-radius: 8px; padding: 15px; margin: 15px 0; }}
        .merged-info-box h4 {{ color: #3fb950; font-size: 13px; margin-bottom: 10px; }}
        .merged-info-box .share-list {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }}
        .merged-info-box .share-tag {{ background: #238636; color: white; font-size: 11px; padding: 4px 10px; border-radius: 4px; }}
        .back-btn {{ background: #21262d; border: 1px solid #30363d; color: #8b949e; padding: 8px 16px; border-radius: 6px; cursor: pointer; margin-bottom: 20px; font-size: 13px; }}
        .back-btn:hover {{ background: #30363d; color: #e6edf3; }}
        @media (max-width: 768px) {{ .metrics-grid {{ grid-template-columns: repeat(2, 1fr); }} .category-grid {{ grid-template-columns: repeat(2, 1fr); }} .navbar-left {{ flex-direction: column; align-items: stretch; }} .search-box {{ width: 100%; }} }}
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="navbar-left">
            <h1>基金产品库智能分析系统<span class="dedup-badge">已去重</span></h1>
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="搜索基金名称或代码...">
                <span class="search-icon">🔍</span>
            </div>
        </div>
        <div class="nav-links">
            <a href="#overview" class="active" onclick="showSection('overview')">概览</a>
            <a href="#top10" onclick="showSection('top10')">TOP10</a>
        </div>
    </nav>

    <div class="container">
        <!-- 概览页 -->
        <div id="overview" class="section active">
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="label">入库基金总数</div>
                    <div class="value">{total_funds}</div>
                    <div class="label">已去重 ({total_merged}组合并)</div>
                </div>
                <div class="metric-card">
                    <div class="label">平均年化收益</div>
                    <div class="value {'positive' if avg_return > 0 else 'negative'}">{avg_return:.2f}%</div>
                </div>
                <div class="metric-card">
                    <div class="label">平均夏普比率</div>
                    <div class="value">{avg_sharpe:.2f}</div>
                </div>
                <div class="metric-card">
                    <div class="label">平均波动率</div>
                    <div class="value">{avg_volatility:.2f}%</div>
                </div>
                <div class="metric-card">
                    <div class="label">平均最大回撤</div>
                    <div class="value negative">{avg_drawdown:.2f}%</div>
                </div>
                <div class="metric-card">
                    <div class="label">基金分类</div>
                    <div class="value small">{len(categories)}类</div>
                </div>
            </div>

            <div class="category-section">
                <h2>基金分类</h2>
                <div class="category-grid" id="categoryGrid">
                    <!-- 动态生成分类卡片 -->
                </div>
            </div>
        </div>

        <!-- TOP10页 -->
        <div id="top10" class="section">
            <div class="table-container">
                <table id="top10Table">
                    <thead>
                        <tr>
                            <th>排名</th>
                            <th>基金名称</th>
                            <th>类别</th>
                            <th>近1年收益</th>
                            <th>夏普比率</th>
                            <th>综合评分</th>
                            <th>份额信息</th>
                        </tr>
                    </thead>
                    <tbody id="top10Body"></tbody>
                </table>
            </div>
        </div>

        <!-- 分类详情页 -->
        <div id="category" class="section">
            <button class="back-btn" onclick="showSection('overview')">← 返回概览</button>
            <h2 id="categoryTitle"></h2>
            <div class="table-container">
                <table id="categoryTable">
                    <thead>
                        <tr>
                            <th>排名</th>
                            <th>基金名称</th>
                            <th>近1年收益</th>
                            <th>波动率</th>
                            <th>夏普</th>
                            <th>回撤</th>
                            <th>综合分</th>
                            <th>份额</th>
                        </tr>
                    </thead>
                    <tbody id="categoryBody"></tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- 详情弹窗 -->
    <div id="fundModal" class="modal-overlay" onclick="closeModalOnBackdrop(event)">
        <div class="modal-content" onclick="event.stopPropagation()">
            <div class="modal-header">
                <div>
                    <h2 id="modalFundName"></h2>
                    <div class="subtitle" id="modalFundCode"></div>
                </div>
                <button class="modal-close" onclick="closeModal()">×</button>
            </div>
            <div class="modal-body" id="modalBody"></div>
        </div>
    </div>

    <script>
        // 基金数据
        const fundReports = {fund_data_js};
        
        // 分类数据
        const categories = {json.dumps({k: [{'name': f['name'], 'code': f['code'], 'score': f['score']} for f in v] for k, v in categories.items()}, ensure_ascii=False)};
        
        // 当前显示的基金列表
        let currentFunds = Object.values(fundReports);
        
        // 初始化
        document.addEventListener('DOMContentLoaded', function() {{
            renderOverview();
            renderTop10();
            setupSearch();
        }});
        
        // 显示页面
        function showSection(sectionId) {{
            document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
            document.getElementById(sectionId).classList.add('active');
            document.querySelectorAll('.nav-links a').forEach(a => a.classList.remove('active'));
            document.querySelector(`[href="#${{sectionId}}"]`).classList.add('active');
            
            if (sectionId === 'top10') {{
                renderTop10();
            }}
        }}
        
        // 渲染概览
        function renderOverview() {{
            const grid = document.getElementById('categoryGrid');
            grid.innerHTML = '';
            
            Object.entries(categories).forEach(([cat, funds]) => {{
                const avgScore = funds.reduce((a, b) => a + b.score, 0) / funds.length;
                const card = document.createElement('div');
                card.className = 'category-card';
                card.onclick = () => showCategory(cat);
                card.innerHTML = `
                    <h3>${{cat}}</h3>
                    <div class="count">${{funds.length}}</div>
                    <div class="stats">
                        <span>平均评分: ${{avgScore.toFixed(1)}}</span>
                        <span>最高评分: ${{Math.max(...funds.map(f => f.score)).toFixed(1)}}</span>
                    </div>
                `;
                grid.appendChild(card);
            }});
        }}
        
        // 渲染TOP10
        function renderTop10() {{
            const sorted = Object.values(fundReports).sort((a, b) => b.score - a.score).slice(0, 10);
            const tbody = document.getElementById('top10Body');
            tbody.innerHTML = '';
            
            sorted.forEach((fund, idx) => {{
                const row = document.createElement('tr');
                row.className = 'clickable';
                row.onclick = () => showFundDetail(fund.code);
                
                const merged = fund.merged_info.share_count > 1;
                const shareBadge = merged 
                    ? `<span class="share-badge merged share-tooltip" data-shares="合并: ${{fund.merged_info.merged_names}}">+${{fund.merged_info.share_count - 1}}</span>`
                    : `<span class="share-badge">${{fund.merged_info.selected_share}}</span>`;
                
                row.innerHTML = `
                    <td><strong>#${{idx + 1}}</strong></td>
                    <td>
                        <div class="fund-name">${{fund.name}}${{shareBadge}}</div>
                        <div class="fund-code">${{fund.code}}</div>
                    </td>
                    <td>${{fund.category}}</td>
                    <td class="${{fund.performance.return_1y >= 0 ? 'positive' : 'negative'}}">${{fund.performance.return_1y.toFixed(2)}}%</td>
                    <td>${{fund.performance.sharpe.toFixed(2)}}</td>
                    <td class="score">${{fund.score.toFixed(1)}}</td>
                    <td>${{fund.merged_info.selected_share}}类 ${{merged ? '(已合并' + (fund.merged_info.share_count-1) + '个)' : ''}}</td>
                `;
                tbody.appendChild(row);
            }});
        }}
        
        // 显示分类详情
        function showCategory(cat) {{
            document.getElementById('categoryTitle').textContent = cat + ' - 基金列表';
            const funds = Object.values(fundReports).filter(f => f.category === cat).sort((a, b) => b.score - a.score);
            const tbody = document.getElementById('categoryBody');
            tbody.innerHTML = '';
            
            funds.forEach((fund, idx) => {{
                const row = document.createElement('tr');
                row.className = 'clickable';
                row.onclick = () => showFundDetail(fund.code);
                
                const merged = fund.merged_info.share_count > 1;
                
                row.innerHTML = `
                    <td>${{idx + 1}}</td>
                    <td>
                        <div class="fund-name">${{fund.name}} ${{merged ? '<span class="share-badge merged">+' + (fund.merged_info.share_count-1) + '</span>' : ''}}</div>
                        <div class="fund-code">${{fund.code}}</div>
                    </td>
                    <td class="${{fund.performance.return_1y >= 0 ? 'positive' : 'negative'}}">${{fund.performance.return_1y.toFixed(2)}}%</td>
                    <td>${{fund.performance.volatility.toFixed(2)}}%</td>
                    <td>${{fund.performance.sharpe.toFixed(2)}}</td>
                    <td class="negative">${{fund.performance.max_drawdown.toFixed(2)}}%</td>
                    <td class="score">${{fund.score.toFixed(1)}}</td>
                    <td>${{fund.merged_info.selected_share}}类</td>
                `;
                tbody.appendChild(row);
            }});
            
            showSection('category');
        }}
        
        // 显示基金详情
        function showFundDetail(code) {{
            const fund = fundReports[code];
            if (!fund) return;
            
            document.getElementById('modalFundName').textContent = fund.name;
            document.getElementById('modalFundCode').textContent = `${{fund.code}} · ${{fund.category}} · ${{fund.manager}}`;
            
            const merged = fund.merged_info.share_count > 1;
            const mergedHtml = merged ? `
                <div class="modal-section">
                    <div class="merged-info-box">
                        <h4>📊 份额合并信息</h4>
                        <p>该基金有 <strong>${{fund.merged_info.share_count}}</strong> 个份额，当前展示的是 <strong>${{fund.merged_info.selected_share}}类</strong>（按优先级选择）</p>
                        <div class="share-list">
                            ${{fund.merged_info.merged_names.split(',').map(name => `<span class="share-tag">${{name}}</span>`).join('')}}
                        </div>
                    </div>
                </div>
            ` : '';
            
            document.getElementById('modalBody').innerHTML = `
                ${{mergedHtml}}
                <div class="modal-section">
                    <h3>📈 业绩表现</h3>
                    <table style="width:100%;margin-top:10px;">
                        <tr><td>近1年收益</td><td class="${{fund.performance.return_1y >= 0 ? 'positive' : 'negative'}}" style="text-align:right;font-weight:600;">${{fund.performance.return_1y.toFixed(2)}}%</td></tr>
                        <tr><td>近6月收益</td><td class="${{fund.performance.return_6m >= 0 ? 'positive' : 'negative'}}" style="text-align:right;font-weight:600;">${{fund.performance.return_6m.toFixed(2)}}%</td></tr>
                        <tr><td>年化波动率</td><td style="text-align:right;">${{fund.performance.volatility.toFixed(2)}}%</td></tr>
                        <tr><td>最大回撤</td><td class="negative" style="text-align:right;">${{fund.performance.max_drawdown.toFixed(2)}}%</td></tr>
                        <tr><td>夏普比率</td><td style="text-align:right;font-weight:600;color:#58a6ff;">${{fund.performance.sharpe.toFixed(2)}}</td></tr>
                    </table>
                </div>
                <div class="modal-section">
                    <h3>🏆 综合评分</h3>
                    <p style="font-size:24px;color:#58a6ff;font-weight:600;">${{fund.score.toFixed(1)}}分 <span style="font-size:16px;">${{fund.rating}}</span></p>
                    <p>质量评级: ${{fund.quality}}</p>
                </div>
                <div class="modal-section">
                    <h3>📊 排名情况</h3>
                    <p>近1年排名: 第 ${{fund.ranking.rank_1y}} 位</p>
                    <p>超越同类: ${{fund.ranking.percentile_1y.toFixed(1)}}%</p>
                </div>
            `;
            
            document.getElementById('fundModal').classList.add('active');
            document.body.style.overflow = 'hidden';
        }}
        
        // 关闭弹窗
        function closeModal() {{
            document.getElementById('fundModal').classList.remove('active');
            document.body.style.overflow = '';
        }}
        
        function closeModalOnBackdrop(event) {{
            if (event.target === event.currentTarget) closeModal();
        }}
        
        // 搜索功能
        function setupSearch() {{
            const input = document.getElementById('searchInput');
            input.addEventListener('input', (e) => {{
                const query = e.target.value.toLowerCase();
                if (!query) return;
                
                const results = Object.values(fundReports).filter(f => 
                    f.name.toLowerCase().includes(query) || 
                    f.code.toLowerCase().includes(query)
                );
                
                if (results.length > 0) {{
                    showSearchResults(results);
                }}
            }});
        }}
        
        function showSearchResults(results) {{
            // 简化为显示第一个结果详情
            if (results.length > 0) {{
                showFundDetail(results[0].code);
            }}
        }}
        
        // ESC键关闭弹窗
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'Escape') closeModal();
        }});
    </script>
</body>
</html>'''
    
    # 保存HTML文件
    with open('index_deduplicated.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ 去重版网页已生成: index_deduplicated.html")
    print(f"   包含 {total_funds} 只基金（已去重）")
    print(f"   其中 {total_merged} 只基金包含多份额合并信息")
    return html

if __name__ == '__main__':
    generate_html()
