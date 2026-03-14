#!/usr/bin/env python3
"""
Web Scraper Skill for OpenClaw
基于Scrapling框架的网页抓取工具

功能:
1. 抓取普通网页内容
2. 抓取动态JS渲染页面
3. 绕过反爬机制(Cloudflare等)
4. 自适应解析(应对网站改版)
"""

import json
import sys
from typing import Dict, List, Optional

def scrape_web(url: str, mode: str = "auto", selector: Optional[str] = None) -> Dict:
    """
    抓取网页内容
    
    Args:
        url: 目标网址
        mode: 抓取模式 - "auto"(自动选择) / "static"(静态) / "dynamic"(动态) / "stealth"(反反爬)
        selector: CSS选择器，用于提取特定内容(可选)
    
    Returns:
        {
            "success": bool,
            "url": str,
            "title": str,
            "content": str,
            "selected_content": str(如果提供了selector),
            "error": str(如果失败)
        }
    """
    try:
        from scrapling.fetchers import Fetcher, DynamicFetcher, StealthyFetcher
        
        # 根据模式选择Fetcher
        if mode == "static":
            fetcher = Fetcher
        elif mode == "dynamic":
            fetcher = DynamicFetcher
        elif mode == "stealth":
            fetcher = StealthyFetcher
        else:  # auto
            # 先尝试静态抓取，失败则使用stealth
            try:
                page = Fetcher.fetch(url)
                fetcher_used = "static"
            except Exception:
                page = StealthyFetcher.fetch(url, headless=True)
                fetcher_used = "stealth"
        
        # 如果是auto模式且上面已经抓取过了，跳过这里
        if mode != "auto":
            if mode in ["dynamic", "stealth"]:
                page = fetcher.fetch(url, headless=True)
            else:
                page = fetcher.fetch(url)
            fetcher_used = mode
        
        # 提取基本信息
        result = {
            "success": True,
            "url": url,
            "title": page.css("title::text").get("").strip(),
            "content": page.text[:5000] if hasattr(page, 'text') else "",
            "fetcher_used": fetcher_used if 'fetcher_used' in locals() else mode
        }
        
        # 如果提供了选择器，提取特定内容
        if selector:
            selected = page.css(selector)
            if selected:
                result["selected_content"] = selected.get("").strip()
                result["selected_html"] = selected.get("", attr="outerHTML")
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "url": url,
            "error": str(e)
        }

def scrape_multiple(urls: List[str], mode: str = "auto") -> List[Dict]:
    """
    批量抓取多个网页
    
    Args:
        urls: 网址列表
        mode: 抓取模式
    
    Returns:
        结果列表
    """
    results = []
    for url in urls:
        result = scrape_web(url, mode)
        results.append(result)
    return results

def monitor_webpage(url: str, selector: str, interval: int = 3600) -> Dict:
    """
    监控网页变化(基础版本)
    
    Args:
        url: 目标网址
        selector: 监控的CSS选择器
        interval: 检查间隔(秒)，默认1小时
    
    Returns:
        变化检测结果
    """
    import hashlib
    import time
    
    result = scrape_web(url, selector=selector)
    
    if not result.get("success"):
        return result
    
    content = result.get("selected_content", "")
    content_hash = hashlib.md5(content.encode()).hexdigest()
    
    return {
        "success": True,
        "url": url,
        "selector": selector,
        "content": content,
        "content_hash": content_hash,
        "timestamp": time.time()
    }

def extract_structured_data(url: str, schema: Dict) -> Dict:
    """
    根据schema提取结构化数据
    
    Args:
        url: 目标网址
        schema: 提取规则，如 {"title": "h1::text", "price": ".price::text"}
    
    Returns:
        结构化数据
    """
    result = scrape_web(url)
    
    if not result.get("success"):
        return result
    
    try:
        from scrapling.fetchers import Fetcher
        page = Fetcher.fetch(url)
        
        data = {"url": url, "success": True}
        for field, selector in schema.items():
            try:
                data[field] = page.css(selector).get("").strip()
            except Exception as e:
                data[field] = f"提取失败: {str(e)}"
        
        return data
        
    except Exception as e:
        return {
            "success": False,
            "url": url,
            "error": str(e)
        }

# CLI入口
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": "用法: python3 web_scraper.py <url> [mode] [selector]"
        }, ensure_ascii=False))
        sys.exit(1)
    
    url = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "auto"
    selector = sys.argv[3] if len(sys.argv) > 3 else None
    
    result = scrape_web(url, mode, selector)
    print(json.dumps(result, ensure_ascii=False, indent=2))
