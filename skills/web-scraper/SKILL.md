# Web Scraper Skill

基于Scrapling框架的网页抓取工具，为OpenClaw提供强大的网页数据获取能力。

## 功能

- **普通网页抓取**：快速获取静态页面内容
- **动态页面抓取**：支持JS渲染的网页
- **反反爬抓取**：绕过Cloudflare等反爬机制
- **自适应解析**：应对网站改版，自动重新匹配元素
- **结构化数据提取**：根据schema提取特定字段

## 安装

```bash
pip3 install scrapling --break-system-packages
```

## 使用方法

### Python调用

```python
from skills.web_scraper.web_scraper import scrape_web, extract_structured_data

# 基础抓取
result = scrape_web("https://example.com")
print(result["content"])

# 指定抓取模式
result = scrape_web("https://example.com", mode="stealth")

# 使用CSS选择器提取内容
result = scrape_web("https://example.com", selector=".article-content")
print(result["selected_content"])

# 提取结构化数据
schema = {
    "title": "h1::text",
    "author": ".author::text",
    "content": ".content::text"
}
data = extract_structured_data("https://example.com", schema)
```

### CLI调用

```bash
# 基础抓取
python3 skills/web-scraper/web_scraper.py https://example.com

# 指定模式
python3 skills/web-scraper/web_scraper.py https://example.com stealth

# 使用选择器
python3 skills/web-scraper/web_scraper.py https://example.com auto ".article-title"
```

## 抓取模式

| 模式 | 说明 | 适用场景 |
|:---:|:---|:---|
| `static` | 静态抓取 | 普通HTML页面 |
| `dynamic` | 动态抓取 | JS渲染页面 |
| `stealth` | 反反爬抓取 | Cloudflare防护网站 |
| `auto` | 自动选择 | 默认，失败自动切换 |

## 应用场景

### 1. 基金数据监控

```python
# 抓取基金公司公告
result = scrape_web(
    "https://fund.eastmoney.com/company/80000200.html",
    selector=". announcement-list"
)
```

### 2. 实时行情获取

```python
# 抓取实时行情（突破API限制）
result = scrape_web(
    "https://quote.eastmoney.com/sh515220.html",
    selector="#price9"
)
```

### 3. 新闻舆情监控

```python
# 抓取财经新闻
schema = {
    "title": "h1::text",
    "content": ".article-content p::text",
    "time": ".time::text"
}
data = extract_structured_data("https://finance.sina.com.cn/...", schema)
```

### 4. 研报自动收集

```python
# 批量抓取券商研报
urls = [
    "https://report.example.com/1.html",
    "https://report.example.com/2.html"
]
results = scrape_multiple(urls, mode="stealth")
```

## 输出格式

```json
{
  "success": true,
  "url": "https://example.com",
  "title": "页面标题",
  "content": "页面正文内容...",
  "selected_content": "选择器提取的内容",
  "fetcher_used": "stealth"
}
```

## 注意事项

1. **遵守robots.txt**：抓取前检查网站robots.txt
2. **控制频率**：避免对同一网站频繁请求
3. **合法使用**：仅用于公开数据抓取，不获取敏感信息
4. **异常处理**：网络不稳定时可能失败，需要重试机制

## 依赖

- Python 3.8+
- scrapling
- 可选: playwright (用于dynamic/stealth模式)

## 版本

v1.0.0 - 初始版本，集成Scrapling核心功能
