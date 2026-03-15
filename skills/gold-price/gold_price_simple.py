#!/usr/bin/env python3
"""
简化版黄金价格获取 - 使用固定配置或用户提供的数据
"""

import json
import sys

def get_configured_gold_price():
    """
    从配置文件或环境变量获取金价
    用户可以手动更新这个值
    """
    # 默认配置 - 用户需要手动更新
    config = {
        "last_updated": "2026-03-08",
        "gold_price_usd": None,  # 用户填写: 例如 5120.50
        "gold_price_cny": None,  # 用户填写: 例如 368.50 (元/克)
        "data_source": "manual",  # manual, api, web
        "notes": "请手动更新实际金价，或使用下方命令获取"
    }
    
    # 尝试读取配置文件
    try:
        import os
        config_path = os.path.expanduser("~/.openclaw/gold_config.json")
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                config.update(user_config)
    except:
        pass
    
    return config

def fetch_from_investing_com():
    """从 investing.com 获取金价 (网页抓取)"""
    try:
        import urllib.request
        import re
        
        url = "https://www.investing.com/currencies/xau-usd"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8')
            
            # 提取价格
            # 寻找 data-test="instrument-price-last" 或其他价格标识
            patterns = [
                r'data-test="instrument-price-last"[^>]*>([\d,]+\.?\d*)',
                r'class="[^"]*text-5xl[^"]*"[^>]*>([\d,]+\.?\d*)',
                r'([\d,]+\.\d{2})</span>[^<]*USD',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, html)
                if match:
                    price_str = match.group(1).replace(',', '')
                    return {
                        "source": "investing.com",
                        "price": float(price_str),
                        "currency": "USD/oz",
                        "symbol": "XAU/USD"
                    }
                    
    except Exception as e:
        return {"error": f"investing.com failed: {e}"}
    
    return {"error": "Could not extract price from investing.com"}

def fetch_from_sina():
    """从新浪财经获取金价"""
    try:
        import urllib.request
        import json
        
        # 新浪财经黄金期货接口
        url = "https://stock.finance.sina.com.cn/futures/view/gold.php"
        
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('gbk', errors='ignore')
            
            # 尝试提取价格
            import re
            match = re.search(r'([\d]+\.\d{2})', html)
            if match:
                return {
                    "source": "sina finance",
                    "price": float(match.group(1)),
                    "note": "需要进一步解析HTML结构"
                }
                
    except Exception as e:
        return {"error": f"sina failed: {e}"}
    
    return {"error": "Sina fetch failed"}

def main():
    print("="*60)
    print("黄金价格获取工具")
    print("="*60)
    
    # 获取配置
    config = get_configured_gold_price()
    
    print("\n【当前配置】")
    print(f"  最后更新: {config.get('last_updated', 'N/A')}")
    print(f"  国际金价: {config.get('gold_price_usd', '未设置')} USD/oz")
    print(f"  国内金价: {config.get('gold_price_cny', '未设置')} CNY/gram")
    print(f"  数据来源: {config.get('data_source', 'manual')}")
    
    print("\n" + "-"*60)
    print("尝试从网络获取...")
    print("-"*60)
    
    # 尝试 investing.com
    result = fetch_from_investing_com()
    if "error" not in result:
        print(f"\n✅ investing.com:")
        print(f"   XAU/USD: {result['price']} {result['currency']}")
        
        # 保存到配置
        config['gold_price_usd'] = result['price']
        config['last_updated'] = result.get('timestamp', '2026-03-08')
        config['data_source'] = 'investing.com'
    else:
        print(f"\n❌ investing.com: {result['error']}")
    
    print("\n" + "="*60)
    print("【使用说明】")
    print("="*60)
    print("""
如果自动获取失败，你可以：

1. 手动设置金价：
   编辑文件: ~/.openclaw/gold_config.json
   内容示例:
   {
     "gold_price_usd": 5120.50,
     "gold_price_cny": 368.50,
     "last_updated": "2026-03-08",
     "data_source": "manual"
   }

2. 从网站查看实时金价：
   - investing.com/currencies/xau-usd
   - 金投网 (gold.org)
   - 新浪财经黄金频道

3. 在cron任务中硬编码当前金价（临时方案）
""")

if __name__ == "__main__":
    main()
