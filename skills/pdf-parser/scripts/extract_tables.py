#!/usr/bin/env python3
"""提取PDF中的表格"""
import sys
import json
import pdfplumber

def extract_tables(pdf_path):
    """提取PDF中的所有表格"""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            all_tables = []
            for i, page in enumerate(pdf.pages, 1):
                tables = page.extract_tables()
                if tables:
                    for j, table in enumerate(tables, 1):
                        all_tables.append({
                            "page": i,
                            "table_index": j,
                            "data": table,
                            "row_count": len(table),
                            "col_count": len(table[0]) if table else 0
                        })
            return all_tables
    except Exception as e:
        return [{"error": str(e)}]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 extract_tables.py <pdf文件路径>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    tables = extract_tables(pdf_path)
    print(json.dumps(tables, ensure_ascii=False, indent=2))
