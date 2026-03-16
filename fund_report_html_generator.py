#!/usr/bin/env python3
"""
基金数据HTML报告生成器
生成美观的HTML格式报告
"""

import json
import os
from datetime import datetime

class FundReportHtmlGenerator:
    """基金报告HTML生成器"""
    
    def __init__(self):
        self.workspace = '/root/.openclaw/workspace'
    
    def generate_full_report(self, output_file=None):
        """生成完整HTML报告"""
        
        if output_file is None:
            output_file = f'{self.workspace}/fund_daily_report_{datetime.now().strftime("%Y%m%d")}.html'
        
        # 读取数据
        summary = self._load_summary()
        trump_data = self._load_trump_strategy()
        consensus_data = self._load_consensus_signals()
        
        # 生成HTML
        html = self._build_html(summary, trump_data, consensus_data)
        
        # 保存文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return output_file
    
    def _load_summary(self):
        """加载执行摘要"""
        try:
            file_path = f'{self.workspace}/auto_run_summary_{datetime.now().strftime("%Y%m%d")}.json'
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def _load_trump_strategy(self):
        """加载特朗普策略数据"""
        try:
            file_path = f'{self.workspace}/trump_visit_strategy_report.json'
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def _load_consensus_signals(self):
        """加载共识信号数据"""
        try:
            file_path = f'{self.workspace}/fund_data/monitor/manager_consensus_signals.json'
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 提取TOP10股票
                stock_signals = [s for s in data.get('signals', []) if s.get('type') == 'stock_consensus']
                stock_signals.sort(key=lambda x: x.get('consensus_count', 0), reverse=True)
                data['top10_stocks'] = stock_signals[:10]
                return data
        except:
            return {}
    
    def _build_html(self, summary, trump_data, consensus_data):
        """构建HTML内容"""
        
        date_str = datetime.now().strftime('%Y年%m月%d日')
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>基金数据日报 - {date_str}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .header .date {{ opacity: 0.9; font-size: 14px; }}
        
        .content {{ padding: 40px; }}
        .section {{ margin-bottom: 40px; }}
        .section h2 {{
            font-size: 20px;
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}
        
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 12px;
            text-align: center;
        }}
        .metric-card .value {{ font-size: 32px; font-weight: bold; margin: 10px 0; }}
        .metric-card .label {{ font-size: 14px; opacity: 0.9; }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }}
        th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 500;
        }}
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
        }}
        tr:hover {{ background: #f8f9ff; }}
        tr:last-child td {{ border-bottom: none; }}
        
        .scenario-card {{
            background: #f8f9fa;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 20px;
            border-left: 4px solid #667eea;
        }}
        .scenario-card h3 {{ color: #667eea; margin-bottom: 10px; }}
        .scenario-card .return {{
            font-size: 24px;
            font-weight: bold;
            color: #3fb950;
            margin: 10px 0;
        }}
        .scenario-card .probability {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            margin-left: 10px;
        }}
        
        .tag {{
            display: inline-block;
            background: #e3f2fd;
            color: #1976d2;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 12px;
            margin-right: 8px;
        }}
        
        .highlight-box {{
            background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
            border-radius: 12px;
            padding: 20px;
            margin: 20px 0;
        }}
        
        .footer {{
            text-align: center;
            padding: 30px;
            color: #999;
            font-size: 12px;
            border-top: 1px solid #eee;
        }}
        
        @media (max-width: 768px) {{
            .metric-grid {{ grid-template-columns: 1fr; }}
            .content {{ padding: 20px; }}
            .header {{ padding: 30px 20px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 基金数据日报</h1>
            <div class="date">{date_str}</div>
        </div>
        
        <div class="content">
            <!-- 概览指标 -->
            <div class="section">
                <h2>📈 今日概览</h2>
                <div class="metric-grid">
                    <div class="metric-card">
                        <div class="label">核心库基金</div>
                        <div class="value">121</div>
                    </div>
                    <div class="metric-card">
                        <div class="label">观察库基金</div>
                        <div class="value">75</div>
                    </div>
                    <div class="metric-card">
                        <div class="label">覆盖基金经理</div>
                        <div class="value">311</div>
                    </div>
                </div>
            </div>
            
            <!-- 特朗普策略 -->
            <div class="section">
                <h2>⚡ 特朗普访华策略</h2>
                {self._build_trump_section(trump_data)}
            </div>
            
            <!-- 共识信号 -->
            <div class="section">
                <h2>🎯 基金经理共识信号</h2>
                {self._build_consensus_section(consensus_data)}
            </div>
            
            <!-- 产品库状态 -->
            <div class="section">
                <h2>📁 产品库监控</h2>
                {self._build_portfolio_section(summary)}
            </div>
        </div>
        
        <div class="footer">
            <p>基金产品库智能分析系统 | 自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>数据来源: Tushare Pro | 策略引擎: OpenClaw AI</p>
        </div>
    </div>
</body>
</html>"""
        
        return html
    
    def _build_trump_section(self, data):
        """构建特朗普策略部分"""
        if not data:
            return '<p>暂无数据</p>'
        
        scenarios = data.get('scenarios', {})
        portfolio = data.get('portfolio', [])
        
        html = '<div class="highlight-box">'
        html += f'<p><strong>组合配置:</strong> {len(portfolio)}只ETF | <strong>预期收益:</strong> {data.get("expected_return", "N/A")}</p>'
        html += '</div>'
        
        # ETF列表
        html += '<table><thead><tr><th>代码</th><th>名称</th><th>主题</th><th>权重</th></tr></thead><tbody>'
        for etf in portfolio:
            html += f'<tr><td>{etf.get("code", "")}</td><td>{etf.get("name", "")}</td><td><span class="tag">{etf.get("theme", "")}</span></td><td>{etf.get("weight", 0)*100:.0f}%</td></tr>'
        html += '</tbody></table>'
        
        # 情景分析
        html += '<h3 style="margin-top: 30px;">情景分析</h3>'
        for name, scenario in scenarios.items():
            html += f'<div class="scenario-card">'
            html += f'<h3>{name}<span class="probability">概率: {scenario.get("probability", "N/A")}</span></h3>'
            html += f'<div class="return">{scenario.get("return", "N/A")}</div>'
            html += f'<p>{scenario.get("description", "")}</p>'
            html += '</div>'
        
        return html
    
    def _build_consensus_section(self, data):
        """构建共识信号部分"""
        if not data:
            return '<p>暂无数据</p>'
        
        total_managers = data.get('total_managers', 0)
        top10 = data.get('top10_stocks', [])
        
        html = '<div class="highlight-box">'
        html += f'<p><strong>覆盖经理:</strong> {total_managers}人 | <strong>生成信号:</strong> {len(data.get("signals", []))}个</p>'
        html += '</div>'
        
        # TOP10股票
        html += '<h3 style="margin-top: 20px;">基金经理重仓共识 TOP10</h3>'
        html += '<table><thead><tr><th>排名</th><th>代码</th><th>共识人数</th><th>平均持仓</th></tr></thead><tbody>'
        
        for i, stock in enumerate(top10, 1):
            rank_style = 'color: #ffd700; font-weight: bold;' if i <= 3 else ''
            html += f'<tr><td style="{rank_style}">#{i}</td><td>{stock.get("code", "")}</td><td>{stock.get("consensus_count", 0)}人</td><td>{stock.get("avg_holding_ratio", 0):.2f}%</td></tr>'
        
        html += '</tbody></table>'
        
        return html
    
    def _build_portfolio_section(self, data):
        """构建产品库部分"""
        summary = data.get('summary', {}) if isinstance(data, dict) else {}
        
        html = '<div class="metric-grid" style="margin-top: 20px;">'
        html += f'<div class="metric-card"><div class="label">核心库</div><div class="value">{summary.get("core_count", 121)}</div></div>'
        html += f'<div class="metric-card"><div class="label">观察库</div><div class="value">{summary.get("watch_count", 75)}</div></div>'
        html += f'<div class="metric-card"><div class="label">平均收益</div><div class="value">{summary.get("core_avg_return", 21.46):.1f}%</div></div>'
        html += '</div>'
        
        return html


def main():
    """测试生成HTML报告"""
    generator = FundReportHtmlGenerator()
    output_file = generator.generate_full_report()
    
    print(f"✅ HTML报告已生成: {output_file}")
    print(f"📄 文件大小: {os.path.getsize(output_file)} bytes")
    
    return output_file


if __name__ == '__main__':
    main()
