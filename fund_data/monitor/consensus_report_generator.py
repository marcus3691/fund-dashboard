#!/usr/bin/env python3
"""
基金经理共识信号报告生成器
生成周报/日报，包含股票TOP10、行业热力图、市场情绪等
"""

import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

sys.path.insert(0, '/root/.openclaw/workspace/fund_data/monitor')

from database import manager_db


class ConsensusReportGenerator:
    """
    基金经理共识信号报告生成器
    支持周报(Weekly)和日报(Daily)两种模式
    """
    
    def __init__(self, report_type: str = 'weekly'):
        """
        初始化报告生成器
        
        Args:
            report_type: 'weekly' 或 'daily'
        """
        self.report_type = report_type
        self.data_dir = '/root/.openclaw/workspace/fund_data/monitor'
        self.reports_dir = os.path.join(self.data_dir, 'reports')
        os.makedirs(self.reports_dir, exist_ok=True)
        
        # 历史数据存储路径
        self.history_dir = os.path.join(self.data_dir, 'history')
        os.makedirs(self.history_dir, exist_ok=True)
        
        # 加载当前数据
        self.current_signals = self._load_current_signals()
        self.manager_views = self._load_manager_views()
        
        # 加载历史数据进行对比
        self.previous_signals = self._load_previous_signals()
        
        # 报告生成时间
        self.report_date = datetime.now()
        
    def _load_current_signals(self) -> Dict:
        """加载当前共识信号数据"""
        signal_file = os.path.join(self.data_dir, 'manager_consensus_signals.json')
        try:
            with open(signal_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"警告: 无法加载当前信号数据: {e}")
            return {'signals': [], 'generated_at': datetime.now().isoformat()}
    
    def _load_manager_views(self) -> List[Dict]:
        """加载基金经理观点数据"""
        views_file = os.path.join(self.data_dir, 'manager_views.json')
        try:
            with open(views_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"警告: 无法加载经理观点数据: {e}")
            return []
    
    def _load_previous_signals(self) -> Dict:
        """加载上周/昨日的信号数据进行对比"""
        # 查找最近的历史文件
        history_files = []
        if os.path.exists(self.history_dir):
            for f in os.listdir(self.history_dir):
                if f.startswith('signals_') and f.endswith('.json'):
                    history_files.append(f)
        
        if not history_files:
            return None
        
        # 按日期排序，取最新的
        history_files.sort(reverse=True)
        latest_file = os.path.join(self.history_dir, history_files[0])
        
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"警告: 无法加载历史数据: {e}")
            return None
    
    def _save_current_to_history(self):
        """将当前数据保存到历史记录"""
        date_str = self.report_date.strftime('%Y%m%d')
        history_file = os.path.join(self.history_dir, f'signals_{date_str}.json')
        
        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_signals, f, ensure_ascii=False, indent=2)
            print(f"历史数据已保存: {history_file}")
        except Exception as e:
            print(f"警告: 无法保存历史数据: {e}")
    
    def analyze_stock_consensus_top10(self) -> List[Dict]:
        """
        分析股票共识TOP10
        返回被最多基金经理重仓的股票列表
        """
        stock_signals = [
            s for s in self.current_signals.get('signals', [])
            if s.get('type') == 'stock_consensus'
        ]
        
        # 按共识人数排序
        stock_signals.sort(key=lambda x: x.get('consensus_count', 0), reverse=True)
        
        top10 = []
        for signal in stock_signals[:10]:
            top10.append({
                'rank': len(top10) + 1,
                'code': signal.get('code', ''),
                'consensus_count': signal.get('consensus_count', 0),
                'avg_holding_ratio': signal.get('avg_holding_ratio', 0),
                'managers': signal.get('managers', [])[:5],  # 前5位经理
                'priority': signal.get('priority', 'medium')
            })
        
        return top10
    
    def analyze_sector_heatmap(self) -> List[Dict]:
        """
        分析行业共识热力图
        返回各行业共识度数据
        """
        sector_signals = [
            s for s in self.current_signals.get('signals', [])
            if s.get('type') == 'sector_consensus'
        ]
        
        # 按共识人数排序
        sector_signals.sort(key=lambda x: x.get('consensus_count', 0), reverse=True)
        
        # 计算最大值用于归一化热度
        max_count = max([s.get('consensus_count', 1) for s in sector_signals]) if sector_signals else 1
        
        heatmap = []
        for signal in sector_signals:
            count = signal.get('consensus_count', 0)
            heat_level = min(100, int((count / max_count) * 100)) if max_count > 0 else 0
            
            heatmap.append({
                'sector': signal.get('sector', ''),
                'consensus_count': count,
                'heat_level': heat_level,
                'managers': signal.get('managers', [])[:3],
                'stocks': signal.get('stocks', [])[:3]
            })
        
        return heatmap
    
    def analyze_market_sentiment(self) -> Dict:
        """
        分析市场情绪指标
        """
        perf_signals = [
            s for s in self.current_signals.get('signals', [])
            if s.get('type') == 'performance_consensus'
        ]
        
        if not perf_signals:
            return {
                'sentiment': 'neutral',
                'sentiment_score': 50,
                'avg_return': 0,
                'description': '暂无情绪数据'
            }
        
        perf = perf_signals[0]
        sentiment = perf.get('sentiment', 'neutral')
        avg_return = perf.get('avg_return', 0)
        
        # 计算情绪分数 (0-100)
        if sentiment == 'positive':
            score = min(100, 50 + avg_return)
        elif sentiment == 'negative':
            score = max(0, 50 - abs(avg_return))
        else:
            score = 50
        
        # 情绪描述
        descriptions = {
            'positive': f'市场情绪积极，平均收益 {avg_return}%',
            'negative': f'市场情绪谨慎，平均收益 {avg_return}%',
            'neutral': f'市场情绪中性，平均收益 {avg_return}%'
        }
        
        return {
            'sentiment': sentiment,
            'sentiment_score': round(score, 1),
            'avg_return': avg_return,
            'description': descriptions.get(sentiment, '未知')
        }
    
    def analyze_changes(self) -> Dict:
        """
        分析与上周/昨日的变化
        返回新增和退出的股票
        """
        if not self.previous_signals:
            return {
                'new_entries': [],
                'exits': [],
                'changes_summary': '无历史数据对比'
            }
        
        # 当前股票集合
        current_stocks = {
            s.get('code'): s 
            for s in self.current_signals.get('signals', [])
            if s.get('type') == 'stock_consensus'
        }
        
        # 历史股票集合
        previous_stocks = {
            s.get('code'): s 
            for s in self.previous_signals.get('signals', [])
            if s.get('type') == 'stock_consensus'
        }
        
        # 新增股票
        new_entries = []
        for code, signal in current_stocks.items():
            if code not in previous_stocks:
                new_entries.append({
                    'code': code,
                    'consensus_count': signal.get('consensus_count', 0),
                    'managers': signal.get('managers', [])[:3]
                })
        
        # 退出股票
        exits = []
        for code, signal in previous_stocks.items():
            if code not in current_stocks:
                exits.append({
                    'code': code,
                    'previous_count': signal.get('consensus_count', 0)
                })
        
        # 排名变化
        rank_changes = []
        prev_ranked = {code: idx for idx, code in enumerate(previous_stocks.keys())}
        curr_ranked = {code: idx for idx, code in enumerate(current_stocks.keys())}
        
        for code in set(current_stocks.keys()) & set(previous_stocks.keys()):
            prev_rank = prev_ranked.get(code, 999)
            curr_rank = curr_ranked.get(code, 999)
            change = prev_rank - curr_rank  # 正值表示排名上升
            
            if abs(change) >= 3:  # 只记录显著变化
                rank_changes.append({
                    'code': code,
                    'change': change,
                    'prev_rank': prev_rank + 1,
                    'curr_rank': curr_rank + 1
                })
        
        rank_changes.sort(key=lambda x: abs(x['change']), reverse=True)
        
        return {
            'new_entries': new_entries,
            'exits': exits,
            'rank_changes': rank_changes[:5],
            'changes_summary': f'新增{len(new_entries)}只，退出{len(exits)}只'
        }
    
    def generate_html_report(self) -> str:
        """
        生成HTML格式的可视化报告
        """
        # 收集数据
        stock_top10 = self.analyze_stock_consensus_top10()
        sector_heatmap = self.analyze_sector_heatmap()
        sentiment = self.analyze_market_sentiment()
        changes = self.analyze_changes()
        
        total_managers = self.current_signals.get('total_managers', 0)
        generated_at = self.current_signals.get('generated_at', '')
        
        # 报告标题
        if self.report_type == 'weekly':
            report_title = f"基金经理共识信号周报 - {self.report_date.strftime('%Y年第%W周')}"
        else:
            report_title = f"基金经理共识信号日报 - {self.report_date.strftime('%Y年%m月%d日')}"
        
        # 情绪颜色
        sentiment_colors = {
            'positive': '#4CAF50',
            'negative': '#f44336',
            'neutral': '#FFC107'
        }
        sentiment_color = sentiment_colors.get(sentiment['sentiment'], '#999')
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report_title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{ 
            max-width: 1200px; 
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
        .header .subtitle {{ opacity: 0.9; font-size: 14px; }}
        .content {{ padding: 40px; }}
        .section {{ margin-bottom: 40px; }}
        .section-title {{ 
            font-size: 20px; 
            color: #333; 
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .section-title::before {{
            content: '';
            width: 4px;
            height: 24px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 2px;
        }}
        
        /* 股票TOP10表格 */
        .stock-table {{ 
            width: 100%; 
            border-collapse: collapse;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }}
        .stock-table th {{ 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 500;
        }}
        .stock-table td {{ 
            padding: 15px;
            border-bottom: 1px solid #eee;
        }}
        .stock-table tr:hover {{ background: #f8f9ff; }}
        .stock-table tr:last-child td {{ border-bottom: none; }}
        .rank {{ 
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            font-weight: bold;
            font-size: 12px;
        }}
        .rank-1 {{ background: #FFD700; color: #333; }}
        .rank-2 {{ background: #C0C0C0; color: #333; }}
        .rank-3 {{ background: #CD7F32; color: white; }}
        .rank-other {{ background: #e0e0e0; color: #666; }}
        .priority-high {{ color: #f44336; font-weight: bold; }}
        .priority-medium {{ color: #ff9800; }}
        
        /* 行业热力图 */
        .heatmap {{ 
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}
        .heatmap-item {{ 
            padding: 20px;
            border-radius: 12px;
            color: white;
            position: relative;
            overflow: hidden;
        }}
        .heatmap-item::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, rgba(255,255,255,0.2) 0%, transparent 100%);
        }}
        .heatmap-name {{ font-size: 18px; font-weight: bold; margin-bottom: 5px; position: relative; }}
        .heatmap-count {{ font-size: 24px; font-weight: bold; position: relative; }}
        .heatmap-stocks {{ 
            font-size: 12px; 
            opacity: 0.9;
            margin-top: 8px;
            position: relative;
        }}
        
        /* 情绪指标 */
        .sentiment-card {{
            background: linear-gradient(135deg, {sentiment_color} 0%, {sentiment_color}dd 100%);
            color: white;
            padding: 30px;
            border-radius: 16px;
            text-align: center;
        }}
        .sentiment-score {{ 
            font-size: 72px; 
            font-weight: bold;
            margin: 20px 0;
        }}
        .sentiment-label {{ 
            font-size: 24px; 
            opacity: 0.95;
        }}
        .sentiment-desc {{
            margin-top: 15px;
            opacity: 0.9;
        }}
        
        /* 变化分析 */
        .changes-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}
        .change-box {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 12px;
            border-left: 4px solid #667eea;
        }}
        .change-box h4 {{ 
            color: #667eea; 
            margin-bottom: 10px;
            font-size: 16px;
        }}
        .change-item {{
            padding: 8px 0;
            border-bottom: 1px dashed #ddd;
            display: flex;
            justify-content: space-between;
        }}
        .change-item:last-child {{ border-bottom: none; }}
        .new-badge {{ 
            background: #4CAF50; 
            color: white; 
            padding: 2px 8px; 
            border-radius: 4px;
            font-size: 12px;
        }}
        .exit-badge {{ 
            background: #f44336; 
            color: white; 
            padding: 2px 8px; 
            border-radius: 4px;
            font-size: 12px;
        }}
        
        /* 统计概览 */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
        }}
        .stat-value {{ font-size: 32px; font-weight: bold; }}
        .stat-label {{ font-size: 12px; opacity: 0.9; margin-top: 5px; }}
        
        /* 响应式 */
        @media (max-width: 768px) {{
            .content {{ padding: 20px; }}
            .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
            .changes-grid {{ grid-template-columns: 1fr; }}
        }}
        
        .footer {{
            text-align: center;
            padding: 20px;
            color: #999;
            font-size: 12px;
            border-top: 1px solid #eee;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 {report_title}</h1>
            <div class="subtitle">
                基于{total_managers}位基金经理持仓数据 | 生成时间: {generated_at[:19]}
            </div>
        </div>
        
        <div class="content">
            <!-- 统计概览 -->
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{total_managers}</div>
                    <div class="stat-label">覆盖基金经理</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{len(stock_top10)}</div>
                    <div class="stat-label">高共识股票</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{len(sector_heatmap)}</div>
                    <div class="stat-label">热门行业</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{sentiment['sentiment_score']}</div>
                    <div class="stat-label">情绪指数</div>
                </div>
            </div>
            
            <!-- 市场情绪指标 -->
            <div class="section">
                <h2 class="section-title">📊 市场情绪指标</h2>
                <div class="sentiment-card">
                    <div class="sentiment-score">{sentiment['sentiment_score']}</div>
                    <div class="sentiment-label">{sentiment['description']}</div>
                    <div class="sentiment-desc">
                        平均收益率: {sentiment['avg_return']}% | 情绪状态: {'积极' if sentiment['sentiment'] == 'positive' else '谨慎' if sentiment['sentiment'] == 'negative' else '中性'}
                    </div>
                </div>
            </div>
            
            <!-- 股票共识TOP10 -->
            <div class="section">
                <h2 class="section-title">🏆 股票共识 TOP10</h2>
                <p style="color: #666; margin-bottom: 15px; font-size: 14px;">
                    被最多基金经理重仓持有的股票（共识人数 ≥ 3）
                </p>
                <table class="stock-table">
                    <thead>
                        <tr>
                            <th style="width: 60px;">排名</th>
                            <th>股票代码</th>
                            <th>共识人数</th>
                            <th>平均持仓比例</th>
                            <th>代表性基金经理</th>
                            <th>信号强度</th>
                        </tr>
                    </thead>
                    <tbody>
"""
        
        # 添加股票TOP10行
        for stock in stock_top10:
            rank_class = 'rank-1' if stock['rank'] == 1 else 'rank-2' if stock['rank'] == 2 else 'rank-3' if stock['rank'] == 3 else 'rank-other'
            priority_class = 'priority-high' if stock['priority'] == 'high' else 'priority-medium'
            priority_text = '🔥 强' if stock['priority'] == 'high' else '⚡ 中'
            managers_text = ', '.join(stock['managers'][:3])
            
            html += f"""
                        <tr>
                            <td><span class="rank {rank_class}">{stock['rank']}</span></td>
                            <td><strong>{stock['code']}</strong></td>
                            <td>{stock['consensus_count']}人</td>
                            <td>{stock['avg_holding_ratio']}%</td>
                            <td>{managers_text}</td>
                            <td class="{priority_class}">{priority_text}</td>
                        </tr>
"""
        
        html += """
                    </tbody>
                </table>
            </div>
            
            <!-- 行业共识热力图 -->
            <div class="section">
                <h2 class="section-title">🔥 行业共识热力图</h2>
                <div class="heatmap">
"""
        
        # 添加行业热力图项
        # 热力颜色映射
        def get_heat_color(level):
            if level >= 80:
                return '#f44336'  # 红 - 最热
            elif level >= 60:
                return '#ff9800'  # 橙
            elif level >= 40:
                return '#FFC107'  # 黄
            elif level >= 20:
                return '#4CAF50'  # 绿
            else:
                return '#2196F3'  # 蓝
        
        for sector in sector_heatmap[:8]:  # 只显示前8个
            color = get_heat_color(sector['heat_level'])
            stocks_text = ', '.join(sector['stocks'][:3]) if sector['stocks'] else '-'
            
            html += f"""
                    <div class="heatmap-item" style="background: {color};">
                        <div class="heatmap-name">{sector['sector']}</div>
                        <div class="heatmap-count">{sector['consensus_count']}人</div>
                        <div class="heatmap-stocks">{stocks_text}</div>
                    </div>
"""
        
        html += """
                </div>
            </div>
            
            <!-- 变化分析 -->
            <div class="section">
                <h2 class="section-title">📈 与上期对比变化</h2>
                <div class="changes-grid">
                    <div class="change-box">
                        <h4>🆕 新增共识股票</h4>
"""
        
        # 新增股票
        if changes['new_entries']:
            for entry in changes['new_entries'][:5]:
                html += f"""
                        <div class="change-item">
                            <span>{entry['code']}</span>
                            <span class="new-badge">{entry['consensus_count']}人</span>
                        </div>
"""
        else:
            html += '<div class="change-item"><span>本期无新增</span></div>'
        
        html += """
                    </div>
                    <div class="change-box">
                        <h4>🚪 退出共识股票</h4>
"""
        
        # 退出股票
        if changes['exits']:
            for exit_item in changes['exits'][:5]:
                html += f"""
                        <div class="change-item">
                            <span>{exit_item['code']}</span>
                            <span class="exit-badge">上期{exit_item['previous_count']}人</span>
                        </div>
"""
        else:
            html += '<div class="change-item"><span>本期无退出</span></div>'
        
        html += f"""
                    </div>
                </div>
                <p style="margin-top: 15px; color: #666; font-size: 14px;">
                    {changes['changes_summary']}
                </p>
            </div>
            
            <!-- 操作建议 -->
            <div class="section">
                <h2 class="section-title">💡 操作建议</h2>
                <div style="background: #f0f7ff; padding: 20px; border-radius: 12px; border-left: 4px solid #667eea;">
                    <p style="line-height: 1.8; color: #333;">
                        <strong>当前信号解读：</strong><br>
                        {self._generate_recommendation(stock_top10, sector_heatmap, sentiment)}
                    </p>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>基金经理共识信号系统 | 数据仅供参考，不构成投资建议</p>
            <p>报告生成时间: {self.report_date.strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""
        
        return html
    
    def _generate_recommendation(self, stock_top10, sector_heatmap, sentiment) -> str:
        """生成操作建议文本"""
        recommendations = []
        
        # 基于情绪
        if sentiment['sentiment'] == 'positive':
            recommendations.append("市场情绪积极，基金经理整体业绩良好，可考虑适度增加权益仓位。")
        elif sentiment['sentiment'] == 'negative':
            recommendations.append("市场情绪谨慎，建议控制仓位，关注防御性板块。")
        else:
            recommendations.append("市场情绪中性，建议保持均衡配置，精选个股。")
        
        # 基于行业
        if sector_heatmap:
            top_sector = sector_heatmap[0]
            recommendations.append(f"{top_sector['sector']}板块获得{top_sector['consensus_count']}位基金经理关注，为当前最热方向。")
        
        # 基于股票共识
        if stock_top10:
            top_stock = stock_top10[0]
            recommendations.append(f"个股方面，{top_stock['code']}获得{top_stock['consensus_count']}位基金经理重仓，共识度最高。")
        
        return '<br>'.join(recommendations)
    
    def save_report(self, html_content: str) -> str:
        """
        保存报告到文件
        
        Returns:
            报告文件路径
        """
        date_str = self.report_date.strftime('%Y%m%d')
        report_filename = f"consensus_report_{self.report_type}_{date_str}.html"
        report_path = os.path.join(self.reports_dir, report_filename)
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"报告已保存: {report_path}")
            return report_path
        except Exception as e:
            print(f"错误: 无法保存报告: {e}")
            return None
    
    def generate_and_save(self) -> Tuple[str, str]:
        """
        生成并保存报告
        
        Returns:
            (报告路径, HTML内容)
        """
        print(f"\n{'='*80}")
        print(f"开始生成{'周报' if self.report_type == 'weekly' else '日报'}...")
        print(f"{'='*80}\n")
        
        # 生成HTML
        html_content = self.generate_html_report()
        
        # 保存报告
        report_path = self.save_report(html_content)
        
        # 保存当前数据到历史记录
        self._save_current_to_history()
        
        print(f"\n{'='*80}")
        print(f"✅ {'周报' if self.report_type == 'weekly' else '日报'}生成完成!")
        print(f"{'='*80}\n")
        
        return report_path, html_content


def main():
    """
    命令行入口
    用法: python consensus_report_generator.py [weekly|daily]
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='基金经理共识信号报告生成器')
    parser.add_argument(
        'type', 
        nargs='?', 
        default='weekly',
        choices=['weekly', 'daily'],
        help='报告类型: weekly(周报) 或 daily(日报)'
    )
    parser.add_argument(
        '--output', 
        '-o',
        help='输出文件路径(可选)'
    )
    
    args = parser.parse_args()
    
    # 创建报告生成器
    generator = ConsensusReportGenerator(report_type=args.type)
    
    # 生成并保存报告
    report_path, html_content = generator.generate_and_save()
    
    if report_path:
        print(f"\n报告文件: {report_path}")
        print(f"文件大小: {os.path.getsize(report_path)} bytes")
        
        # 如果指定了输出路径，也复制一份
        if args.output:
            import shutil
            shutil.copy(report_path, args.output)
            print(f"已复制到: {args.output}")
        
        return 0
    else:
        print("\n❌ 报告生成失败")
        return 1


if __name__ == '__main__':
    sys.exit(main())
