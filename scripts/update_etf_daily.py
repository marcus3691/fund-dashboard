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

import requests

def fetch_etf_daily(code, name):
    """
    从Tushare Pro获取ETF日线数据
    """
    token = 'b5733b112e3fb832a729f1faa92155a3e2527e0c27cc148b6615fc58'
    url = 'http://api.tushare.pro'
    
    # 获取最近10个交易日的数据用于计算均线
    from datetime import datetime, timedelta
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=60)).strftime('%Y%m%d')
    
    payload = {
        'api_name': 'fund_daily',
        'token': token,
        'params': {
            'ts_code': code,
            'start_date': start_date,
            'end_date': end_date
        },
        'fields': 'trade_date,open,high,low,close,vol,amount'
    }
    
    try:
        r = requests.post(url, json=payload, timeout=30)
        result = r.json()
        
        if result.get('code') != 0 or not result.get('data'):
            print(f"  ⚠️ Tushare返回空数据或错误: {result.get('msg', 'unknown')}")
            return None
        
        fields = result['data']['fields']
        items = result['data']['items']
        
        if not items:
            print(f"  ⚠️ 无交易数据")
            return None
        
        # 转换数据格式
        daily_data = []
        for item in items:
            row = dict(zip(fields, item))
            daily_data.append({
                "date": row['trade_date'],
                "open": float(row['open']),
                "close": float(row['close']),
                "high": float(row['high']),
                "low": float(row['low']),
                "volume": int(row['vol']),
                "amount": float(row['amount'])
            })
        
        # 按日期排序（旧到新）
        daily_data.sort(key=lambda x: x['date'])
        
        latest = daily_data[-1]
        prev = daily_data[-2] if len(daily_data) >= 2 else daily_data[-1]
        change_pct = round((latest['close'] - prev['close']) / prev['close'] * 100, 2) if prev['close'] != 0 else 0
        
        metrics = calculate_metrics(daily_data)
        
        return {
            "code": code,
            "name": name,
            "latest": {
                "date": latest['date'][:4] + '-' + latest['date'][4:6] + '-' + latest['date'][6:],
                "open": latest['open'],
                "close": latest['close'],
                "high": latest['high'],
                "low": latest['low'],
                "volume": latest['volume'],
                "amount": round(latest['amount'], 2)
            },
            "change_pct": change_pct,
            "metrics": metrics
        }
        
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")
        return None

def calculate_metrics(daily_data):
    """计算技术指标"""
    if not daily_data or len(daily_data) < 20:
        return {}
    
    import statistics
    
    closes = [d["close"] for d in daily_data]
    
    metrics = {
        "ma5": round(sum(closes[-5:]) / 5, 4),
        "ma10": round(sum(closes[-10:]) / 10, 4),
        "ma20": round(sum(closes[-20:]) / 20, 4),
        "volatility_20d": round(statistics.stdev(closes[-20:]) / statistics.mean(closes[-20:]) * 100, 2)
    }
    
    if len(closes) >= 60:
        metrics["ma60"] = round(sum(closes[-60:]) / 60, 4)
    
    # 52周高低点（最近252个交易日≈1年）
    if len(closes) >= 60:
        metrics["high_52w"] = round(max(closes[-min(252, len(closes)):]), 4)
        metrics["low_52w"] = round(min(closes[-min(252, len(closes)):]), 4)
    
    return metrics

def update_etf_data():
    """更新所有ETF数据"""
    etf_data = {
        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data_source": "Tushare Pro",
        "etf_list": {}
    }
    
    success_count = 0
    failed_count = 0
    
    for code, info in ETF_UNIVERSE.items():
        print(f"Updating {code} - {info['name']}...")
        
        # 获取日线数据
        daily = fetch_etf_daily(code, info['name'])
        
        if daily is None:
            print(f"  ⚠️ 跳过 {code} - 无数据")
            failed_count += 1
            continue
        
        etf_data["etf_list"][code] = {
            **info,
            "latest": daily["latest"],
            "change_pct": daily["change_pct"],
            "metrics": daily["metrics"]
        }
        success_count += 1
    
    # 保存到JSON文件
    output_path = os.path.join(os.path.dirname(__file__), "etf_daily_data.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(etf_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ ETF数据更新完成！")
    print(f"📁 保存路径: {output_path}")
    print(f"🕐 更新时间: {etf_data['update_time']}")
    print(f"📊 成功: {success_count} / {len(ETF_UNIVERSE)} 只ETF")
    if failed_count > 0:
        print(f"⚠️ 失败: {failed_count} 只ETF")
    
    return etf_data

if __name__ == "__main__":
    update_etf_data()
