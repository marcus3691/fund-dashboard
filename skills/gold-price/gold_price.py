#!/usr/bin/env python3
"""
黄金价格获取工具
"""

import sys
import json
from datetime import datetime, timedelta

def get_gold_price_yfinance():
    """使用 yfinance 获取国际金价"""
    try:
        import yfinance as yf
        
        # 尝试多个黄金相关标的
        tickers = ["GC=F", "GLD", "XAUUSD=X"]
        
        for ticker in tickers:
            try:
                t = yf.Ticker(ticker)
                data = t.history(period="3d")
                
                if not data.empty and len(data) >= 1:
                    latest = data.iloc[-1]
                    prev = data.iloc[-2] if len(data) > 1 else latest
                    
                    return {
                        "source": f"yfinance ({ticker})",
                        "symbol": ticker,
                        "price": round(float(latest["Close"]), 2),
                        "change": round(float(latest["Close"] - prev["Close"]), 2),
                        "change_pct": round(float((latest["Close"] - prev["Close"]) / prev["Close"] * 100), 2),
                        "date": str(data.index[-1]),
                        "open": round(float(latest["Open"]), 2),
                        "high": round(float(latest["High"]), 2),
                        "low": round(float(latest["Low"]), 2),
                        "currency": "USD/oz" if ticker in ["GC=F", "GLD", "XAUUSD=X"] else "USD"
                    }
            except:
                continue
                
    except Exception as e:
        return {"error": f"yfinance failed: {e}"}
    
    return {"error": "yfinance rate limited"}

def get_sge_gold():
    """使用 akshare 获取上海黄金交易所数据"""
    try:
        import akshare as ak
        
        # 获取上海金交所现货价格
        try:
            df = ak.spot_golden_sh()
            if not df.empty:
                latest = df.iloc[0]
                return {
                    "source": "akshare (SGE)",
                    "contract": str(latest.get("品种", "Au99.99")),
                    "price": float(latest.get("最新价", 0)),
                    "change": float(latest.get("涨跌", 0)),
                    "currency": "CNY/gram"
                }
        except:
            pass
            
        # 备用： futures 接口
        try:
            df = ak.futures_zh_realtime(symbol="SH")
            gold_df = df[df["name"].str.contains("黄金", na=False)]
            if not gold_df.empty:
                row = gold_df.iloc[0]
                return {
                    "source": "akshare (SHFE Gold)",
                    "contract": str(row.get("name", "")),
                    "price": float(row.get("最新", 0)),
                    "currency": "CNY/gram"
                }
        except:
            pass
            
    except Exception as e:
        return {"error": f"akshare failed: {e}"}
    
    return {"error": "akshare no data"}

def get_a_share_gold():
    """使用 tushare 获取A股黄金股"""
    try:
        import tushare as ts
        import tushare.pro.client as client
        
        client.DataApi._DataApi__http_url = "http://tushare.xyz"
        pro = ts.pro_api('080afaf41dbb746406290078112f271e50e79a0858c9494bb52a1ec1')
        
        # 获取最近交易日
        today = datetime.now()
        trade_date = today.strftime('%Y%m%d')
        
        stocks = {
            "600547.SH": "山东黄金",
            "600489.SH": "中金黄金", 
            "600988.SH": "赤峰黄金"
        }
        
        results = {}
        for code, name in stocks.items():
            try:
                df = pro.daily(ts_code=code, trade_date=trade_date)
                if not df.empty:
                    row = df.iloc[0]
                    results[code] = {
                        "name": name,
                        "close": round(float(row["close"]), 2),
                        "open": round(float(row["open"]), 2),
                        "high": round(float(row["high"]), 2),
                        "low": round(float(row["low"]), 2),
                        "pct_chg": round(float(row["pct_chg"]), 2),
                        "volume": int(row["vol"]),
                        "amount": int(row["amount"])
                    }
            except Exception as e:
                results[code] = {"error": str(e)}
        
        return {
            "source": "tushare",
            "trade_date": trade_date,
            "data": results
        }
    except Exception as e:
        return {"error": f"tushare failed: {e}"}

def get_gold_price_direct():
    """直接访问免费API获取金价"""
    try:
        import urllib.request
        import json
        
        # 尝试访问 gold-api 免费接口
        try:
            url = "https://api.metals.live/v1/spot"
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                if 'gold' in data:
                    return {
                        "source": "metals.live API",
                        "price": float(data['gold']),
                        "currency": "USD/oz",
                        "timestamp": data.get('timestamp', '')
                    }
        except:
            pass
            
        # 备用 API
        try:
            url = "https://www.goldapi.io/api/XAU/USD"
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0',
                'x-access-token': 'goldapi-xxx'  # 免费版不需要token
            })
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                return {
                    "source": "goldapi.io",
                    "price": float(data.get('price', 0)),
                    "currency": "USD/oz",
                    "timestamp": data.get('timestamp', '')
                }
        except:
            pass
            
    except Exception as e:
        return {"error": f"Direct API failed: {e}"}
    
    return {"error": "All direct APIs failed"}

def main():
    """主函数"""
    print("正在获取黄金价格数据...\n")
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "sources": {}
    }
    
    # 1. 国际金价 (yfinance)
    results["sources"]["international"] = get_gold_price_yfinance()
    
    # 2. 国内金价 (akshare)
    results["sources"]["domestic"] = get_sge_gold()
    
    # 3. A股黄金股 (tushare)
    results["sources"]["a_shares"] = get_a_share_gold()
    
    # 4. 直接API
    results["sources"]["api"] = get_gold_price_direct()
    
    print(json.dumps(results, indent=2, ensure_ascii=False))
    
    # 输出简要总结
    print("\n" + "="*50)
    print("黄金价格摘要:")
    print("="*50)
    
    for name, data in results["sources"].items():
        if "error" not in data:
            price = data.get("price", "N/A")
            currency = data.get("currency", "")
            source = data.get("source", name)
            print(f"• {source}: {price} {currency}")

if __name__ == "__main__":
    main()
