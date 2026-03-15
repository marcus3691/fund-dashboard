#!/usr/bin/env python3
"""提取PDF元数据"""
import sys
import json
import pdfplumber

def extract_metadata(pdf_path):
    """提取PDF元数据"""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            meta = {
                "pages": len(pdf.pages),
                "metadata": dict(pdf.metadata) if pdf.metadata else {}
            }
            return meta
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 extract_metadata.py <pdf文件路径>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    metadata = extract_metadata(pdf_path)
    print(json.dumps(metadata, ensure_ascii=False, indent=2))
