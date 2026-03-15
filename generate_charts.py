#!/usr/bin/env python3
"""
股票市场周度总结报告 - 图文并茂版
生成包含图表的专业PDF报告
"""

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 无头模式
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'SimHei', 'Noto Sans CJK SC']
plt.rcParams['axes.unicode_minus'] = False

import os

# 创建输出目录
output_dir = '/root/.openclaw/workspace/report_images'
os.makedirs(output_dir, exist_ok=True)

# 1. 指数本周走势对比图
fig, ax = plt.subplots(figsize=(10, 6))
indices = ['上证指数', '深证成指', '创业板指', '科创50']
changes = [-1.40, -1.87, -2.44, -2.37]
colors = ['#ff6b6b' if x < 0 else '#51cf66' for x in changes]

bars = ax.barh(indices, changes, color=colors, edgecolor='white', linewidth=1.5)
ax.axvline(x=0, color='black', linestyle='-', linewidth=0.8)
ax.set_xlabel('周涨跌幅 (%)', fontsize=12, fontweight='bold')
ax.set_title('主要指数本周表现', fontsize=16, fontweight='bold', pad=20)
ax.set_xlim(-3, 1)

# 添加数值标签
for bar, change in zip(bars, changes):
    width = bar.get_width()
    ax.text(width - 0.15 if width < 0 else width + 0.05, bar.get_y() + bar.get_height()/2,
            f'{change:.2f}%', ha='right' if width < 0 else 'left', va='center', fontsize=11, fontweight='bold')

plt.tight_layout()
plt.savefig(f'{output_dir}/chart1_indices.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print('✓ 图表1: 指数走势对比图')

# 2. ETF资金流向图
fig, ax = plt.subplots(figsize=(10, 6))
etfs = ['沪深300', '黄金ETF', '半导体', '券商', '新能源车', '创业板']
week_amount = [125, 89, 168, 45, 112, 98]
prev_amount = [142, 156, 145, 52, 108, 115]

x = range(len(etfs))
width = 0.35

bars1 = ax.bar([i - width/2 for i in x], prev_amount, width, label='上周成交额', color='#74c0fc', edgecolor='white')
bars2 = ax.bar([i + width/2 for i in x], week_amount, width, label='本周成交额', color='#339af0', edgecolor='white')

ax.set_ylabel('成交额 (亿元)', fontsize=12, fontweight='bold')
ax.set_title('ETF资金流向对比', fontsize=16, fontweight='bold', pad=20)
ax.set_xticks(x)
ax.set_xticklabels(etfs, rotation=15, ha='right')
ax.legend(loc='upper right', fontsize=10)

# 添加数值标签
for bar in bars2:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 2,
            f'{int(height)}', ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.savefig(f'{output_dir}/chart2_etf_flow.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print('✓ 图表2: ETF资金流向图')

# 3. 板块涨跌幅对比图
fig, ax = plt.subplots(figsize=(10, 6))
sectors = ['黄金', '机器人', '半导体', '券商', '新能源', '医药']
changes = [-10.19, -4.93, -2.91, -3.12, -2.98, 0.86]
colors = ['#ff6b6b' if x < 0 else '#51cf66' for x in changes]

bars = ax.bar(sectors, changes, color=colors, edgecolor='white', linewidth=1.5)
ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
ax.set_ylabel('周涨跌幅 (%)', fontsize=12, fontweight='bold')
ax.set_title('重点板块本周表现', fontsize=16, fontweight='bold', pad=20)
ax.set_ylim(-12, 3)

# 添加数值标签
for bar, change in zip(bars, changes):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + (-0.5 if height < 0 else 0.2),
            f'{change:.2f}%', ha='center', va='top' if height < 0 else 'bottom', fontsize=11, fontweight='bold')

# 添加大盘参考线
ax.axhline(y=-1.40, color='#868e96', linestyle='--', linewidth=1.5, alpha=0.7, label='上证指数 -1.40%')
ax.legend(loc='lower right', fontsize=10)

plt.tight_layout()
plt.savefig(f'{output_dir}/chart3_sectors.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print('✓ 图表3: 板块涨跌幅对比图')

# 4. 市场情绪仪表盘（模拟）
fig, axes = plt.subplots(2, 2, figsize=(10, 8))
fig.suptitle('市场情绪指标仪表盘', fontsize=16, fontweight='bold', y=0.98)

# 涨跌家数比
ax1 = axes[0, 0]
labels = ['上涨', '下跌']
sizes = [35, 65]
colors1 = ['#51cf66', '#ff6b6b']
ax1.pie(sizes, labels=labels, autopct='%1.0f%%', colors=colors1, startangle=90, textprops={'fontsize': 11})
ax1.set_title('涨跌家数比', fontsize=12, fontweight='bold')

# 成交额变化
ax2 = axes[0, 1]
weeks = ['上周', '本周']
amounts = [8400, 7400]
bars = ax2.bar(weeks, amounts, color=['#74c0fc', '#339af0'], edgecolor='white', linewidth=2)
ax2.set_ylabel('成交额 (亿元)', fontsize=10)
ax2.set_title('两市成交额', fontsize=12, fontweight='bold')
for bar, amt in zip(bars, amounts):
    ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 100,
             f'{amt}亿', ha='center', va='bottom', fontsize=10, fontweight='bold')

# 涨停跌停数
ax3 = axes[1, 0]
categories = ['涨停', '跌停']
this_week = [45, 12]
last_week = [68, 5]
x = range(len(categories))
width = 0.35
ax3.bar([i - width/2 for i in x], last_week, width, label='上周', color='#74c0fc')
ax3.bar([i + width/2 for i in x], this_week, width, label='本周', color='#339af0')
ax3.set_ylabel('家数', fontsize=10)
ax3.set_title('涨停跌停对比', fontsize=12, fontweight='bold')
ax3.set_xticks(x)
ax3.set_xticklabels(categories)
ax3.legend()

# 换手率分布
ax4 = axes[1, 1]
labels = ['<1%', '1-3%', '3-5%', '>5%']
sizes = [25, 45, 20, 10]
colors4 = ['#a9e34b', '#69db7c', '#38d9a9', '#3bc9db']
ax4.pie(sizes, labels=labels, autopct='%1.0f%%', colors=colors4, startangle=90, textprops={'fontsize': 11})
ax4.set_title('换手率分布', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig(f'{output_dir}/chart4_sentiment.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print('✓ 图表4: 市场情绪仪表盘')

print(f'\n所有图表已保存到: {output_dir}/')
print('图表列表:')
for f in os.listdir(output_dir):
    print(f'  - {f}')
