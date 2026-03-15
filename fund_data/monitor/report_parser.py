#!/usr/bin/env python3
"""
基金季报PDF解析器
提取"投资策略和运作分析"章节文本及关键信息
"""

import pdfplumber
import re
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class ReportParser:
    """
    基金季报PDF解析器
    
    功能:
    1. 提取PDF全部文本
    2. 定位"投资策略和运作分析"章节
    3. 提取章节结构化内容
    4. 分析关键信息（调仓思路、市场观点等）
    """
    
    # "投资策略和运作分析"章节的多种可能标题变体
    STRATEGY_SECTION_PATTERNS = [
        r'投资策略.*?运作分析',
        r'投资策.*?运作分析',
        r'报告期内.*?投资策略',
        r'投资策略.*?(?=\n|$)',
        r'基金.*?投资策略',
        r'投资运作.*?分析',
    ]
    
    # 章节结束标记（用于定位章节边界）
    SECTION_END_MARKERS = [
        r'^\s*第[一二三四五六七八九十\d]+节',  # 下一节开始
        r'^\s*\d+\.\d+',  # 编号小节
        r'^\s*§\d+',  # 分节符
        r'投资组合报告',  # 下一章
        r'财务会计报告',
        r'管理人报告',
        r'基金份额变动',
    ]
    
    def __init__(self, pdf_path: str = None):
        self.pdf_path = pdf_path
        self.full_text = ""
        self.pages_text = []
        self.metadata = {}
        
    def load_pdf(self, pdf_path: str = None) -> bool:
        """
        加载PDF文件
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            bool: 是否成功加载
        """
        if pdf_path:
            self.pdf_path = pdf_path
            
        if not self.pdf_path or not os.path.exists(self.pdf_path):
            print(f"❌ PDF文件不存在: {self.pdf_path}")
            return False
            
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                # 提取元数据
                self.metadata = {
                    'pages': len(pdf.pages),
                    'filename': os.path.basename(self.pdf_path),
                    'file_size': os.path.getsize(self.pdf_path),
                    'parsed_at': datetime.now().isoformat()
                }
                
                # 提取每页文本
                self.pages_text = []
                self.full_text = ""
                
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text() or ""
                    self.pages_text.append({
                        'page_num': i + 1,
                        'text': text
                    })
                    self.full_text += f"\n--- Page {i+1} ---\n{text}"
                    
            return True
            
        except Exception as e:
            print(f"❌ PDF解析失败: {e}")
            return False
    
    def extract_from_bytes(self, pdf_bytes: bytes) -> bool:
        """
        从二进制数据加载PDF（用于直接下载的内容）
        
        Args:
            pdf_bytes: PDF二进制数据
            
        Returns:
            bool: 是否成功加载
        """
        try:
            import io
            
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                self.metadata = {
                    'pages': len(pdf.pages),
                    'parsed_at': datetime.now().isoformat()
                }
                
                self.pages_text = []
                self.full_text = ""
                
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text() or ""
                    self.pages_text.append({
                        'page_num': i + 1,
                        'text': text
                    })
                    self.full_text += f"\n--- Page {i+1} ---\n{text}"
                    
            return True
            
        except Exception as e:
            print(f"❌ PDF解析失败: {e}")
            return False
    
    def extract_all_text(self) -> str:
        """
        提取PDF全部文本
        
        Returns:
            str: 完整文本内容
        """
        return self.full_text
    
    def find_strategy_section(self) -> Optional[Dict]:
        """
        定位"投资策略和运作分析"章节
        
        Returns:
            Dict: 包含章节标题、内容、页码范围等
        """
        if not self.full_text:
            return None
            
        text = self.full_text
        
        # 尝试多种模式匹配章节标题
        section_start = -1
        section_title = ""
        
        for pattern in self.STRATEGY_SECTION_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                section_start = match.start()
                section_title = match.group(0).strip()
                break
        
        if section_start == -1:
            # 尝试更宽松的匹配
            # 查找包含"策略"和"运作"的段落
            alt_patterns = [
                r'报告期内基金.{0,20}策略',
                r'市场回顾.{0,50}?策略',
            ]
            for pattern in alt_patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                if match:
                    section_start = match.start()
                    section_title = "投资策略和运作分析（推测）"
                    break
        
        if section_start == -1:
            return None
        
        # 查找章节结束位置
        section_end = len(text)
        remaining_text = text[section_start:]
        
        for pattern in self.SECTION_END_MARKERS:
            match = re.search(pattern, remaining_text, re.IGNORECASE | re.MULTILINE)
            if match and match.start() > 50:  # 确保不是开头就匹配到
                section_end = section_start + match.start()
                break
        
        # 提取章节内容
        section_content = text[section_start:section_end].strip()
        
        # 清理内容
        section_content = self._clean_section_text(section_content)
        
        # 确定页码范围
        start_page = 1
        end_page = len(self.pages_text)
        
        char_count = 0
        for page_info in self.pages_text:
            page_text = page_info['text']
            page_start = char_count
            page_end = char_count + len(page_text)
            
            if page_start <= section_start < page_end:
                start_page = page_info['page_num']
            if page_start < section_end <= page_end:
                end_page = page_info['page_num']
                
            char_count += len(page_text) + len(f"\n--- Page {page_info['page_num']} ---\n")
        
        return {
            'title': section_title,
            'content': section_content,
            'start_page': start_page,
            'end_page': end_page,
            'char_count': len(section_content)
        }
    
    def _clean_section_text(self, text: str) -> str:
        """
        清理章节文本
        
        Args:
            text: 原始文本
            
        Returns:
            str: 清理后的文本
        """
        # 移除页码标记
        text = re.sub(r'\n--- Page \d+ ---\n', '\n', text)
        
        # 移除多余的空行
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # 移除页眉页脚（通常是数字或基金代码）
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # 跳过纯数字行（页码）
            if re.match(r'^\d+$', line):
                continue
            # 跳过过短的行（可能是页眉）
            if len(line) < 3 and not line.isalnum():
                continue
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def analyze_strategy_content(self, section_content: str) -> Dict:
        """
        分析投资策略内容，提取关键信息
        
        Args:
            section_content: 章节文本内容
            
        Returns:
            Dict: 结构化分析结果
        """
        if not section_content:
            return {'error': '无内容可分析'}
        
        analysis = {
            'market_view': self._extract_market_view(section_content),
            'position_adjustment': self._extract_position_adjustment(section_content),
            'sector_preference': self._extract_sector_preference(section_content),
            'risk_awareness': self._extract_risk_awareness(section_content),
            'future_outlook': self._extract_future_outlook(section_content),
        }
        
        return analysis
    
    def _extract_market_view(self, text: str) -> Dict:
        """提取市场观点"""
        # 匹配市场描述的关键词
        market_patterns = {
            'bullish': ['上涨', '反弹', '看好', '乐观', '机会', '配置价值', '吸引力'],
            'bearish': ['下跌', '调整', '谨慎', '悲观', '风险', '高估', '压力'],
            'neutral': ['震荡', '结构性', '分化', '精选', '稳健']
        }
        
        sentiment_score = 0
        found_keywords = []
        
        for sentiment, keywords in market_patterns.items():
            for keyword in keywords:
                if keyword in text:
                    found_keywords.append(keyword)
                    if sentiment == 'bullish':
                        sentiment_score += 1
                    elif sentiment == 'bearish':
                        sentiment_score -= 1
        
        # 提取具体市场描述段落
        market_paragraphs = []
        paragraphs = text.split('\n\n')
        
        for para in paragraphs[:3]:  # 通常前3段是市场表现回顾
            if any(kw in para for kw in ['市场', '指数', '行情', '走势', 'A股']):
                if len(para) > 20:
                    market_paragraphs.append(para[:200] + "..." if len(para) > 200 else para)
        
        return {
            'sentiment_score': sentiment_score,
            'keywords': list(set(found_keywords)),
            'summary_paragraphs': market_paragraphs[:2]  # 最多2段
        }
    
    def _extract_position_adjustment(self, text: str) -> Dict:
        """提取调仓思路"""
        # 调仓相关关键词
        adjustment_keywords = [
            '增持', '减持', '加仓', '减仓', '配置', '调整', '优化',
            '集中度', '分散', '精选', '调仓', '换股'
        ]
        
        found_actions = []
        for keyword in adjustment_keywords:
            if keyword in text:
                found_actions.append(keyword)
        
        # 提取调仓描述段落
        adjustment_paragraphs = []
        paragraphs = text.split('\n\n')
        
        for para in paragraphs:
            if any(kw in para for kw in adjustment_keywords):
                if len(para) > 30:
                    adjustment_paragraphs.append(para[:300] + "..." if len(para) > 300 else para)
        
        return {
            'actions': list(set(found_actions)),
            'descriptions': adjustment_paragraphs[:3]  # 最多3段
        }
    
    def _extract_sector_preference(self, text: str) -> Dict:
        """提取行业偏好"""
        # 常见行业关键词
        sector_keywords = {
            '科技': ['科技', 'TMT', '电子', '计算机', '半导体', '芯片', '人工智能', 'AI'],
            '消费': ['消费', '白酒', '医药', '医疗', '食品饮料', '家电', '零售'],
            '周期': ['周期', '化工', '有色', '钢铁', '煤炭', '建材', '石油'],
            '金融': ['金融', '银行', '保险', '证券', '地产', '房地产'],
            '新能源': ['新能源', '光伏', '电动车', '锂电', '储能', '碳中和'],
            '制造': ['制造', '机械', '汽车', '军工', '高端制造', '装备']
        }
        
        found_sectors = {}
        for sector, keywords in sector_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    if sector not in found_sectors:
                        found_sectors[sector] = []
                    found_sectors[sector].append(keyword)
        
        return {
            'mentioned_sectors': list(found_sectors.keys()),
            'sector_keywords': found_sectors
        }
    
    def _extract_risk_awareness(self, text: str) -> Dict:
        """提取风险提示"""
        risk_keywords = [
            '风险', '波动', '不确定性', '压力', '挑战', '谨慎', '警惕',
            '回调', '下行', '冲击', '扰动', '影响'
        ]
        
        risk_mentions = []
        paragraphs = text.split('\n\n')
        
        for para in paragraphs:
            if any(kw in para for kw in risk_keywords):
                # 筛选出包含风险提示的段落
                if '风险' in para or '波动' in para or '不确定性' in para:
                    if len(para) > 20:
                        risk_mentions.append(para[:250] + "..." if len(para) > 250 else para)
        
        return {
            'has_risk_warning': len(risk_mentions) > 0,
            'risk_mentions': risk_mentions[:2]  # 最多2条
        }
    
    def _extract_future_outlook(self, text: str) -> Dict:
        """提取未来展望"""
        # 展望相关标记词
        outlook_markers = ['展望', '未来', '下季度', '下一步', '后市', '中长期']
        
        outlook_paragraphs = []
        paragraphs = text.split('\n\n')
        
        # 通常展望在章节后半部分
        for para in paragraphs[-5:]:  # 最后5段
            if any(marker in para for marker in outlook_markers):
                if len(para) > 30:
                    outlook_paragraphs.append(para[:300] + "..." if len(para) > 300 else para)
        
        return {
            'has_outlook': len(outlook_paragraphs) > 0,
            'outlook_content': outlook_paragraphs[:2]  # 最多2段
        }
    
    def parse(self, pdf_path: str = None) -> Dict:
        """
        完整解析PDF季报
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            Dict: 结构化解析结果
        """
        # 加载PDF
        if not self.load_pdf(pdf_path):
            return {'success': False, 'error': 'PDF加载失败'}
        
        # 提取策略章节
        strategy_section = self.find_strategy_section()
        
        if not strategy_section:
            return {
                'success': False,
                'error': '未找到投资策略和运作分析章节',
                'metadata': self.metadata,
                'full_text_sample': self.full_text[:1000] if self.full_text else None
            }
        
        # 分析章节内容
        analysis = self.analyze_strategy_content(strategy_section['content'])
        
        return {
            'success': True,
            'metadata': self.metadata,
            'strategy_section': strategy_section,
            'analysis': analysis,
            'parsed_at': datetime.now().isoformat()
        }
    
    def parse_from_bytes(self, pdf_bytes: bytes, fund_code: str = None, 
                         fund_name: str = None) -> Dict:
        """
        从二进制数据解析PDF（用于在线下载）
        
        Args:
            pdf_bytes: PDF二进制数据
            fund_code: 基金代码（可选）
            fund_name: 基金名称（可选）
            
        Returns:
            Dict: 结构化解析结果
        """
        if not self.extract_from_bytes(pdf_bytes):
            return {'success': False, 'error': 'PDF解析失败'}
        
        self.metadata['fund_code'] = fund_code
        self.metadata['fund_name'] = fund_name
        
        # 提取策略章节
        strategy_section = self.find_strategy_section()
        
        if not strategy_section:
            return {
                'success': False,
                'error': '未找到投资策略和运作分析章节',
                'metadata': self.metadata,
                'full_text_sample': self.full_text[:1000] if self.full_text else None
            }
        
        # 分析章节内容
        analysis = self.analyze_strategy_content(strategy_section['content'])
        
        return {
            'success': True,
            'metadata': self.metadata,
            'strategy_section': strategy_section,
            'analysis': analysis,
            'parsed_at': datetime.now().isoformat()
        }


class BatchReportParser:
    """
    批量报告解析器
    处理多个基金的季报解析
    """
    
    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir or '/root/.openclaw/workspace/fund_data/reports_parsed'
        os.makedirs(self.output_dir, exist_ok=True)
        self.results = []
    
    def parse_single_file(self, pdf_path: str, fund_code: str = None, 
                          fund_name: str = None) -> Dict:
        """
        解析单个PDF文件
        
        Args:
            pdf_path: PDF文件路径
            fund_code: 基金代码
            fund_name: 基金名称
            
        Returns:
            Dict: 解析结果
        """
        parser = ReportParser()
        result = parser.parse(pdf_path)
        
        # 添加基金信息
        if fund_code:
            result['fund_code'] = fund_code
        if fund_name:
            result['fund_name'] = fund_name
            
        return result
    
    def parse_directory(self, directory: str, pattern: str = "*.pdf") -> List[Dict]:
        """
        批量解析目录中的所有PDF
        
        Args:
            directory: 目录路径
            pattern: 文件匹配模式
            
        Returns:
            List[Dict]: 解析结果列表
        """
        import glob
        
        pdf_files = glob.glob(os.path.join(directory, pattern))
        print(f"找到 {len(pdf_files)} 个PDF文件待解析")
        
        self.results = []
        for pdf_path in sorted(pdf_files):
            print(f"\n解析: {os.path.basename(pdf_path)}")
            
            # 尝试从文件名提取基金信息
            filename = os.path.basename(pdf_path)
            fund_code = self._extract_fund_code_from_filename(filename)
            
            result = self.parse_single_file(pdf_path, fund_code)
            self.results.append(result)
            
            if result.get('success'):
                print(f"  ✅ 成功提取策略章节 ({len(result['strategy_section']['content'])} 字符)")
            else:
                print(f"  ❌ {result.get('error')}")
        
        return self.results
    
    def _extract_fund_code_from_filename(self, filename: str) -> Optional[str]:
        """从文件名提取基金代码"""
        # 常见格式: 基金代码_基金名称_报告类型.pdf
        match = re.search(r'(\d{6})', filename)
        if match:
            return match.group(1)
        return None
    
    def save_results(self, filename: str = None) -> str:
        """
        保存解析结果到JSON文件
        
        Args:
            filename: 输出文件名
            
        Returns:
            str: 输出文件路径
        """
        if not filename:
            filename = f"parsed_reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        output_path = os.path.join(self.output_dir, filename)
        
        # 只保存成功解析的结果的摘要
        summary = {
            'total_files': len(self.results),
            'successful': sum(1 for r in self.results if r.get('success')),
            'failed': sum(1 for r in self.results if not r.get('success')),
            'parsed_at': datetime.now().isoformat(),
            'results': []
        }
        
        for result in self.results:
            if result.get('success'):
                summary_result = {
                    'fund_code': result.get('fund_code'),
                    'fund_name': result.get('fund_name'),
                    'success': True,
                    'metadata': result.get('metadata'),
                    'strategy_summary': {
                        'title': result['strategy_section'].get('title'),
                        'char_count': result['strategy_section'].get('char_count'),
                        'pages': f"{result['strategy_section'].get('start_page')}-{result['strategy_section'].get('end_page')}"
                    },
                    'analysis_summary': {
                        'market_sentiment': result['analysis'].get('market_view', {}).get('sentiment_score'),
                        'sectors': result['analysis'].get('sector_preference', {}).get('mentioned_sectors'),
                        'has_outlook': result['analysis'].get('future_outlook', {}).get('has_outlook')
                    }
                }
            else:
                summary_result = {
                    'fund_code': result.get('fund_code'),
                    'fund_name': result.get('fund_name'),
                    'success': False,
                    'error': result.get('error')
                }
            
            summary['results'].append(summary_result)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"\n结果已保存: {output_path}")
        return output_path
    
    def get_consolidated_text(self) -> str:
        """
        获取所有成功解析的策略章节合并文本
        
        Returns:
            str: 合并的文本
        """
        consolidated = []
        
        for result in self.results:
            if result.get('success'):
                fund_name = result.get('fund_name', '未知基金')
                fund_code = result.get('fund_code', '')
                content = result['strategy_section'].get('content', '')
                
                consolidated.append(f"\n{'='*60}")
                consolidated.append(f"基金: {fund_name} ({fund_code})")
                consolidated.append(f"{'='*60}\n")
                consolidated.append(content)
                consolidated.append("\n")
        
        return '\n'.join(consolidated)


# ============ 整合到爬虫的便捷函数 ============

def parse_report_pdf(pdf_bytes: bytes, fund_code: str = None, 
                     fund_name: str = None) -> Dict:
    """
    便捷函数：从PDF字节数据解析季报
    
    这个函数可以直接整合到 cninfo_crawler.py 中使用
    
    Args:
        pdf_bytes: PDF二进制数据
        fund_code: 基金代码
        fund_name: 基金名称
        
    Returns:
        Dict: 解析结果
    """
    parser = ReportParser()
    return parser.parse_from_bytes(pdf_bytes, fund_code, fund_name)


def batch_parse_reports(pdf_directory: str, output_dir: str = None) -> Dict:
    """
    批量解析目录中的PDF季报
    
    Args:
        pdf_directory: PDF文件目录
        output_dir: 输出目录
        
    Returns:
        Dict: 批处理结果摘要
    """
    batch_parser = BatchReportParser(output_dir)
    results = batch_parser.parse_directory(pdf_directory)
    output_path = batch_parser.save_results()
    
    return {
        'success': True,
        'total': len(results),
        'successful': sum(1 for r in results if r.get('success')),
        'output_file': output_path,
        'results': results
    }


# ============ 测试 ============

def test_parser():
    """测试解析器"""
    print("="*70)
    print("基金季报PDF解析器测试")
    print("="*70)
    
    # 检查是否有测试PDF
    test_pdf = "/root/.openclaw/workspace/fund_data/analysis/基金策略增强版报告_20260313.pdf"
    
    if os.path.exists(test_pdf):
        print(f"\n测试文件: {test_pdf}")
        parser = ReportParser()
        result = parser.parse(test_pdf)
        
        print("\n解析结果:")
        print(f"  成功: {result.get('success')}")
        
        if result.get('success'):
            print(f"\n  元数据:")
            for key, value in result['metadata'].items():
                print(f"    {key}: {value}")
            
            print(f"\n  策略章节:")
            section = result['strategy_section']
            print(f"    标题: {section.get('title')}")
            print(f"    页码: {section.get('start_page')}-{section.get('end_page')}")
            print(f"    字符数: {section.get('char_count')}")
            print(f"\n  内容预览(前500字符):")
            print(f"    {section.get('content', '')[:500]}...")
            
            print(f"\n  智能分析:")
            analysis = result['analysis']
            print(f"    市场情绪得分: {analysis.get('market_view', {}).get('sentiment_score')}")
            print(f"    关键词: {analysis.get('market_view', {}).get('keywords')}")
            print(f"    涉及行业: {analysis.get('sector_preference', {}).get('mentioned_sectors')}")
            print(f"    调仓动作: {analysis.get('position_adjustment', {}).get('actions')}")
        else:
            print(f"  错误: {result.get('error')}")
    else:
        print(f"\n⚠️ 测试PDF不存在: {test_pdf}")
        print("请先下载基金季报PDF进行测试")


if __name__ == "__main__":
    test_parser()
