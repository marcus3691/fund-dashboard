# 基金经理共识信号报告自动化系统

## 功能概述

本系统实现基金经理共识信号的自动化报告生成和邮件发送，包括：

- **股票共识TOP10**: 被最多基金经理重仓的股票
- **行业共识热力图**: 各行业基金经理关注度可视化
- **市场情绪指标**: 基于基金经理平均收益的市场情绪
- **变化分析**: 新增/退出共识的股票对比
- **操作建议**: 基于数据的智能投资建议

## 文件说明

### 核心脚本

| 文件 | 功能 | 用法 |
|------|------|------|
| `consensus_report_generator.py` | 报告生成器 | `python3 consensus_report_generator.py [daily\|weekly]` |
| `consensus_email_sender.py` | 邮件发送器 | `python3 consensus_email_sender.py [daily\|weekly\|test]` |
| `consensus_auto_runner.py` | 自动化执行器 | `python3 consensus_auto_runner.py [daily\|weekly]` |

### 辅助脚本

| 文件 | 功能 |
|------|------|
| `setup_cron.sh` | 定时任务配置脚本 |
| `run_daily_report.sh` | 日报执行脚本(由cron调用) |
| `run_weekly_report.sh` | 周报执行脚本(由cron调用) |

## 快速开始

### 1. 手动生成报告

```bash
# 生成日报
cd /root/.openclaw/workspace/fund_data/monitor
python3 consensus_report_generator.py daily

# 生成周报
python3 consensus_report_generator.py weekly
```

### 2. 发送邮件

```bash
# 发送日报邮件
python3 consensus_email_sender.py daily

# 发送周报邮件
python3 consensus_email_sender.py weekly

# 发送测试邮件
python3 consensus_email_sender.py test --to your@email.com
```

### 3. 一键执行(生成+发送)

```bash
# 执行完整日报流程
python3 consensus_auto_runner.py daily

# 执行完整周报流程
python3 consensus_auto_runner.py weekly

# 仅生成报告，不发送邮件
python3 consensus_auto_runner.py daily --skip-email

# 使用现有数据，跳过信号生成
python3 consensus_auto_runner.py daily --skip-signal
```

## 定时任务配置

### 方法1: 使用配置脚本

```bash
cd /root/.openclaw/workspace/fund_data/monitor
./setup_cron.sh
```

按提示完成安装。

### 方法2: 手动配置

```bash
crontab -e
```

添加以下内容：

```cron
# 基金经理共识信号报告定时任务
# 日报: 每天20:00
0 20 * * * /root/.openclaw/workspace/fund_data/monitor/run_daily_report.sh >> /root/.openclaw/workspace/fund_data/monitor/logs/cron.log 2>&1

# 周报: 每周一09:00
0 9 * * 1 /root/.openclaw/workspace/fund_data/monitor/run_weekly_report.sh >> /root/.openclaw/workspace/fund_data/monitor/logs/cron.log 2>&1
```

### 当前定时任务

```
日报: 每天 20:00
周报: 每周一 09:00
```

## 输出目录

```
/root/.openclaw/workspace/fund_data/monitor/
├── reports/              # HTML报告文件
│   ├── consensus_report_daily_YYYYMMDD.html
│   └── consensus_report_weekly_YYYYMMDD.html
├── history/              # 历史数据存档
│   └── signals_YYYYMMDD.json
└── logs/                 # 执行日志
    ├── daily_YYYYMMDD.log
    ├── weekly_YYYYMMDD.log
    └── cron.log
```

## 邮件配置

默认使用139邮箱发送：

- **SMTP服务器**: smtp.139.com
- **端口**: 465 (SSL)
- **发件人**: 18817205079@139.com

## 报告内容说明

### 1. 统计概览
- 覆盖基金经理数量
- 高共识股票数量
- 热门行业数量
- 情绪指数

### 2. 市场情绪指标
- 情绪评分(0-100)
- 平均收益率
- 情绪状态(积极/中性/谨慎)

### 3. 股票共识TOP10
- 排名(金银铜牌标识)
- 股票代码
- 共识人数
- 平均持仓比例
- 代表性基金经理
- 信号强度(高/中)

### 4. 行业共识热力图
- 热力颜色标识关注度
- 红色: 高热度(80%+)
- 橙色: 中高热度(60-80%)
- 黄色: 中等热度(40-60%)
- 绿色: 低热度(20-40%)
- 蓝色: 极低热度(<20%)

### 5. 与上期对比
- 新增共识股票
- 退出共识股票
- 排名变化

### 6. 操作建议
基于数据分析的智能投资建议

## 故障排查

### 检查日志
```bash
# 查看最新日志
tail -f /root/.openclaw/workspace/fund_data/monitor/logs/cron.log

# 查看日报日志
tail -f /root/.openclaw/workspace/fund_data/monitor/logs/daily_*.log

# 查看周报日志
tail -f /root/.openclaw/workspace/fund_data/monitor/logs/weekly_*.log
```

### 检查定时任务
```bash
crontab -l
```

### 手动测试
```bash
# 测试报告生成
python3 consensus_report_generator.py daily

# 测试邮件发送
python3 consensus_email_sender.py test
```

## 数据依赖

本系统依赖以下数据文件：

1. `manager_consensus_signals.json` - 共识信号数据
2. `manager_views.json` - 基金经理观点数据

确保运行前已通过 `consensus_signal_generator.py` 生成最新信号数据。
