#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DataMiner Agent - 数据抓取模块
功能：获取ETF/个股行情数据、财报数据、基金持仓数据
直接使用Tushare HTTP API
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import pandas as pd
import numpy as np
import requests

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('DataMiner')


class DataMinerAgent:
    """数据抓取Agent"""
    
    def __init__(self, config):
        self.config = config
        self.token = config.TUSHARE_TOKEN
        self.api_url = "http://api.tushare.pro"
        self.data_cache = {}
        logger.info("✓ DataMiner初始化完成")
    
    def _call_api(self, api_name: str, params: Dict = None, fields: str = None) -> Optional[pd.DataFrame]:
        """调用Tushare API"""
        try:
            payload = {
                'api_name': api_name,
                'token': self.token,
                'params': params or {},
                'fields': fields
            }
            
            response = requests.post(
                self.api_url,
                headers={'Content-Type': 'application/json'},
                data=json.dumps(payload),
                timeout=30
            )
            
            result = response.json()
            
            if result.get('code') != 0:
                logger.warning(f"API错误: {result.get('msg')}")
                return None
            
            data = result.get('data', {})
            fields_list = data.get('fields', [])
            items = data.get('items', [])
            
            if not items:
                return None
            
            df = pd.DataFrame(items, columns=fields_list)
            return df
            
        except Exception as e:
            logger.warning(f"API调用失败: {e}")
            return None
    
    def run(self, task_input: Dict) -> Dict:
        """
        执行数据抓取任务
        
        task_input: {
            'codes': ['518880.SH', '300394.SZ'],  # 资产代码列表
            'start_date': '20260101',
            'end_date': '20260320',
            'data_types': ['price', 'fundamentals', 'holdings'],
            'use_mock': False  # 是否使用模拟数据
        }
        """
        results = {
            'status': 'success',
            'data': {},
            'errors': [],
            'timestamp': datetime.now().isoformat()
        }
        
        codes = task_input.get('codes', [])
        start_date = task_input.get('start_date')
        end_date = task_input.get('end_date', datetime.now().strftime('%Y%m%d'))
        data_types = task_input.get('data_types', ['price'])
        use_mock = task_input.get('use_mock', False)
        
        logger.info(f"开始抓取数据: {len(codes)}个资产, 类型: {data_types}")
        
        for code in codes:
            try:
                asset_data = {}
                
                # 获取行情数据
                if 'price' in data_types:
                    if use_mock:
                        price_data = self._get_mock_price_data(code, start_date, end_date)
                    else:
                        price_data = self._get_price_data(code, start_date, end_date)
                    if price_data is not None:
                        asset_data['price'] = price_data
                
                # 获取基本面数据（仅股票）
                if 'fundamentals' in data_types and self._is_stock(code):
                    fundamentals = self._get_fundamentals(code)
                    if fundamentals:
                        asset_data['fundamentals'] = fundamentals
                
                # 获取机构持仓（仅股票）
                if 'holdings' in data_types and self._is_stock(code):
                    holdings = self._get_holdings(code)
                    if holdings:
                        asset_data['holdings'] = holdings
                
                results['data'][code] = asset_data
                logger.info(f"✓ {code}: 抓取完成")
                
            except Exception as e:
                logger.error(f"✗ {code}: 抓取失败 - {e}")
                results['errors'].append({'code': code, 'error': str(e)})
        
        # 获取基准数据
        if 'benchmark' in data_types:
            if use_mock:
                results['benchmarks'] = self._get_mock_benchmark_data(start_date, end_date)
            else:
                results['benchmarks'] = self._get_benchmark_data(start_date, end_date)
        
        logger.info(f"数据抓取完成: 成功{len(results['data'])}, 失败{len(results['errors'])}")
        return results
    
    def _get_mock_price_data(self, code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """生成模拟价格数据用于测试"""
        try:
            # 生成交易日序列
            dates = pd.date_range(start=start_date, end=end_date, freq='B')  # 工作日
            
            # 根据资产类型设置不同的基础价格和波动率
            base_prices = {
                '518880.SH': 5.5,    # 黄金ETF
                '159562.SZ': 1.2,    # 黄金股ETF
                '512710.SH': 1.0,    # 军工
                '300394.SZ': 85.0,   # 天孚通信
                '688195.SH': 45.0,   # 腾景科技
                '512480.SH': 0.9,    # 半导体
                '159819.SZ': 0.8,    # AI ETF
                '159326.SZ': 1.1,    # 电网
                '159611.SZ': 1.3,    # 电力
                '513130.SH': 0.6,    # 恒生科技
                '513120.SH': 0.7,    # 港股创新药
            }
            
            base = base_prices.get(code, 1.0)
            
            # 生成随机价格序列
            np.random.seed(hash(code) % 10000)  # 固定随机种子
            returns = np.random.normal(0.0005, 0.02, len(dates))  # 日均收益0.05%，波动2%
            
            # 添加趋势
            trend = np.linspace(0, 0.1, len(dates))  # 10%的上涨趋势
            returns += trend / len(dates)
            
            # 计算价格
            prices = base * (1 + returns).cumprod()
            
            df = pd.DataFrame({
                'trade_date': dates,
                'open': prices * 0.995,
                'high': prices * 1.02,
                'low': prices * 0.98,
                'close': prices,
                'vol': np.random.randint(1000000, 10000000, len(dates)),
                'amount': np.random.randint(10000000, 100000000, len(dates)),
            })
            
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            df['daily_return'] = df['close'].pct_change()
            
            return df
        except Exception as e:
            logger.warning(f"{code} 模拟数据生成失败: {e}")
            return None
    
    def _get_mock_benchmark_data(self, start_date: str, end_date: str) -> Dict:
        """生成模拟基准数据"""
        benchmarks = {}
        for code, config in self.config.BENCHMARK_CONFIG.items():
            try:
                dates = pd.date_range(start=start_date, end=end_date, freq='B')
                
                base = 4000 if code == '000300.SH' else 4500
                np.random.seed(hash(code) % 10000)
                returns = np.random.normal(0.0003, 0.015, len(dates))
                trend = np.linspace(0, 0.08, len(dates))
                returns += trend / len(dates)
                prices = base * (1 + returns).cumprod()
                
                df = pd.DataFrame({
                    'trade_date': dates,
                    'open': prices * 0.995,
                    'high': prices * 1.015,
                    'low': prices * 0.985,
                    'close': prices,
                })
                
                df['trade_date'] = pd.to_datetime(df['trade_date'])
                df['daily_return'] = df['close'].pct_change()
                benchmarks[code] = df
            except Exception as e:
                logger.warning(f"基准 {code} 模拟数据生成失败: {e}")
        return benchmarks
    
    def _get_price_data(self, code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """获取行情数据"""
        try:
            if self._is_etf(code):
                # ETF日线数据
                df = self._call_api(
                    'fund_daily',
                    params={'ts_code': code, 'start_date': start_date, 'end_date': end_date},
                    fields='ts_code,trade_date,open,high,low,close,vol,amount'
                )
            else:
                # 股票日线数据
                df = self._call_api(
                    'daily',
                    params={'ts_code': code, 'start_date': start_date, 'end_date': end_date},
                    fields='ts_code,trade_date,open,high,low,close,vol,amount'
                )
            
            if df is not None and len(df) > 0:
                df = df.sort_values('trade_date').reset_index(drop=True)
                df['trade_date'] = pd.to_datetime(df['trade_date'])
                df['close'] = df['close'].astype(float)
                df['daily_return'] = df['close'].pct_change()
                return df
            return None
        except Exception as e:
            logger.warning(f"{code} 价格数据获取失败: {e}")
            return None
    
    def _get_fundamentals(self, code: str) -> Optional[Dict]:
        """获取基本面数据"""
        try:
            df = self._call_api(
                'fina_indicator',
                params={'ts_code': code, 'period': '2024Q3'},
                fields='ts_code,roe,grossprofit_margin,debt_to_assets,eps,bps,end_date'
            )
            if df is not None and len(df) > 0:
                row = df.iloc[0]
                return {
                    'roe': float(row.get('roe', 0)) if row.get('roe') else None,
                    'grossprofit_margin': float(row.get('grossprofit_margin', 0)) if row.get('grossprofit_margin') else None,
                    'debt_to_assets': float(row.get('debt_to_assets', 0)) if row.get('debt_to_assets') else None,
                    'eps': float(row.get('eps', 0)) if row.get('eps') else None,
                    'bps': float(row.get('bps', 0)) if row.get('bps') else None,
                    'period': row.get('end_date')
                }
            return None
        except Exception as e:
            logger.warning(f"{code} 基本面数据获取失败: {e}")
            return None
    
    def _get_holdings(self, code: str) -> Optional[Dict]:
        """获取机构持仓数据（简化版）"""
        try:
            # 获取基金持仓数量
            df_fund = self._call_api(
                'fund_holdings',
                params={'ts_code': code},
                fields='ts_code,end_date,holdings'
            )
            
            return {
                'fund_count': len(df_fund) if df_fund is not None else 0,
                'northbound_trend': 'unknown'
            }
        except Exception as e:
            logger.warning(f"{code} 持仓数据获取失败: {e}")
            return None
    
    def _get_benchmark_data(self, start_date: str, end_date: str) -> Dict:
        """获取基准数据"""
        benchmarks = {}
        for code in self.config.BENCHMARK_CONFIG.keys():
            try:
                df = self._call_api(
                    'index_daily',
                    params={'ts_code': code, 'start_date': start_date, 'end_date': end_date},
                    fields='ts_code,trade_date,open,high,low,close,vol,amount'
                )
                if df is not None and len(df) > 0:
                    df = df.sort_values('trade_date').reset_index(drop=True)
                    df['trade_date'] = pd.to_datetime(df['trade_date'])
                    df['close'] = df['close'].astype(float)
                    df['daily_return'] = df['close'].pct_change()
                    benchmarks[code] = df
            except Exception as e:
                logger.warning(f"基准 {code} 获取失败: {e}")
        return benchmarks
    
    def _is_etf(self, code: str) -> bool:
        """判断是否为ETF"""
        return code in self.config.PORTFOLIO_CONFIG and \
               self.config.PORTFOLIO_CONFIG[code].get('type') == 'etf'
    
    def _is_stock(self, code: str) -> bool:
        """判断是否为股票"""
        return code in self.config.PORTFOLIO_CONFIG and \
               self.config.PORTFOLIO_CONFIG[code].get('type') == 'stock'
    
    def get_daily_update(self, codes: List[str]) -> Dict:
        """获取每日更新数据（收盘后调用）"""
        today = datetime.now().strftime('%Y%m%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
        
        return self.run({
            'codes': codes,
            'start_date': yesterday,
            'end_date': today,
            'data_types': ['price']
        })
    
    def calculate_portfolio_returns(self, data: Dict, weights: Dict) -> pd.DataFrame:
        """
        计算组合收益率
        
        data: DataMiner.run()的输出
        weights: {'code': weight, ...}
        """
        portfolio_data = data.get('data', {})
        
        # 统一交易日
        trading_dates = None
        for code, asset_data in portfolio_data.items():
            if 'price' in asset_data:
                dates = set(asset_data['price']['trade_date'])
                if trading_dates is None:
                    trading_dates = dates
                else:
                    trading_dates = trading_dates & dates
        
        if not trading_dates:
            logger.error("没有统一的交易日")
            return pd.DataFrame()
        
        trading_dates = sorted(list(trading_dates))
        
        # 计算每日组合收益
        returns_df = pd.DataFrame({'date': trading_dates})
        returns_df['portfolio_return'] = 0.0
        
        for i, date in enumerate(trading_dates):
            daily_return = 0
            
            for code, weight in weights.items():
                if code not in portfolio_data:
                    continue
                    
                asset_data = portfolio_data[code]
                if 'price' not in asset_data:
                    continue
                
                price_df = asset_data['price']
                day_data = price_df[price_df['trade_date'] == date]
                
                if len(day_data) > 0:
                    ret = day_data['daily_return'].values[0]
                    if not pd.isna(ret):
                        daily_return += weight * ret
            
            returns_df.loc[i, 'portfolio_return'] = daily_return
        
        # 计算累计收益
        returns_df['cum_return'] = (1 + returns_df['portfolio_return']).cumprod() - 1
        returns_df['nav'] = 1 + returns_df['cum_return']
        
        return returns_df


if __name__ == '__main__':
    # 测试
    import sys
    sys.path.append('/root/.openclaw/workspace/investment_system')
    from config.config import *
    
    agent = DataMinerAgent(Config())
    
    # 测试数据抓取
    result = agent.run({
        'codes': ['518880.SH', '300394.SZ'],
        'start_date': '20260301',
        'end_date': '20260320',
        'data_types': ['price']
    })
    
    print(f"成功: {len(result['data'])}")
    print(f"失败: {len(result['errors'])}")
