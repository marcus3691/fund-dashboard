#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SMART资产配置模型
基于张忆东/韦冀星研报框架的主题配置策略
"""

import logging
from typing import Dict, List, Tuple
from dataclasses import dataclass

import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('SMARTPortfolio')


@dataclass
class SMARTConfig:
    """SMART配置参数"""
    security_weight: float = 0.35      # Security 能源安全
    manufacturing_weight: float = 0.25  # Manufacturing Abroad 制造出海
    rd_weight: float = 0.25            # R&D Technology 硬科技
    cash_weight: float = 0.15          # 现金/黄金避险
    
    # 子配置
    gold_ratio: float = 0.60           # Security中黄金占比
    defense_ratio: float = 0.25        # Security中军工占比
    power_ratio: float = 0.15          # Security中电力占比
    
    grid_ratio: float = 0.70           # Manufacturing中电网占比
    equipment_ratio: float = 0.30      # Manufacturing中设备出海占比
    
    ai_ratio: float = 0.50             # R&D中AI/光模块占比
    semi_ratio: float = 0.35           # R&D中半导体占比
    biotech_ratio: float = 0.15        # R&D中创新药占比


class SMARTPortfolioModel:
    """
    SMART资产配置模型
    
    核心逻辑：
    1. Security (35%): 能源安全主题 - 黄金+军工+电力
    2. Manufacturing Abroad (25%): 制造出海 - 电网设备+机械设备
    3. R&D Technology (25%): 硬科技 - AI算力+半导体+创新药
    4. Cash/Gold (15%): 反脆弱性缓冲
    """
    
    def __init__(self, config: SMARTConfig = None):
        self.config = config or SMARTConfig()
        
        # 资产映射表
        self.asset_mapping = {
            # Security - 能源安全
            '518880.SH': {'sector': 'security', 'sub': 'gold', 'name': '黄金ETF'},
            '159562.SZ': {'sector': 'security', 'sub': 'gold', 'name': '黄金股ETF'},
            '512710.SH': {'sector': 'security', 'sub': 'defense', 'name': '军工龙头ETF'},
            '159326.SZ': {'sector': 'security', 'sub': 'power', 'name': '电网设备ETF'},
            '159611.SZ': {'sector': 'security', 'sub': 'power', 'name': '电力ETF'},
            
            # Manufacturing Abroad - 制造出海
            '300394.SZ': {'sector': 'manufacturing', 'sub': 'equipment', 'name': '天孚通信'},
            '688195.SH': {'sector': 'manufacturing', 'sub': 'equipment', 'name': '腾景科技'},
            
            # R&D Technology - 硬科技
            '512480.SH': {'sector': 'rd', 'sub': 'semi', 'name': '半导体ETF'},
            '159819.SZ': {'sector': 'rd', 'sub': 'ai', 'name': '人工智能ETF'},
            '513120.SH': {'sector': 'rd', 'sub': 'biotech', 'name': '港股创新药ETF'},
            
            # 港股/其他
            '513130.SH': {'sector': 'other', 'sub': 'hk', 'name': '恒生科技ETF'},
        }
    
    def calculate_weights(self, current_weights: Dict = None) -> Dict[str, float]:
        """
        计算SMART配置权重
        
        Returns:
            {'code': weight, ...}
        """
        cfg = self.config
        weights = {}
        
        # 1. Security 配置 (35%)
        security_total = cfg.security_weight
        gold_weight = security_total * cfg.gold_ratio
        defense_weight = security_total * cfg.defense_ratio
        power_weight = security_total * cfg.power_ratio
        
        # 黄金配置 (21% = 35% * 60%)
        weights['518880.SH'] = gold_weight * 0.60  # 12.6%
        weights['159562.SZ'] = gold_weight * 0.40  # 8.4%
        
        # 军工配置 (8.75% = 35% * 25%)
        weights['512710.SH'] = defense_weight  # 8.75%
        
        # 电力配置 (5.25% = 35% * 15%)
        weights['159326.SZ'] = power_weight * 0.65  # 3.4%
        weights['159611.SZ'] = power_weight * 0.35  # 1.85%
        
        # 2. Manufacturing Abroad 配置 (25%)
        mfg_total = cfg.manufacturing_weight
        grid_weight = mfg_total * cfg.grid_ratio
        equip_weight = mfg_total * cfg.equipment_ratio
        
        # 电网设备 (17.5% = 25% * 70%)
        # 合并到电力ETF中
        weights['159326.SZ'] += grid_weight * 0.70
        weights['159611.SZ'] += grid_weight * 0.30
        
        # 设备出海 (7.5% = 25% * 30%)
        weights['300394.SZ'] = equip_weight * 0.35  # 2.6%
        weights['688195.SH'] = equip_weight * 0.65  # 4.9%
        
        # 3. R&D Technology 配置 (25%)
        rd_total = cfg.rd_weight
        ai_weight = rd_total * cfg.ai_ratio
        semi_weight = rd_total * cfg.semi_ratio
        biotech_weight = rd_total * cfg.biotech_ratio
        
        # AI/光模块 (12.5% = 25% * 50%)
        # 由个股覆盖
        
        # 半导体 (8.75% = 25% * 35%)
        weights['512480.SH'] = semi_weight  # 8.75%
        
        # 创新药 (3.75% = 25% * 15%)
        weights['513120.SH'] = biotech_weight  # 3.75%
        
        # 4. 港股科技 - 作为卫星配置
        weights['513130.SH'] = 0.05  # 5%
        
        # 5. 现金隐含在剩余权重中
        total_allocated = sum(weights.values())
        cash = 1.0 - total_allocated  # 约15%
        
        logger.info(f"SMART配置完成: 权益{total_allocated*100:.1f}% + 现金{cash*100:.1f}%")
        
        return weights, cash
    
    def generate_report(self, weights: Dict, cash: float) -> str:
        """生成SMART配置报告"""
        
        # 计算各主题权重
        theme_weights = {'Security': 0, 'Manufacturing': 0, 'R&D': 0, 'Other': 0}
        for code, w in weights.items():
            if code in self.asset_mapping:
                sector = self.asset_mapping[code]['sector']
                if sector == 'security':
                    theme_weights['Security'] += w
                elif sector == 'manufacturing':
                    theme_weights['Manufacturing'] += w
                elif sector == 'rd':
                    theme_weights['R&D'] += w
                else:
                    theme_weights['Other'] += w
        
        report = f"""# SMART资产配置报告

## 一、配置框架

基于张忆东/韦冀星研报框架，采用主题配置策略：

| 主题 | 权重 | 配置逻辑 |
|:---|:---:|:---|
| **S - Security** | {theme_weights['Security']*100:.1f}% | 能源安全：黄金+军工+电力 |
| **M - Manufacturing** | {theme_weights['Manufacturing']*100:.1f}% | 制造出海：电网+设备 |
| **A - R&D Tech** | {theme_weights['R&D']*100:.1f}% | 硬科技：AI+半导体+创新药 |
| **R - Risk Off** | {cash*100:.1f}% | 现金/黄金避险缓冲 |
| **其他** | {theme_weights['Other']*100:.1f}% | 港股科技等卫星配置 |

## 二、详细配置

### Security（能源安全）

| 资产 | 权重 | 细分主题 |
|:---|:---:|:---|
"""
        
        for code, w in weights.items():
            if code in self.asset_mapping and self.asset_mapping[code]['sector'] == 'security':
                name = self.asset_mapping[code]['name']
                sub = self.asset_mapping[code]['sub']
                report += f"| {code} {name} | {w*100:.2f}% | {sub} |\n"
        
        report += f"""
### Manufacturing Abroad（制造出海）

| 资产 | 权重 | 细分主题 |
|:---|:---:|:---|
"""
        
        for code, w in weights.items():
            if code in self.asset_mapping and self.asset_mapping[code]['sector'] == 'manufacturing':
                name = self.asset_mapping[code]['name']
                sub = self.asset_mapping[code]['sub']
                report += f"| {code} {name} | {w*100:.2f}% | {sub} |\n"
        
        report += f"""
### R&D Technology（硬科技）

| 资产 | 权重 | 细分主题 |
|:---|:---:|:---|
"""
        
        for code, w in weights.items():
            if code in self.asset_mapping and self.asset_mapping[code]['sector'] == 'rd':
                name = self.asset_mapping[code]['name']
                sub = self.asset_mapping[code]['sub']
                report += f"| {code} {name} | {w*100:.2f}% | {sub} |\n"
        
        report += f"""
### 其他配置

| 资产 | 权重 | 说明 |
|:---|:---:|:---|
"""
        
        for code, w in weights.items():
            if code in self.asset_mapping and self.asset_mapping[code]['sector'] == 'other':
                name = self.asset_mapping[code]['name']
                report += f"| {code} {name} | {w*100:.2f}% | 卫星配置 |\n"
        
        report += f"""
## 三、配置逻辑

### 1. Security（能源安全）- {theme_weights['Security']*100:.1f}%

**核心逻辑**：国际秩序重构，安全赤字扩大

- **黄金（{self.config.gold_ratio*100:.0f}%）**: 美元武器化背景下，黄金成为终极信用锚
- **军工（{self.config.defense_ratio*100:.0f}%）**: 地缘冲突长期化，军费开支上升
- **电力（{self.config.power_ratio*100:.0f}%）**: 能源自主"大动脉"，十五五规划重点

### 2. Manufacturing Abroad（制造出海）- {theme_weights['Manufacturing']*100:.1f}%

**核心逻辑**：供应链重组，制造业出海红利

- **电网设备（{self.config.grid_ratio*100:.0f}%）**: 算电协同首次写入政府工作报告
- **设备出海（{self.config.equipment_ratio*100:.0f}%）**: 电力设备出口高增长

### 3. R&D Technology（硬科技）- {theme_weights['R&D']*100:.1f}%

**核心逻辑**：科技自立，国产替代加速

- **AI/光模块（{self.config.ai_ratio*100:.0f}%）**: 算力需求爆发
- **半导体（{self.config.semi_ratio*100:.0f}%）**: 国产替代关键领域
- **创新药（{self.config.biotech_ratio*100:.0f}%）**: 老龄化+出海双驱动

### 4. 现金缓冲 - {cash*100:.1f}%

**反脆弱性配置**：地缘不确定性下的防御仓位

---

*配置时间: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}*
*框架来源: 张忆东SMART + 韦冀星电力设备研报*
"""
        
        return report


if __name__ == '__main__':
    model = SMARTPortfolioModel()
    weights, cash = model.calculate_weights()
    
    print("SMART配置权重:")
    for code, w in sorted(weights.items(), key=lambda x: -x[1]):
        print(f"  {code}: {w*100:.2f}%")
    print(f"  现金: {cash*100:.2f}%")
    print(f"\n总权重: {(sum(weights.values()) + cash)*100:.1f}%")
