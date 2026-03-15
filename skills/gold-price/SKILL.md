---
name: gold-price
description: 获取黄金实时价格数据。支持国际金价(XAU/USD)、黄金ETF(GLD)、黄金期货以及A股黄金板块数据。
triggers:
  - pattern: "黄金价格|gold price|XAU|金价"
    description: "检测黄金价格查询"
  - pattern: "国际金价|伦敦金|现货黄金"
    description: "检测国际金价查询"
auto_invoke: true
---

# Gold Price Data Retrieval

使用多种数据源获取黄金价格：
1. yfinance - 国际金价、黄金ETF、黄金期货
2. akshare - A股黄金板块、上海黄金交易所
3. tushare - A股黄金股数据

## 依赖安装

```bash
pip install yfinance akshare --break-system-packages
```

## 使用示例

### 获取国际金价 (XAU/USD)
```python
import yfinance as yf

gold = yf.Ticker("GC=F")  # COMEX黄金期货
data = gold.history(period="5d")
print(data)

# 或获取黄金ETF GLD
gld = yf.Ticker("GLD")
data = gld.history(period="5d")
```

### 获取A股黄金板块
```python
import akshare as ak

# 黄金概念板块
stock_board_concept_name_ths_df = ak.stock_board_concept_name_ths()
gold_board = stock_board_concept_name_ths_df[stock_board_concept_name_ths_df['概念名称'].str.contains('黄金')]

# 板块成分股
stock_board_concept_cons_ths_df = ak.stock_board_concept_cons_ths(symbol="黄金概念")
```

### 使用 Tushare 获取黄金股
```python
import tushare as ts
import tushare.pro.client as client

client.DataApi._DataApi__http_url = "http://tushare.xyz"
pro = ts.pro_api('YOUR_TOKEN')

# 山东黄金、中金黄金等
df = pro.daily(ts_code='600547.SH', start_date='20260301', end_date='20260307')
```

## 数据源对比

| 数据源 | 数据类型 | 优势 | 限制 |
|--------|---------|------|------|
| yfinance | 国际期货/ETF | 免费、实时 | 有时限流 |
| akshare | A股/国内期货 | 中文、免费 | 稳定性一般 |
| tushare | A股 | 数据完整 | 需要积分 |
