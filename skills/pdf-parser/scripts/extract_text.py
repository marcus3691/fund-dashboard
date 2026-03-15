#!/usr/bin/env python3
"""提取PDF全部文本内容"""
import sys
import pdfplumber

def extract_text(pdf_path):
    """提取PDF全部文本"""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = []
            for i, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text:
                    full_text.append(f"=== 第 {i} 页 ===\n{text}\n")
            return "\n".join(full_text)
    except Exception as e:
        return f"错误: {e}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 extract_text.py <pdf文件路径>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    result = extract_text(pdf_path)
    print(result)
