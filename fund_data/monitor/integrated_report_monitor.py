#!/usr/bin/env python3
"""
基金季报文本监控系统
整合 cninfo_crawler + report_parser 到现有监控体系

功能:
1. 自动抓取最新季报PDF
2. 提取"投资策略和运作分析"章节
3. 智能分析（市场情绪、行业偏好、调仓思路等）
4. 生成监控报告并发送邮件通知
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Optional

sys.path.insert(0, '/root/.openclaw/workspace/fund_data/monitor')

from cninfo_crawler import CNInfoCrawler
from report_parser import ReportParser, BatchReportParser


class ReportTextMonitor:
    """
    基金季报文本监控器
    监控基金经理在季报中披露的"投资策略和运作分析"
    """
    
    def __init__(self, 
                 pdf_save_dir: str = None,
                 parsed_output_dir: str = None,
                 state_file: str = None):
        """
        初始化监控器
        
        Args:
            pdf_save_dir: PDF文件保存目录
            parsed_output_dir: 解析结果输出目录
            state_file: 状态文件路径（用于记录已处理的报告）
        """
        self.pdf_save_dir = pdf_save_dir or '/root/.openclaw/workspace/fund_data/reports_pdf'
        self.parsed_output_dir = parsed_output_dir or '/root/.openclaw/workspace/fund_data/reports_parsed'
        self.state_file = state_file or '/root/.openclaw/workspace/fund_data/monitor/logs/report_monitor_state.json'
        
        os.makedirs(self.pdf_save_dir, exist_ok=True)
        os.makedirs(self.parsed_output_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        
        self.crawler = CNInfoCrawler()
        self.processed_reports = self._load_state()
        
    def _load_state(self) -> Dict:
        """加载已处理报告的状态"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ 加载状态文件失败: {e}")
        return {'processed': []}
    
    def _save_state(self):
        """保存处理状态"""
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.processed_reports, f, ensure_ascii=False, indent=2)
    
    def is_report_processed(self, announcement_id: str) -> bool:
        """检查报告是否已处理"""
        return announcement_id in self.processed_reports.get('processed', [])
    
    def mark_report_processed(self, announcement_id: str):
        """标记报告为已处理"""
        if 'processed' not in self.processed_reports:
            self.processed_reports['processed'] = []
        self.processed_reports['processed'].append(announcement_id)
        self._save_state()
    
    def monitor_fund_quarterly(self, fund_code: str, fund_name: str, 
                               force_update: bool = False) -> Dict:
        """
        监控单个基金的最新季报
        
        Args:
            fund_code: 基金代码
            fund_name: 基金名称
            force_update: 强制重新处理（即使已处理过）
            
        Returns:
            Dict: 监控结果
        """
        print(f"\n{'='*60}")
        print(f"监控基金: {fund_name} ({fund_code})")
        print(f"{'='*60}")
        
        # 搜索基金信息
        fund_info = self.crawler.search_fund(fund_name) or self.crawler.search_fund(fund_code)
        
        if not fund_info:
            return {
                'success': False,
                'fund_code': fund_code,
                'fund_name': fund_name,
                'error': '未找到基金信息'
            }
        
        code = fund_info.get('code') or fund_code
        org_id = fund_info.get('orgId')
        name = fund_info.get('name') or fund_name
        
        # 获取最新季报
        reports = self.crawler.get_quarterly_reports(code, org_id)
        
        if not reports:
            return {
                'success': False,
                'fund_code': code,
                'fund_name': name,
                'error': '未找到季报'
            }
        
        latest = reports[0]
        announcement_id = latest.get('announcementId', f"{code}_{latest.get('time', '')}")
        
        # 检查是否已处理
        if not force_update and self.is_report_processed(announcement_id):
            print(f"✓ 报告已处理过，跳过: {latest['title']}")
            return {
                'success': True,
                'fund_code': code,
                'fund_name': name,
                'status': 'skipped',
                'message': '报告已处理过',
                'report_title': latest['title']
            }
        
        print(f"📄 发现新报告: {latest['title']}")
        print(f"   日期: {latest['time']}")
        
        # 提取完整信息（下载+解析）
        result = self.crawler.extract_investment_strategy(
            fund_code=code,
            fund_name=name,
            auto_parse=True,
            save_pdf=True,
            save_dir=self.pdf_save_dir
        )
        
        if result.get('success'):
            self.mark_report_processed(announcement_id)
            
            # 生成摘要
            if 'strategy_analysis' in result.get('latest_report', {}):
                analysis = result['latest_report']['strategy_analysis']
                print(f"\n📊 分析摘要:")
                
                market = analysis.get('market_view', {})
                sentiment = market.get('sentiment_score', 0)
                sentiment_str = '看多' if sentiment > 0 else ('看空' if sentiment < 0 else '中性')
                print(f"   市场情绪: {sentiment_str} ({sentiment:+.0f})")
                
                sectors = analysis.get('sector_preference', {}).get('mentioned_sectors', [])
                print(f"   关注行业: {', '.join(sectors) if sectors else '未明确提及'}")
                
                actions = analysis.get('position_adjustment', {}).get('actions', [])
                print(f"   调仓方向: {', '.join(actions) if actions else '未明确提及'}")
                
                outlook = analysis.get('future_outlook', {})
                print(f"   未来展望: {'有' if outlook.get('has_outlook') else '无'}")
        
        return result
    
    def batch_monitor_funds(self, fund_list: List[Dict], 
                           force_update: bool = False) -> Dict:
        """
        批量监控多个基金的季报
        
        Args:
            fund_list: 基金列表 [{'fund_code': '...', 'fund_name': '...'}, ...]
            force_update: 强制更新
            
        Returns:
            Dict: 批量监控结果
        """
        print(f"\n{'='*70}")
        print(f"批量季报监控")
        print(f"共 {len(fund_list)} 个基金")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}\n")
        
        results = []
        successful = 0
        failed = 0
        skipped = 0
        new_parsed = 0
        
        for i, fund in enumerate(fund_list, 1):
            fund_code = fund.get('fund_code') or fund.get('code')
            fund_name = fund.get('fund_name') or fund.get('name')
            
            print(f"\n[{i}/{len(fund_list)}] ", end="")
            
            try:
                result = self.monitor_fund_quarterly(
                    fund_code=fund_code,
                    fund_name=fund_name,
                    force_update=force_update
                )
                results.append(result)
                
                if result.get('status') == 'skipped':
                    skipped += 1
                elif result.get('success'):
                    successful += 1
                    if 'strategy_text' in result.get('latest_report', {}):
                        new_parsed += 1
                else:
                    failed += 1
                    
            except Exception as e:
                print(f"❌ 异常: {e}")
                failed += 1
                results.append({
                    'success': False,
                    'fund_code': fund_code,
                    'fund_name': fund_name,
                    'error': str(e)
                })
        
        # 保存汇总报告
        summary = self._generate_summary_report(results)
        
        print(f"\n{'='*70}")
        print(f"监控完成!")
        print(f"  总计: {len(fund_list)}")
        print(f"  成功: {successful}")
        print(f"  跳过: {skipped}")
        print(f"  失败: {failed}")
        print(f"  新解析: {new_parsed}")
        if summary.get('report_file'):
            print(f"  报告: {summary['report_file']}")
        print(f"{'='*70}\n")
        
        return {
            'total': len(fund_list),
            'successful': successful,
            'skipped': skipped,
            'failed': failed,
            'new_parsed': new_parsed,
            'results': results,
            'summary': summary
        }
    
    def _generate_summary_report(self, results: List[Dict]) -> Dict:
        """
        生成监控汇总报告
        
        Args:
            results: 监控结果列表
            
        Returns:
            Dict: 汇总报告信息
        """
        report_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = os.path.join(self.parsed_output_dir, f'monitor_summary_{report_time}.json')
        
        # 提取有策略分析的基金
        analyzed_funds = []
        for r in results:
            if r.get('success') and 'strategy_analysis' in r.get('latest_report', {}):
                analysis = r['latest_report']['strategy_analysis']
                analyzed_funds.append({
                    'fund_code': r.get('fund_code'),
                    'fund_name': r.get('fund_name'),
                    'report_title': r['latest_report'].get('title'),
                    'report_date': r['latest_report'].get('date'),
                    'sentiment_score': analysis.get('market_view', {}).get('sentiment_score', 0),
                    'sectors': analysis.get('sector_preference', {}).get('mentioned_sectors', []),
                    'actions': analysis.get('position_adjustment', {}).get('actions', []),
                    'has_outlook': analysis.get('future_outlook', {}).get('has_outlook', False),
                    'strategy_text_preview': r['latest_report'].get('strategy_text', '')[:500]
                })
        
        # 统计行业偏好
        sector_counter = {}
        for fund in analyzed_funds:
            for sector in fund.get('sectors', []):
                sector_counter[sector] = sector_counter.get(sector, 0) + 1
        
        # 统计市场情绪分布
        sentiment_distribution = {'bullish': 0, 'neutral': 0, 'bearish': 0}
        for fund in analyzed_funds:
            score = fund.get('sentiment_score', 0)
            if score > 0:
                sentiment_distribution['bullish'] += 1
            elif score < 0:
                sentiment_distribution['bearish'] += 1
            else:
                sentiment_distribution['neutral'] += 1
        
        summary = {
            'report_time': datetime.now().isoformat(),
            'total_monitored': len(results),
            'successfully_analyzed': len(analyzed_funds),
            'sentiment_distribution': sentiment_distribution,
            'top_sectors': sorted(sector_counter.items(), key=lambda x: x[1], reverse=True)[:10],
            'analyzed_funds': analyzed_funds
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        return {
            'report_file': report_file,
            'analyzed_count': len(analyzed_funds),
            'top_sectors': summary['top_sectors'],
            'sentiment_distribution': sentiment_distribution
        }
    
    def generate_text_report(self, summary_result: Dict, output_file: str = None) -> str:
        """
        生成文本格式的监控报告（便于阅读和邮件发送）
        
        Args:
            summary_result: 汇总结果
            output_file: 输出文件路径
            
        Returns:
            str: 报告文件路径
        """
        if not output_file:
            report_time = datetime.now().strftime('%Y%m%d')
            output_file = f'/root/.openclaw/workspace/fund_data/monitor/logs/quarterly_report_text_{report_time}.md'
        
        analyzed_funds = summary_result.get('summary', {}).get('analyzed_funds', [])
        
        lines = []
        lines.append(f"# 基金季报文本监控报告")
        lines.append(f"")
        lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**监控基金数**: {summary_result.get('total', 0)}")
        lines.append(f"**成功解析**: {summary_result.get('new_parsed', 0)}")
        lines.append(f"")
        lines.append(f"---")
        lines.append(f"")
        
        # 市场情绪汇总
        sentiment_dist = summary_result.get('summary', {}).get('sentiment_distribution', {})
        lines.append(f"## 📊 市场情绪汇总")
        lines.append(f"")
        total_with_sentiment = sum(sentiment_dist.values())
        if total_with_sentiment > 0:
            lines.append(f"- 🟢 看多: {sentiment_dist.get('bullish', 0)} ({sentiment_dist.get('bullish', 0)/total_with_sentiment*100:.1f}%)")
            lines.append(f"- ⚪ 中性: {sentiment_dist.get('neutral', 0)} ({sentiment_dist.get('neutral', 0)/total_with_sentiment*100:.1f}%)")
            lines.append(f"- 🔴 看空: {sentiment_dist.get('bearish', 0)} ({sentiment_dist.get('bearish', 0)/total_with_sentiment*100:.1f}%)")
        lines.append(f"")
        
        # 热门行业
        top_sectors = summary_result.get('summary', {}).get('top_sectors', [])
        if top_sectors:
            lines.append(f"## 🔥 热门行业")
            lines.append(f"")
            for sector, count in top_sectors[:5]:
                lines.append(f"- {sector}: {count}个基金提及")
            lines.append(f"")
        
        # 各基金详细分析
        lines.append(f"## 📋 各基金策略分析")
        lines.append(f"")
        
        for fund in analyzed_funds:
            lines.append(f"### {fund.get('fund_name')} ({fund.get('fund_code')})")
            lines.append(f"")
            lines.append(f"**报告**: {fund.get('report_title')}")
            lines.append(f"")
            
            sentiment = fund.get('sentiment_score', 0)
            sentiment_icon = '🟢' if sentiment > 0 else ('🔴' if sentiment < 0 else '⚪')
            lines.append(f"**市场情绪**: {sentiment_icon} {sentiment:+.0f}")
            
            sectors = fund.get('sectors', [])
            if sectors:
                lines.append(f"**关注行业**: {', '.join(sectors)}")
            
            actions = fund.get('actions', [])
            if actions:
                lines.append(f"**调仓动作**: {', '.join(actions)}")
            
            lines.append(f"")
            lines.append(f"**策略摘要**:")
            preview = fund.get('strategy_text_preview', '')
            if preview:
                lines.append(f"> {preview}...")
            lines.append(f"")
            lines.append(f"---")
            lines.append(f"")
        
        # 保存报告
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print(f"📄 文本报告已生成: {output_file}")
        return output_file


# ============ 便捷函数 ============

def run_quarterly_text_monitor(fund_list: List[Dict] = None, 
                                force_update: bool = False,
                                generate_report: bool = True) -> Dict:
    """
    运行季报文本监控（便捷函数，可集成到主监控系统）
    
    Args:
        fund_list: 监控基金列表，为None时使用核心基金列表
        force_update: 强制更新
        generate_report: 是否生成文本报告
        
    Returns:
        Dict: 监控结果
    """
    # 默认使用核心基金列表
    if fund_list is None:
        try:
            from manager_tiers import CORE_MANAGERS
            fund_list = [{'fund_code': code, 'fund_name': name} 
                        for code, name in CORE_MANAGERS[:20]]  # 先监控前20个
        except ImportError:
            print("⚠️ 无法导入核心基金列表，使用测试列表")
            fund_list = [
                {'fund_code': '005827', 'fund_name': '易方达蓝筹精选混合'},
                {'fund_code': '000083', 'fund_name': '汇添富消费行业混合'},
                {'fund_code': '110022', 'fund_name': '易方达消费行业股票'},
            ]
    
    monitor = ReportTextMonitor()
    result = monitor.batch_monitor_funds(fund_list, force_update=force_update)
    
    if generate_report and result.get('successful', 0) > 0:
        text_report = monitor.generate_text_report(result)
        result['text_report'] = text_report
    
    return result


# ============ 测试 ============

def test_monitor():
    """测试季报文本监控器"""
    print("="*70)
    print("基金季报文本监控器测试")
    print("="*70)
    
    # 测试基金
    test_funds = [
        {'fund_code': '005827', 'fund_name': '易方达蓝筹精选混合'},
        {'fund_code': '000083', 'fund_name': '汇添富消费行业混合'},
    ]
    
    result = run_quarterly_text_monitor(
        fund_list=test_funds,
        force_update=True,
        generate_report=True
    )
    
    print(f"\n测试结果:")
    print(f"  总计: {result.get('total')}")
    print(f"  成功: {result.get('successful')}")
    print(f"  失败: {result.get('failed')}")
    
    if result.get('text_report'):
        print(f"  报告: {result['text_report']}")


if __name__ == "__main__":
    test_monitor()
