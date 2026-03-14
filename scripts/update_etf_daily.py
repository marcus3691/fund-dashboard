#!/usr/bin/env python3
"""
ETF日行情数据更新脚本
从Tushare获取ETF日线数据，生成JSON供前端使用
"""

import json
import os
import sys
from datetime import datetime, timedelta

# ETF标的池
ETF_UNIVERSE = {
    # 核心层 - 地缘防御
    "515220.SH": {"name": "煤炭ETF", "layer": "core", "category": "能源"},
    "512400.SH": {"name": "有色金属ETF", "layer": "core", "category": "有色"},
    "518880.SH": {"name": "黄金ETF", "layer": "core", "category": "贵金属"},
    "159972.SZ": {"name": "5年地债ETF", "layer": "core", "category": "债券"},
    
    # 卫星层 - 科技进攻
    "512480.SH": {"name": "半导体ETF", "layer": "satellite", "category": "科技-算力"},
    "515880.SH": {"name": "通信ETF", "layer": "satellite", "category": "科技-光模块"},
    "159819.SZ": {"name": "人工智能ETF", "layer": "satellite", "category": "科技-AI应用"},
    "516510.SH": {"name": "云计算ETF", "layer": "satellite", "category": "科技-云服务"},
    "512660.SH": {"name": "军工ETF", "layer": "satellite", "category": "军工"},
    "516020.SH": {"name": "化工ETF", "layer": "satellite", "category": "化工"},
    
    # 对冲层
    "510300.SH": {"name": "沪深300ETF", "layer": "hedge", "category": "宽基"},
    "511010.SH": {"name": "国债ETF", "layer": "hedge", "category": "债券"},
}

def fetch_etf_daily(code, name):
    """
    获取ETF日线数据
    实际使用时接入Tushare Pro API
    当前使用模拟数据演示结构
    """
    # TODO: 接入Tushare Pro
    # import tushare as ts
    # pro = ts.pro_api('your_token')
    # df = pro.fund_daily(ts_code=code, start_date='20240101', end_date='20260314')
    
    # 模拟返回数据结构
    return {
        "code": code,
        "name": name,
        "latest": {
            "date": "2026-03-14",
            "open": 2.15,
            "close": 2.18,
            "high": 2.20,
            "low": 2.14,
            "volume": 1250000,
            "amount": 2725000
        },
        "change_pct": 1.40,
        "metrics": {
            "ma5": 2.12,
            "ma10": 2.10,
            "ma20": 2.08,
            "ma60": 2.02,
            "high_52w": 2.45,
            "low_52w": 1.85,
            "volatility_20d": 15.5
        }
    }

def calculate_metrics(daily_data):
    """计算技术指标"""
    if not daily_data:
        return {}
    
    closes = [d["close"] for d in daily_data[-60:]]  # 最近60天
    if len(closes) < 20:
        return {}
    
    import statistics
    
    return {
        "ma5": sum(closes[-5:]) / 5,
        "ma10": sum(closes[-10:]) / 10,
        "ma20": sum(closes[-20:]) / 20,
        "ma60": sum(closes[-60:]) / 60 if len(closes) >= 60 else None,
        "volatility_20d": statistics.stdev(closes[-20:]) / statistics.mean(closes[-20:]) * 100
    }

def update_etf_data():
    """更新所有ETF数据"""
    etf_data = {
        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data_source": "Tushare Pro (待接入)",
        "etf_list": {}
    }
    
    for code, info in ETF_UNIVERSE.items():
        print(f"Updating {code} - {info['name']}...")
        
        # 获取日线数据
        daily = fetch_etf_daily(code, info['name'])
        
        etf_data["etf_list"][code] = {
            **info,
            "latest": daily["latest"],
            "change_pct": daily["change_pct"],
            "metrics": daily["metrics"]
        }
    
    # 保存到JSON文件
    output_path = os.path.join(os.path.dirname(__file__), "etf_daily_data.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(etf_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ ETF数据更新完成！")
    print(f"📁 保存路径: {output_path}")
    print(f"🕐 更新时间: {etf_data['update_time']}")
    print(f"📊 共更新 {len(ETF_UNIVERSE)} 只ETF")
    
    return etf_data

if __name__ == "__main__":
    update_etf_data()
