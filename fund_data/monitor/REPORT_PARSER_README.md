# 基金季报文本获取系统 - 使用指南

## 系统概述

本系统实现了完整的基金季报PDF下载、解析和智能分析功能，主要包含三个模块：

1. **cninfo_crawler.py** - 巨潮资讯网爬虫（已增强）
2. **report_parser.py** - PDF解析器（新增）
3. **integrated_report_monitor.py** - 季报文本监控器（新增）

## 核心功能

### 1. PDF文本提取
- 使用 `pdfplumber` 解析PDF
- 自动定位"投资策略和运作分析"章节
- 提取章节文本和页码范围

### 2. 智能文本分析
- **市场观点分析**: 识别看多/看空/中性情绪
- **行业偏好提取**: 识别关注的行业板块
- **调仓思路识别**: 提取增持/减持等操作
- **风险提示识别**: 识别风险提示内容
- **未来展望**: 提取投资展望

### 3. 批量处理
- 支持多个基金同时处理
- 生成结构化JSON报告
- 生成Markdown格式的可读报告

## 使用示例

### 单个基金解析

```python
from fund_data.monitor.cninfo_crawler import CNInfoCrawler

# 创建爬虫实例
crawler = CNInfoCrawler()

# 提取完整信息（搜索+下载+解析）
result = crawler.extract_investment_strategy(
    fund_code='005827',
    fund_name='易方达蓝筹精选混合',
    auto_parse=True,      # 自动解析PDF
    save_pdf=True         # 保存PDF文件
)

# 查看结果
if result['success']:
    report = result['latest_report']
    print(f"报告标题: {report['title']}")
    print(f"策略章节: {report['strategy_text'][:500]}...")
    print(f"市场情绪: {report['strategy_analysis']['market_view']['sentiment_score']}")
    print(f"关注行业: {report['strategy_analysis']['sector_preference']['mentioned_sectors']}")
```

### 批量解析

```python
from fund_data.monitor.cninfo_crawler import CNInfoCrawler

# 创建爬虫实例
crawler = CNInfoCrawler()

# 基金列表
fund_list = [
    {'fund_code': '005827', 'fund_name': '易方达蓝筹精选混合'},
    {'fund_code': '000083', 'fund_name': '汇添富消费行业混合'},
    {'fund_code': '110022', 'fund_name': '易方达消费行业股票'},
]

# 批量提取
result = crawler.batch_extract_strategies(
    fund_list=fund_list,
    save_results=True
)

print(f"成功: {result['successful']}/{result['total']}")
print(f"结果文件: {result['output_file']}")
```

### 使用季报文本监控器

```python
from fund_data.monitor.integrated_report_monitor import ReportTextMonitor

# 创建监控器
monitor = ReportTextMonitor()

# 监控单个基金
result = monitor.monitor_fund_quarterly(
    fund_code='005827',
    fund_name='易方达蓝筹精选混合',
    force_update=False  # 如果已处理过则跳过
)

# 批量监控
fund_list = [
    {'fund_code': '005827', 'fund_name': '易方达蓝筹精选混合'},
    {'fund_code': '000083', 'fund_name': '汇添富消费行业混合'},
]

result = monitor.batch_monitor_funds(fund_list)

# 生成文本报告
text_report = monitor.generate_text_report(result)
```

### 集成到主监控系统

```python
from fund_data.monitor.integrated_report_monitor import run_quarterly_text_monitor

# 运行完整的季报监控（自动使用核心基金列表）
result = run_quarterly_text_monitor(
    fund_list=None,        # 使用默认核心基金列表
    force_update=False,    # 不重复处理
    generate_report=True   # 生成文本报告
)
```

### 仅解析已有PDF文件

```python
from fund_data.monitor.report_parser import ReportParser

# 创建解析器
parser = ReportParser()

# 解析PDF文件
result = parser.parse('/path/to/report.pdf')

if result['success']:
    print(f"章节标题: {result['strategy_section']['title']}")
    print(f"章节内容: {result['strategy_section']['content']}")
    print(f"市场情绪: {result['analysis']['market_view']}")
    print(f"行业偏好: {result['analysis']['sector_preference']}")
```

## 输出格式

### 解析结果JSON结构

```json
{
  "success": true,
  "fund_code": "005827",
  "fund_name": "易方达蓝筹精选混合",
  "metadata": {
    "pages": 56,
    "filename": "005827_易方达蓝筹精选混合_2024年年度报告.pdf",
    "parsed_at": "2024-03-15T10:30:00"
  },
  "strategy_section": {
    "title": "投资策略和运作分析",
    "content": "报告期内，本基金...",
    "start_page": 12,
    "end_page": 15,
    "char_count": 3520
  },
  "analysis": {
    "market_view": {
      "sentiment_score": 2,
      "keywords": ["上涨", "看好", "机会"],
      "summary_paragraphs": ["..."]
    },
    "position_adjustment": {
      "actions": ["增持", "加仓"],
      "descriptions": ["..."]
    },
    "sector_preference": {
      "mentioned_sectors": ["消费", "科技", "医药"],
      "sector_keywords": {
        "消费": ["白酒", "食品饮料"],
        "科技": ["半导体", "人工智能"]
      }
    },
    "risk_awareness": {
      "has_risk_warning": true,
      "risk_mentions": ["..."]
    },
    "future_outlook": {
      "has_outlook": true,
      "outlook_content": ["..."]
    }
  }
}
```

## 文件存储位置

- **PDF文件**: `/root/.openclaw/workspace/fund_data/reports_pdf/`
- **解析结果**: `/root/.openclaw/workspace/fund_data/reports_parsed/`
- **监控日志**: `/root/.openclaw/workspace/fund_data/monitor/logs/`

## 测试运行

```bash
# 测试PDF解析器
cd /root/.openclaw/workspace/fund_data/monitor
python3 report_parser.py

# 测试爬虫（仅搜索和列表）
python3 cninfo_crawler.py

# 测试完整提取流程（搜索+下载+解析）
python3 cninfo_crawler.py --full

# 测试批量提取
python3 cninfo_crawler.py --batch

# 测试季报文本监控器
python3 integrated_report_monitor.py
```

## 技术细节

### 章节定位算法

系统使用多种正则表达式模式匹配"投资策略和运作分析"章节：

```python
STRATEGY_SECTION_PATTERNS = [
    r'投资策略.*?运作分析',
    r'投资策.*?运作分析',
    r'报告期内.*?投资策略',
    r'投资策略.*?(?=\n|$)',
    r'基金.*?投资策略',
    r'投资运作.*?分析',
]
```

### 市场情绪分析

基于关键词词典进行情感分析：

- **看多词**: 上涨、反弹、看好、乐观、机会、配置价值
- **看空词**: 下跌、调整、谨慎、悲观、风险、高估
- **中性词**: 震荡、结构性、分化、精选、稳健

### 行业识别

系统识别以下行业关键词：

- **科技**: TMT、电子、计算机、半导体、芯片、AI
- **消费**: 白酒、医药、食品饮料、家电、零售
- **周期**: 化工、有色、钢铁、煤炭、建材
- **金融**: 银行、保险、证券、地产
- **新能源**: 光伏、电动车、锂电、储能
- **制造**: 机械、汽车、军工、高端制造

## 注意事项

1. **PDF格式差异**: 不同基金公司季报格式可能有差异，解析器会尝试多种匹配模式
2. **网络请求**: 下载PDF需要联网，请确保网络连接正常
3. **去重机制**: 系统使用announcementId进行去重，避免重复处理
4. **存储空间**: PDF文件会占用存储空间，定期清理旧报告

## 扩展开发

### 添加新的分析维度

在 `report_parser.py` 的 `analyze_strategy_content` 方法中添加：

```python
def analyze_strategy_content(self, section_content: str) -> Dict:
    analysis = {
        # ... 现有分析 ...
        'your_new_analysis': self._extract_your_feature(section_content),
    }
    return analysis

def _extract_your_feature(self, text: str) -> Dict:
    # 实现你的分析逻辑
    return {'result': '...'}
```

### 自定义输出格式

修改 `BatchReportParser.save_results()` 方法自定义输出格式。
