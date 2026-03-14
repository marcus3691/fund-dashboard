#!/usr/bin/env python3
"""
巨潮资讯网基金季报抓取脚本
官方信息披露平台，数据权威可靠
"""

import requests
import json
import re
from datetime import datetime
from typing import Dict, List, Optional

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
    
    def extract_investment_strategy(self, fund_code: str, fund_name: str) -> Dict:
        """
        提取基金投资策略
        
        流程:
        1. 搜索基金获取orgId
        2. 获取最新季报
        3. 下载PDF并解析
        
        Returns:
            {
                'success': bool,
                'fund_code': str,
                'fund_name': str,
                'latest_report': {
                    'title': str,
                    'date': str,
                    'strategy_text': str,  # 投资策略章节文本
                    'holdings_text': str   # 持仓章节文本
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
        
        # 2. 获取季报列表
        reports = self.get_quarterly_reports(code, org_id)
        
        if not reports:
            return {'success': False, 'error': '未找到季报'}
        
        # 获取最新季报
        latest = reports[0]
        
        return {
            'success': True,
            'fund_code': code,
            'fund_name': fund_info.get('name') or fund_name,
            'org_id': org_id,
            'latest_report': {
                'title': latest['title'],
                'date': latest['time'],
                'url': latest['url'],
                'pdf_url': latest['pdf_url']
            }
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

if __name__ == "__main__":
    test_cninfo_crawler()
