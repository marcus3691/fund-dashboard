#!/usr/bin/env python3
"""
研报/会议纪要 AI 解析流水线
支持 PDF、图片格式自动提取核心观点并结构化输出
"""

import os
import sys
import json
import re
from pathlib import Path
import pdfplumber
from PIL import Image

class ResearchReportParser:
    """研报解析器"""
    
    def __init__(self, output_dir="/root/.openclaw/workspace/parsed_reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def parse_pdf(self, pdf_path):
        """解析PDF文件"""
        result = {
            "source_file": pdf_path,
            "total_pages": 0,
            "has_text_layer": False,
            "extracted_text": "",
            "images": []
        }
        
        with pdfplumber.open(pdf_path) as pdf:
            result["total_pages"] = len(pdf.pages)
            
            # 尝试提取文本
            full_text = []
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text and text.strip():
                    full_text.append(f"\n--- 第{i+1}页 ---\n{text}")
                    result["has_text_layer"] = True
                
                # 检查是否有图片
                if page.images:
                    # 转换为图片保存
                    im = page.to_image(resolution=150)
                    img_path = os.path.join(self.output_dir, f"{Path(pdf_path).stem}_page_{i+1}.png")
                    im.save(img_path)
                    result["images"].append(img_path)
            
            result["extracted_text"] = "\n".join(full_text)
        
        return result
    
    def extract_key_insights(self, text):
        """从文本中提取核心观点（简化版，实际可接入AI）"""
        insights = {
            "宏观观点": [],
            "行业推荐": [],
            "风险提示": [],
            "配置建议": []
        }
        
        # 简单的关键词匹配（实际应用中会调用AI进行深度分析）
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 匹配行业关键词
            industries = ['煤炭', '石油', '有色', '稀土', '光伏', '半导体', '银行', '白酒', 
                         '新能源', '军工', '医药', '消费', '科技', 'AI', '机器人']
            for ind in industries:
                if ind in line and ('看好' in line or '推荐' in line or '关注' in line):
                    insights["行业推荐"].append(line)
                    break
            
            # 匹配风险提示
            risk_keywords = ['风险', '谨慎', '注意', '警惕', '压力', '调整']
            if any(kw in line for kw in risk_keywords) and len(line) < 100:
                insights["风险提示"].append(line)
        
        return insights
    
    def save_structured_output(self, pdf_path, parse_result, insights):
        """保存结构化输出"""
        output = {
            "metadata": {
                "source_file": os.path.basename(pdf_path),
                "parsed_at": pd.Timestamp.now().isoformat(),
                "total_pages": parse_result["total_pages"],
                "has_text_layer": parse_result["has_text_layer"]
            },
            "raw_text": parse_result["extracted_text"][:5000] if parse_result["extracted_text"] else "(图片PDF，需OCR)",
            "key_insights": insights,
            "extracted_images": parse_result["images"]
        }
        
        output_file = os.path.join(
            self.output_dir, 
            f"{Path(pdf_path).stem}_parsed.json"
        )
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        return output_file


def main():
    """主函数 - 命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='研报PDF解析工具')
    parser.add_argument('pdf_path', help='PDF文件路径')
    parser.add_argument('-o', '--output', default='/root/.openclaw/workspace/parsed_reports',
                       help='输出目录')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.pdf_path):
        print(f"错误: 文件不存在 {args.pdf_path}")
        sys.exit(1)
    
    print(f"开始解析: {args.pdf_path}")
    
    rp = ResearchReportParser(output_dir=args.output)
    result = rp.parse_pdf(args.pdf_path)
    
    print(f"\n解析结果:")
    print(f"  总页数: {result['total_pages']}")
    print(f"  是否有文本层: {result['has_text_layer']}")
    print(f"  提取图片数: {len(result['images'])}")
    
    # 提取核心观点
    insights = rp.extract_key_insights(result["extracted_text"])
    
    # 保存结构化输出
    output_file = rp.save_structured_output(args.pdf_path, result, insights)
    print(f"\n结构化输出已保存: {output_file}")
    
    # 打印核心观点预览
    print("\n核心观点预览:")
    for category, items in insights.items():
        if items:
            print(f"\n【{category}】")
            for item in items[:3]:  # 只显示前3条
                print(f"  - {item[:80]}...")


if __name__ == "__main__":
    import pandas as pd
    main()
