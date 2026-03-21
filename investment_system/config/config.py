# config.py - 系统配置文件
"""
KimiClaw 投研系统配置
"""


class Config:
    """系统配置类"""
    
    # Tushare Pro 配置
    TUSHARE_TOKEN = "ac67f4a573934b28bcd76489aa579d47fcca70bd09ad9f2154208a82"
    
    # 路径配置
    DATA_DIR = "/root/.openclaw/workspace/investment_system/data"
    REPORTS_DIR = "/root/.openclaw/workspace/investment_system/reports"
    LOGS_DIR = "/root/.openclaw/workspace/investment_system/logs"
    
    # 组合配置
    PORTFOLIO_CONFIG = {
        # ETF部分
        '518880.SH': {'name': '黄金ETF', 'weight': 0.15, 'type': 'etf', 'sector': '黄金'},
        '159562.SZ': {'name': '黄金股ETF', 'weight': 0.10, 'type': 'etf', 'sector': '黄金'},
        '512710.SH': {'name': '军工龙头ETF', 'weight': 0.08, 'type': 'etf', 'sector': '军工'},
        # 个股替代
        '300394.SZ': {'name': '天孚通信', 'weight': 0.04, 'type': 'stock', 'sector': '科技'},
        '688195.SH': {'name': '腾景科技', 'weight': 0.08, 'type': 'stock', 'sector': '科技'},
        '512480.SH': {'name': '半导体ETF', 'weight': 0.05, 'type': 'etf', 'sector': '科技'},
        '159819.SZ': {'name': '人工智能ETF', 'weight': 0.03, 'type': 'etf', 'sector': '科技'},
        '159326.SZ': {'name': '电网设备ETF', 'weight': 0.10, 'type': 'etf', 'sector': '电力'},
        '159611.SZ': {'name': '电力ETF', 'weight': 0.05, 'type': 'etf', 'sector': '电力'},
        '513130.SH': {'name': '恒生科技ETF', 'weight': 0.05, 'type': 'etf', 'sector': '港股'},
        '513120.SH': {'name': '港股创新药ETF', 'weight': 0.02, 'type': 'etf', 'sector': '港股'},
    }
    
    # 现金配置
    CASH_WEIGHT = 0.25
    CASH_ANNUAL_RETURN = 0.02
    
    # 基准配置
    BENCHMARK_CONFIG = {
        '000300.SH': {'name': '沪深300'},
        '000906.SH': {'name': '中证800'},
    }
    
    # 信号监控阈值
    SIGNAL_THRESHOLDS = {
        'max_drawdown_warning': -0.05,      # 回撤5%警告
        'max_drawdown_alert': -0.10,        # 回撤10%告警
        'daily_loss_limit': -0.03,          # 单日跌3%告警
        'consecutive_loss_days': 3,         # 连续亏损3天告警
        'sector_deviation_limit': 0.05,     # 行业偏离5%提醒
    }
    
    # 资产配置参数
    PORTFOLIO_OPTIMIZATION = {
        'risk_free_rate': 0.02,
        'trading_days': 252,
        'rebalance_frequency': 'quarterly',  # 季度再平衡
        'max_single_weight': 0.30,           # 单资产最大权重
        'min_single_weight': 0.01,           # 单资产最小权重
    }
    
    # 报告配置
    REPORT_CONFIG = {
        'default_formats': ['markdown'],
        'auto_save': True,
        'retention_days': 365,
    }
    
    # 日志配置
    LOG_CONFIG = {
        'level': 'INFO',
        'file': f"{LOGS_DIR}/system.log",
        'max_size': 10 * 1024 * 1024,  # 10MB
        'backup_count': 5,
    }
