#!/usr/bin/env python3
"""
巨潮资讯网基金季报抓取脚本
官方信息披露平台，数据权威可靠

整合功能:
1. 搜索基金并获取公告列表
2. 下载季报PDF
3. 自动解析PDF提取"投资策略和运作分析"
"""

import requests
import json
import re
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

# 添加报告解析器
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from report_parser import ReportParser, parse_report_pdf
    REPORT_PARSER_AVAILABLE = True
except ImportError:
    REPORT_PARSER_AVAILABLE = False
    print("⚠️ 警告: report_parser模块未找到，PDF解析功能不可用")

class CNInfoCrawler:
    """
    巨潮资讯网爬虫
    获取基金公告、季报、年报等官方披露信息
    """
    
    BASE_URL = "http://www.cninfo.com.cn"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'X-Requested-With': 'XMLHttpRequest'
        })
    
    def search_fund(self, fund_name: str) -> Optional[Dict]:
        """
        搜索基金/基金公司
        
        Returns:
            {
                'code': '基金代码',
                'orgId': '机构ID',
                'name': '基金名称'
            }
        """
        url = f"{self.BASE_URL}/new/information/topSearch/query"
        
        data = {
            'keyWord': fund_name,
            'maxNum': '10'
        }
        
        try:
            resp = self.session.post(url, data=data, timeout=10)
            result = resp.json()
            
            if result and len(result) > 0:
                # 返回第一个匹配结果
                item = result[0] if isinstance(result, list) else result.get('data', [{}])[0]
                return {
                    'code': item.get('code'),
                    'orgId': item.get('orgId'),
                    'name': item.get('stockName') or item.get('zwjc'),
                    'category': item.get('category')
                }
            return None
            
        except Exception as e:
            print(f"搜索基金失败: {e}")
            return None
    
    def get_fund_announcements(self, fund_code: str, org_id: str, 
                               page_num: int = 1, page_size: int = 30) -> List[Dict]:
        """
        获取基金公告列表
        
        Args:
            fund_code: 基金代码
            org_id: 机构ID
            page_num: 页码
            page_size: 每页数量
        
        Returns:
            公告列表
        """
        url = f"{self.BASE_URL}/new/hisAnnouncement/query"
        
        params = {
            'stock': fund_code,
            'tabName': 'fulltext',
            'pageNum': page_num,
            'pageSize': page_size,
            'column': 'fund',
            'category': 'category_fund_report',  # 基金报告
            'plate': 'fund',
            'orgId': org_id,
            'seDate': '',  # 时间范围
            'sortType': '0',
            'sortName': ''
        }
        
        try:
            resp = self.session.post(url, params=params, timeout=10)
            result = resp.json()
            
            if result.get('announcements'):
                return result['announcements']
            return []
            
        except Exception as e:
            print(f"获取公告列表失败: {e}")
            return []
    
    def get_quarterly_reports(self, fund_code: str, org_id: str) -> List[Dict]:
        """
        获取基金季报列表
        
        Returns:
            季报列表（包含投资策略和运作分析）
        """
        announcements = self.get_fund_announcements(fund_code, org_id)
        
        # 筛选季报
        quarterly_reports = []
        for item in announcements:
            title = item.get('announcementTitle', '')
            # 匹配季报标题
            if '季度报告' in title or '年度报告' in title or '中期报告' in title:
                quarterly_reports.append({
                    'title': title,
                    'time': item.get('announcementTime'),
                    'url': f"{self.BASE_URL}/new/disclosure/detail?orgId={org_id}&announcementId={item.get('announcementId')}",
                    'pdf_url': item.get('adjunctUrl'),  # PDF下载链接
                    'announcementId': item.get('announcementId')
                })
        
        return quarterly_reports
    
    def download_report_pdf(self, pdf_url: str) -> Optional[bytes]:
        """
        下载报告PDF
        
        Args:
            pdf_url: PDF相对路径，如 /cninfo-new/disclosure/fund/...
        
        Returns:
            PDF二进制内容
        """
        if not pdf_url:
            return None
        
        full_url = f"http://static.cninfo.com.cn/{pdf_url}"
        
        try:
            resp = self.session.get(full_url, timeout=30)
            if resp.status_code == 200:
                return resp.content
            return None
        except Exception as e:
            print(f"下载PDF失败: {e}")
            return None
    
    def extract_investment_strategy(self, fund_code: str, fund_name: str, 
                                    auto_parse: bool = True,
                                    save_pdf: bool = True,
                                    save_dir: str = None) -> Dict:
        """
        提取基金投资策略（完整流程）
        
        流程:
        1. 搜索基金获取orgId
        2. 获取最新季报
        3. 下载PDF
        4. 解析PDF提取策略章节
        
        Args:
            fund_code: 基金代码
            fund_name: 基金名称
            auto_parse: 是否自动解析PDF
            save_pdf: 是否保存PDF文件
            save_dir: PDF保存目录
            
        Returns:
            {
                'success': bool,
                'fund_code': str,
                'fund_name': str,
                'latest_report': {
                    'title': str,
                    'date': str,
                    'strategy_text': str,      # 投资策略章节文本
                    'strategy_analysis': dict,  # 智能分析结果
                    'pdf_path': str,           # 本地PDF路径
                    'pdf_url': str             # 原始PDF链接
                }
            }
        """
        # 1. 搜索基金
        fund_info = self.search_fund(fund_name)
        if not fund_info:
            # 尝试用基金代码搜索
            fund_info = self.search_fund(fund_code)
        
        if not fund_info:
            return {'success': False, 'error': '未找到基金信息'}
        
        org_id = fund_info.get('orgId')
        code = fund_info.get('code') or fund_code
        name = fund_info.get('name') or fund_name
        
        # 2. 获取季报列表
        reports = self.get_quarterly_reports(code, org_id)
        
        if not reports:
            return {'success': False, 'error': '未找到季报'}
        
        # 获取最新季报
        latest = reports[0]
        
        result = {
            'success': True,
            'fund_code': code,
            'fund_name': name,
            'org_id': org_id,
            'latest_report': {
                'title': latest['title'],
                'date': latest['time'],
                'url': latest['url'],
                'pdf_url': latest['pdf_url']
            }
        }
        
        # 3. 下载PDF
        pdf_content = self.download_report_pdf(latest['pdf_url'])
        
        if not pdf_content:
            result['success'] = False
            result['error'] = 'PDF下载失败'
            return result
        
        # 4. 保存PDF（可选）
        pdf_path = None
        if save_pdf:
            if not save_dir:
                save_dir = '/root/.openclaw/workspace/fund_data/reports_pdf'
            os.makedirs(save_dir, exist_ok=True)
            
            # 生成文件名: 基金代码_基金名称_报告标题.pdf
            safe_name = re.sub(r'[\\/:*?"<>>|]', '_', name)
            safe_title = re.sub(r'[\\/:*?"<>>|]', '_', latest['title'])[:50]
            filename = f"{code}_{safe_name}_{safe_title}.pdf"
            pdf_path = os.path.join(save_dir, filename)
            
            with open(pdf_path, 'wb') as f:
                f.write(pdf_content)
            
            result['latest_report']['pdf_path'] = pdf_path
            print(f"  📄 PDF已保存: {pdf_path}")
        
        # 5. 解析PDF（可选）
        if auto_parse and REPORT_PARSER_AVAILABLE:
            print(f"  🔍 正在解析PDF...")
            parser = ReportParser()
            parse_result = parser.parse_from_bytes(pdf_content, code, name)
            
            if parse_result.get('success'):
                strategy_section = parse_result.get('strategy_section', {})
                result['latest_report']['strategy_text'] = strategy_section.get('content')
                result['latest_report']['strategy_pages'] = f"{strategy_section.get('start_page')}-{strategy_section.get('end_page')}"
                result['latest_report']['strategy_analysis'] = parse_result.get('analysis')
                print(f"  ✅ 成功提取策略章节 ({len(strategy_section.get('content', ''))} 字符)")
            else:
                result['latest_report']['parse_error'] = parse_result.get('error')
                print(f"  ⚠️ PDF解析失败: {parse_result.get('error')}")
        
        return result

    def batch_extract_strategies(self, fund_list: List[Dict], 
                                  save_results: bool = True,
                                  output_file: str = None) -> Dict:
        """
        批量提取多个基金的投资策略
        
        Args:
            fund_list: 基金列表，每项包含fund_code和fund_name
                      例如: [{'fund_code': '005827', 'fund_name': '易方达蓝筹精选'}, ...]
            save_results: 是否保存结果到文件
            output_file: 输出文件名
            
        Returns:
            {
                'total': int,
                'successful': int,
                'failed': int,
                'results': List[Dict],
                'output_file': str
            }
        """
        results = []
        successful = 0
        failed = 0
        
        print(f"\n{'='*70}")
        print(f"批量提取基金投资策略")
        print(f"共 {len(fund_list)} 个基金")
        print(f"{'='*70}\n")
        
        for i, fund in enumerate(fund_list, 1):
            fund_code = fund.get('fund_code') or fund.get('code')
            fund_name = fund.get('fund_name') or fund.get('name')
            
            print(f"\n[{i}/{len(fund_list)}] 处理: {fund_name} ({fund_code})")
            
            try:
                result = self.extract_investment_strategy(
                    fund_code=fund_code,
                    fund_name=fund_name,
                    auto_parse=True,
                    save_pdf=True
                )
                results.append(result)
                
                if result.get('success'):
                    successful += 1
                    if 'strategy_analysis' in result.get('latest_report', {}):
                        analysis = result['latest_report']['strategy_analysis']
                        sentiment = analysis.get('market_view', {}).get('sentiment_score', 0)
                        sectors = analysis.get('sector_preference', {}).get('mentioned_sectors', [])
                        print(f"    📊 市场情绪: {sentiment:+.0f} | 关注行业: {', '.join(sectors[:3]) if sectors else '无'}")
                else:
                    failed += 1
                    print(f"    ❌ 失败: {result.get('error')}")
                    
            except Exception as e:
                failed += 1
                print(f"    ❌ 异常: {e}")
                results.append({
                    'success': False,
                    'fund_code': fund_code,
                    'fund_name': fund_name,
                    'error': str(e)
                })
        
        # 保存结果
        output_path = None
        if save_results:
            import json
            
            if not output_file:
                output_file = f"batch_strategy_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            save_dir = '/root/.openclaw/workspace/fund_data/monitor/logs'
            os.makedirs(save_dir, exist_ok=True)
            output_path = os.path.join(save_dir, output_file)
            
            # 只保存成功解析的详细结果
            summary = {
                'extraction_time': datetime.now().isoformat(),
                'total': len(fund_list),
                'successful': successful,
                'failed': failed,
                'results': []
            }
            
            for r in results:
                if r.get('success') and 'strategy_analysis' in r.get('latest_report', {}):
                    summary['results'].append({
                        'fund_code': r.get('fund_code'),
                        'fund_name': r.get('fund_name'),
                        'report_title': r['latest_report'].get('title'),
                        'report_date': r['latest_report'].get('date'),
                        'strategy_summary': {
                            'char_count': len(r['latest_report'].get('strategy_text', '')),
                            'sentiment': r['latest_report']['strategy_analysis'].get('market_view', {}).get('sentiment_score'),
                            'sectors': r['latest_report']['strategy_analysis'].get('sector_preference', {}).get('mentioned_sectors'),
                            'actions': r['latest_report']['strategy_analysis'].get('position_adjustment', {}).get('actions'),
                            'has_outlook': r['latest_report']['strategy_analysis'].get('future_outlook', {}).get('has_outlook')
                        },
                        'strategy_text': r['latest_report'].get('strategy_text', '')[:1000]  # 只保存前1000字符
                    })
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 结果已保存: {output_path}")
        
        return {
            'total': len(fund_list),
            'successful': successful,
            'failed': failed,
            'results': results,
            'output_file': output_path
        }


# 测试
def test_cninfo_crawler():
    """测试巨潮资讯网爬虫"""
    print("="*70)
    print("巨潮资讯网基金季报抓取测试")
    print("="*70)
    
    crawler = CNInfoCrawler()
    
    # 测试搜索基金
    print("\n【测试1】搜索基金")
    fund_info = crawler.search_fund("易方达蓝筹精选")
    if fund_info:
        print(f"✓ 找到基金: {fund_info}")
    else:
        print("✗ 未找到基金")
    
    # 测试获取公告列表
    if fund_info:
        print("\n【测试2】获取公告列表")
        code = fund_info.get('code')
        org_id = fund_info.get('orgId')
        
        reports = crawler.get_quarterly_reports(code, org_id)
        print(f"✓ 找到 {len(reports)} 份报告")
        
        if reports:
            print(f"\n最新报告:")
            print(f"  标题: {reports[0]['title']}")
            print(f"  时间: {reports[0]['time']}")
            print(f"  PDF: {reports[0]['pdf_url']}")


def test_full_extraction():
    """测试完整提取流程（下载+解析）"""
    print("\n" + "="*70)
    print("完整提取流程测试（下载+解析）")
    print("="*70)
    
    crawler = CNInfoCrawler()
    
    # 测试单个基金完整提取
    test_fund = {
        'fund_code': '005827',
        'fund_name': '易方达蓝筹精选混合'
    }
    
    print(f"\n测试基金: {test_fund['fund_name']} ({test_fund['fund_code']})")
    print("-"*70)
    
    result = crawler.extract_investment_strategy(
        fund_code=test_fund['fund_code'],
        fund_name=test_fund['fund_name'],
        auto_parse=True,
        save_pdf=True
    )
    
    if result.get('success'):
        print("\n✅ 提取成功!")
        print(f"\n报告信息:")
        report = result['latest_report']
        print(f"  标题: {report.get('title')}")
        print(f"  日期: {report.get('date')}")
        print(f"  PDF路径: {report.get('pdf_path')}")
        
        if 'strategy_text' in report:
            print(f"\n策略章节 ({len(report['strategy_text'])} 字符):")
            print(f"  页码: {report.get('strategy_pages')}")
            print(f"\n  内容预览(前300字符):")
            print(f"  {report['strategy_text'][:300]}...")
        
        if 'strategy_analysis' in report:
            print(f"\n智能分析:")
            analysis = report['strategy_analysis']
            market = analysis.get('market_view', {})
            print(f"  市场情绪得分: {market.get('sentiment_score', 0):+.0f}")
            print(f"  关键词: {', '.join(market.get('keywords', []))}")
            
            sectors = analysis.get('sector_preference', {})
            print(f"  关注行业: {', '.join(sectors.get('mentioned_sectors', []))}")
            
            actions = analysis.get('position_adjustment', {})
            print(f"  调仓动作: {', '.join(actions.get('actions', []))}")
    else:
        print(f"\n❌ 提取失败: {result.get('error')}")


def test_batch_extraction():
    """测试批量提取"""
    print("\n" + "="*70)
    print("批量提取测试")
    print("="*70)
    
    crawler = CNInfoCrawler()
    
    # 测试基金列表
    test_funds = [
        {'fund_code': '005827', 'fund_name': '易方达蓝筹精选混合'},
        {'fund_code': '000083', 'fund_name': '汇添富消费行业混合'},
        {'fund_code': '110022', 'fund_name': '易方达消费行业股票'},
    ]
    
    result = crawler.batch_extract_strategies(
        fund_list=test_funds,
        save_results=True
    )
    
    print(f"\n{'='*70}")
    print(f"批量处理完成!")
    print(f"  总计: {result['total']}")
    print(f"  成功: {result['successful']}")
    print(f"  失败: {result['failed']}")
    if result.get('output_file'):
        print(f"  结果文件: {result['output_file']}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--full':
        test_full_extraction()
    elif len(sys.argv) > 1 and sys.argv[1] == '--batch':
        test_batch_extraction()
    else:
        test_cninfo_crawler()
        print("\n" + "="*70)
        print("提示: 使用 --full 参数测试完整提取流程")
        print("      使用 --batch 参数测试批量提取")
        print("="*70)
