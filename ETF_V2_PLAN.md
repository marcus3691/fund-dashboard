# ETF策略库 V2.0 开发规划

## 一、日行情接入方案

### 数据源
- **Tushare Pro**: ETF日线数据（开盘价、收盘价、最高价、最低价、成交量）
- **更新频率**: 每日收盘后自动更新（Cron定时任务）
- **存储方式**: JSON文件（轻量化，无需数据库）

### 数据字段
```json
{
  "515220.SH": {
    "name": "煤炭ETF",
    "daily_data": {
      "2026-03-13": {"open": 2.15, "close": 2.18, "high": 2.20, "low": 2.14, "volume": 1250000},
      "2026-03-12": {"open": 2.12, "close": 2.15, "high": 2.16, "low": 2.11, "volume": 1180000}
    },
    "metrics": {
      "latest_price": 2.18,
      "change_pct": 1.40,
      "ma20": 2.10,
      "ma60": 2.05
    }
  }
}
```

### 前端展示
- ETF卡片显示最新净值、涨跌幅
- 7日/30日/90日涨跌幅对比
- 溢价率监控（场内价格 vs 净值）

---

## 二、调仓信号推送系统

### 信号来源
1. **宏观事件**: 霍尔木兹海峡通航状态、美伊谈判进展、OPEC会议
2. **技术指标**: 油价突破关键点位、VIX波动率、风格切换信号
3. **日历事件**: EIA库存报告、美联储议息会议

### 信号类型
```json
{
  "signal_id": "SIG_20260314_001",
  "timestamp": "2026-03-14T10:30:00",
  "type": "geopolitical",
  "trigger": "霍尔木兹海峡封锁加深",
  "threshold": "航运费用上涨>20%",
  "action": {
    "layer": "core",
    "etf": "515220.SH",
    "direction": "加仓",
    "weight_change": 5
  },
  "urgency": "high",
  "source": "新闻监控"
}
```

### 推送方式
- **网页弹窗**: 用户访问时显示最新信号
- **浏览器通知**: 重要信号推送（可选）
- **邮件简报**: 每日收盘后发送信号汇总

---

## 三、组合回测框架

### 回测参数
- **起始时间**: 2020-01-01 至 当前
- **初始资金**: 100万
- **调仓频率**: 信号触发时调仓
- **交易成本**: 买入0.03%，卖出0.03%，最低5元

### 回测逻辑
```python
# 伪代码
for date in trading_days:
    # 1. 检查是否有调仓信号
    signals = get_signals(date)
    
    # 2. 执行调仓
    for signal in signals:
        execute_trade(signal)
    
    # 3. 记录组合净值
    portfolio_value = calculate_portfolio_value(date)
    
    # 4. 计算指标
    daily_return = (portfolio_value - prev_value) / prev_value

# 计算回测指标
total_return = (final_value - initial_value) / initial_value
annualized_return = (1 + total_return) ** (365 / days) - 1
max_drawdown = max((peak - trough) / peak)
sharpe_ratio = (annualized_return - risk_free_rate) / volatility
```

### 回测报告
- 累计收益率曲线 vs 基准（沪深300）
- 年度收益率对比
- 最大回撤、夏普比率、胜率
- 调仓记录明细

---

## 四、个性化配置

### 用户配置项
```json
{
  "user_config": {
    "risk_profile": "balanced",
    "initial_capital": 1000000,
    "custom_etfs": [
      {"code": "515220.SH", "name": "煤炭ETF", "weight": 20}
    ],
    "excluded_etfs": ["512200.SH"],
    "rebalance_threshold": 5,
    "notification": {
      "email": "user@example.com",
      "browser": true,
      "high_priority_only": false
    }
  }
}
```

### 配置功能
1. **风险偏好切换**: 进取/平衡/保守
2. **自定义ETF**: 添加/删除ETF，调整权重
3. **调仓阈值**: 设置触发调仓的权重偏离阈值
4. **通知设置**: 邮件/浏览器通知开关

### 数据存储
- **方式**: localStorage（浏览器本地存储）
- **优点**: 无需后端，用户数据隐私
- **缺点**: 换设备需重新配置（可导出/导入JSON）

---

## 五、实施时间表

| 阶段 | 任务 | 工时 | 交付物 |
|:---|:---|:---:|:---|
| **Phase 1** | 日行情接入 | 4h | etf_daily_data.json + 行情展示 |
| **Phase 2** | 调仓信号系统 | 6h | 信号数据 + 推送机制 + 历史信号库 |
| **Phase 3** | 组合回测 | 8h | 回测引擎 + 报告页面 |
| **Phase 4** | 个性化配置 | 4h | 配置面板 + localStorage存储 |
| **Phase 5** | 整合测试 | 2h | 完整功能测试 + Bug修复 |
| **总计** | | 24h | ETF策略库 V2.0 |

---

## 六、技术架构

```
etf_strategy.html
├── 行情数据 (etf_daily_data.json)
├── 信号系统 (etf_signals.json)
├── 回测引擎 (JavaScript)
├── 配置管理 (localStorage)
└── 可视化 (图表库: Chart.js)
```

---

## 七、风险评估

| 风险 | 影响 | 缓解措施 |
|:---|:---|:---|
| Tushare数据延迟 | 行情不是实时 | 明确标注"日行情"，非实时 |
| 信号准确性 | 误报/漏报 | 人工复核 + 多源验证 |
| 回测过拟合 | 历史不代表未来 | 添加免责声明 |
| 本地数据丢失 | 用户配置消失 | 提供导出/导入功能 |

---

## 八、下一步行动

需要用户确认：
1. **优先级排序**: 日行情、调仓信号、回测、配置，哪个先做？
2. **信号源**: 是否需要接入新闻API（如中金在线、华尔街见闻）？
3. **回测基准**: 以沪深300为基准，还是自建组合基准？
4. **邮件服务**: 是否需要邮件通知功能（需要SMTP配置）？
