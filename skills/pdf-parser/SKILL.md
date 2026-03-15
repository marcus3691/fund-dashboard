---
name: pdf-parser
description: Parse and extract text, tables, and metadata from PDF files. Use when users need to extract content from PDF documents, convert PDF to text, analyze PDF structure, or work with PDF data. Supports text extraction, table extraction, page-by-page analysis, and metadata retrieval.
triggers:
  - pattern: "PDF|pdf|解析PDF|提取PDF|PDF内容"
    description: "检测PDF相关查询"
  - pattern: "extract.*pdf|parse.*pdf|pdf.*text|pdf.*content"
    description: "检测PDF内容提取需求"
  - pattern: "PDF表格|PDF数据|PDF转文本"
    description: "检测PDF数据提取需求"
auto_invoke: true
---

# PDF Parser

使用 `pdfplumber` 库解析PDF文件，提取文本、表格和元数据。

## 快速开始

### 提取PDF全部文本

```bash
python3 skills/pdf-parser/scripts/extract_text.py /path/to/file.pdf
```

### 提取PDF表格

```bash
python3 skills/pdf-parser/scripts/extract_tables.py /path/to/file.pdf
```

### 提取PDF元数据

```bash
python3 skills/pdf-parser/scripts/extract_metadata.py /path/to/file.pdf
```

## 功能特性

- **文本提取**：提取全部文本或按页提取
- **表格提取**：自动识别PDF中的表格数据
- **元数据获取**：标题、作者、创建日期等信息
- **页面分析**：逐页内容分析

## Python API 使用

```python
import pdfplumber

# 打开PDF
with pdfplumber.open("file.pdf") as pdf:
    # 获取页数
    print(f"总页数: {len(pdf.pages)}")
    
    # 提取第一页文本
    first_page = pdf.pages[0]
    text = first_page.extract_text()
    
    # 提取表格
    tables = first_page.extract_tables()
```

## 脚本说明

| 脚本 | 功能 | 输出 |
|:---|:---|:---|
| `extract_text.py` | 提取全部文本 | 纯文本 |
| `extract_tables.py` | 提取所有表格 | JSON格式 |
| `extract_metadata.py` | 提取文档元数据 | JSON格式 |
| `extract_pages.py` | 按页提取内容 | 分页文本 |

## 依赖

- `pdfplumber` (已安装)
