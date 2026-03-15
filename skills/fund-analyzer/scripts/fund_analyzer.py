#!/usr/bin/env python3
"""
Fund Analyzer - Core Analysis Module
Usage: python fund_analyzer.py <fund_code> --start YYYY-MM-DD --end YYYY-MM-DD
"""

import sys
import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# Import tushare with custom config
import tushare as ts
import tushare.pro.client as client

def load_config():
    """Load skill configuration"""
    config_path = Path(__file__).parent.parent / "config.yaml"
    # Default config
    config = {
        "tushare": {
            "server": "http://tushare.xyz",
            "token": "080afaf41dbb746406290078112f271e50e79a0858c9494bb52a1ec1"
        },
        "analysis": {
            "default_period": {
                "start": "2025-01-01",
                "end": "2025-12-31"
            },
            "top_holdings": 15,
            "min_trading_days": 100
        }
    }
    return config

def init_tushare(config):
    """Initialize Tushare API"""
    client.DataApi._DataApi__http_url = config["tushare"]["server"]
    return ts.pro_api(config["tushare"]["token"])

def get_quarter_end_dates(start_date, end_date):
    """Get all quarter-end dates between start and end"""
    # Convert to datetime
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    
    # Generate quarter-end dates
    quarter_ends = []
    current = start
    
    while current <= end:
        # Get quarter end
        year = current.year
        quarter = (current.month - 1) // 3 + 1
        
        if quarter == 1:
            q_end = pd.Timestamp(f"{year}-03-31")
        elif quarter == 2:
            q_end = pd.Timestamp(f"{year}-06-30")
        elif quarter == 3:
            q_end = pd.Timestamp(f"{year}-09-30")
        else:
            q_end = pd.Timestamp(f"{year}-12-31")
        
        if q_end >= start and q_end <= end and q_end not in quarter_ends:
            quarter_ends.append(q_end)
        
        # Move to next quarter
        current = q_end + pd.Timedelta(days=1)
    
    # Sort and convert to strings
    quarter_ends = sorted(quarter_ends)
    return [d.strftime("%Y%m%d") for d in quarter_ends]

def get_fund_basic(pro, fund_code):
    """Get fund basic information"""
    df = pro.fund_basic(ts_code=fund_code)
    if df.empty:
        return None
    return {
        "code": fund_code,
        "name": df.iloc[0]["name"],
        "type": df.iloc[0]["invest_type"],
        "management": df.iloc[0]["management"],
        "found_date": df.iloc[0]["found_date"]
    }

def get_fund_nav(pro, fund_code, start_date, end_date):
    """Get fund NAV data for a period"""
    start_str = pd.to_datetime(start_date).strftime("%Y%m%d")
    end_str = pd.to_datetime(end_date).strftime("%Y%m%d")
    
    df = pro.fund_nav(ts_code=fund_code, start_date=start_str, end_date=end_str)
    if df.empty or len(df) < 30:
        return None
    
    df = df.sort_values("nav_date")
    
    # Calculate metrics
    start_nav = df.iloc[0]["unit_nav"]
    end_nav = df.iloc[-1]["unit_nav"]
    
    df["daily_return"] = df["unit_nav"].pct_change()
    volatility = df["daily_return"].std() * (252**0.5) * 100
    
    period_return = (end_nav - start_nav) / start_nav * 100
    
    # Annualized return (assuming period can be any length)
    days = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days
    annual_return = period_return * (365 / days) if days > 0 else 0
    
    # Max drawdown
    cummax = df["unit_nav"].cummax()
    drawdown = (cummax - df["unit_nav"]) / cummax
    max_drawdown = drawdown.max() * 100
    
    # Sharpe ratio (assuming 2% risk-free rate)
    sharpe = (annual_return - 2) / volatility if volatility > 0 else 0
    
    return {
        "start_date": start_date,
        "end_date": end_date,
        "start_nav": start_nav,
        "end_nav": end_nav,
        "period_return": round(period_return, 2),
        "annual_return": round(annual_return, 2),
        "volatility": round(volatility, 2),
        "max_drawdown": round(max_drawdown, 2),
        "sharpe": round(sharpe, 2),
        "data_points": len(df),
        "trading_days": days
    }

def get_fund_holdings(pro, fund_code, start_date, end_date):
    """Get fund holdings for all quarter-ends within period"""
    # Get quarter-end dates
    quarter_dates = get_quarter_end_dates(start_date, end_date)
    
    holdings = {}
    
    for q_date in quarter_dates:
        q_name = pd.to_datetime(q_date).strftime("%YQ%q")
        try:
            df = pro.fund_portfolio(ts_code=fund_code, end_date=q_date)
            if not df.empty:
                holdings[q_name] = {
                    "date": q_date,
                    "holdings": df.head(15).to_dict("records")
                }
        except:
            holdings[q_name] = {"date": q_date, "holdings": []}
    
    return holdings

def analyze_fund(fund_code, start_date=None, end_date=None):
    """Main analysis function"""
    config = load_config()
    pro = init_tushare(config)
    
    # Use default dates if not provided
    if not start_date:
        start_date = config["analysis"]["default_period"]["start"]
    if not end_date:
        end_date = config["analysis"]["default_period"]["end"]
    
    print(f"Analyzing {fund_code}")
    print(f"Period: {start_date} to {end_date}")
    print()
    
    # Get data
    basic = get_fund_basic(pro, fund_code)
    nav = get_fund_nav(pro, fund_code, start_date, end_date)
    holdings = get_fund_holdings(pro, fund_code, start_date, end_date)
    
    if not basic or not nav:
        print(f"Error: Insufficient data for {fund_code}")
        return None
    
    # Build analysis result
    result = {
        "fund_code": fund_code,
        "fund_name": basic["name"],
        "fund_type": basic["type"],
        "management": basic["management"],
        "analysis_period": {
            "start": start_date,
            "end": end_date
        },
        "timestamp": datetime.now().isoformat(),
        "basic_info": basic,
        "performance": nav,
        "holdings": holdings,
        "quarter_ends_analyzed": list(holdings.keys())
    }
    
    print(f"✓ Analysis complete for {basic['name']}")
    print(f"  Period: {nav['trading_days']} days")
    print(f"  Period Return: {nav['period_return']}%")
    print(f"  Annual Return: {nav['annual_return']}%")
    print(f"  Volatility: {nav['volatility']}%")
    print(f"  Sharpe: {nav['sharpe']}")
    print(f"  Quarter-ends analyzed: {len(holdings)}")
    
    return result

def save_analysis(result, output_dir="./fund_analysis"):
    """Save analysis results"""
    if not result:
        return
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    fund_code = result["fund_code"]
    start = result["analysis_period"]["start"].replace("-", "")
    end = result["analysis_period"]["end"].replace("-", "")
    
    # Save JSON
    json_path = output_path / f"{fund_code}_{start}_{end}_analysis.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Saved to {json_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fund_analyzer.py <fund_code> [--start YYYY-MM-DD] [--end YYYY-MM-DD]")
        print("Example: python fund_analyzer.py 501220.SH --start 2023-06-01 --end 2025-12-31")
        print("         python fund_analyzer.py 501220.SH (uses default period from config)")
        sys.exit(1)
    
    fund_code = sys.argv[1]
    
    # Parse optional arguments
    start_date = None
    end_date = None
    
    if "--start" in sys.argv:
        start_idx = sys.argv.index("--start")
        start_date = sys.argv[start_idx + 1]
    
    if "--end" in sys.argv:
        end_idx = sys.argv.index("--end")
        end_date = sys.argv[end_idx + 1]
    
    result = analyze_fund(fund_code, start_date, end_date)
    save_analysis(result)
