#!/usr/bin/env python3
"""
股票市场周度总结报告 - 图表生成（红涨绿跌版）
"""

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei', 'Noto Sans CJK JP', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

import os

output_dir = '/root/.openclaw/workspace/report_images'
os.makedirs(output_dir, exist_ok=True)

# 删除旧图表
for f in os.listdir(output_dir):
    os.remove(os.path.join(output_dir, f))

print('开始生成图表...')

# 中国股市配色：红涨绿跌
COLOR_UP = '#cc0000'      # 红色-涨
COLOR_DOWN = '#006600'    # 绿色-跌
COLOR_NEUTRAL = '#666666' # 灰色-中性

# 1. 指数本周走势对比图
fig, ax = plt.subplots(figsize=(10, 6))
indices = ['上证指数', '深证成指', '创业板指', '科创50']
changes = [-1.40, -1.87, -2.44, -2.37]
# 跌幅用绿色（中国股市习惯）
colors = [COLOR_DOWN if x < 0 else COLOR_UP for x in changes]

bars = ax.barh(indices, changes, color=colors, edgecolor='white', linewidth=1.5)
ax.axvline(x=0, color='black', linestyle='-', linewidth=0.8)
ax.set_xlabel('周涨跌幅 (%)', fontsize=12, color='black')
ax.set_title('主要指数本周表现', fontsize=16, pad=20, color='black')
ax.set_xlim(-3, 1)

# 添加数值标签
for bar, change in zip(bars, changes):
    width = bar.get_width()
    label_x = width - 0.1 if width < 0 else width + 0.05
    color = COLOR_DOWN if change < 0 else COLOR_UP
    ax.text(label_x, bar.get_y() + bar.get_height()/2,
            f'{change:.2f}%', ha='right' if width < 0 else 'left', 
            va='center', fontsize=11, color=color, fontweight='bold')

plt.tight_layout()
plt.savefig(f'{output_dir}/chart1_indices.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print('✓ 图表1: 指数走势对比图（红涨绿跌）')

# 2. ETF资金流向图
fig, ax = plt.subplots(figsize=(10, 6))
etfs = ['沪深300', '黄金ETF', '半导体', '券商', '新能源车', '创业板']
week_amount = [125, 89, 168, 45, 112, 98]
prev_amount = [142, 156, 145, 52, 108, 115]

x = range(len(etfs))
width = 0.35

bars1 = ax.bar([i - width/2 for i in x], prev_amount, width, 
               label='上周成交额', color='#999999', edgecolor='white')
bars2 = ax.bar([i + width/2 for i in x], week_amount, width, 
               label='本周成交额', color='#3366cc', edgecolor='white')

ax.set_ylabel('成交额 (亿元)', fontsize=12, color='black')
ax.set_title('ETF资金流向对比', fontsize=16, pad=20, color='black')
ax.set_xticks(x)
ax.set_xticklabels(etfs, rotation=15, ha='right', color='black')
ax.legend(loc='upper right', fontsize=10)

# 添加数值标签
for bar in bars2:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 2,
            f'{int(height)}', ha='center', va='bottom', fontsize=9, color='black')

plt.tight_layout()
plt.savefig(f'{output_dir}/chart2_etf_flow.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print('✓ 图表2: ETF资金流向图')

# 3. 板块涨跌幅对比图
fig, ax = plt.subplots(figsize=(10, 6))
sectors = ['黄金板块', '机器人', '半导体', '券商', '新能源', '医药']
changes = [-10.19, -4.93, -2.91, -3.12, -2.98, 0.86]
# 红涨绿跌
colors = [COLOR_DOWN if x < 0 else COLOR_UP for x in changes]

bars = ax.bar(sectors, changes, color=colors, edgecolor='white', linewidth=1.5)
ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
ax.set_ylabel('周涨跌幅 (%)', fontsize=12, color='black')
ax.set_title('重点板块本周表现', fontsize=16, pad=20, color='black')
ax.set_ylim(-12, 3)
ax.set_xticklabels(sectors, rotation=15, ha='right', color='black')

# 添加数值标签
for bar, change in zip(bars, changes):
    height = bar.get_height()
    label_y = height - 0.5 if height < 0 else height + 0.2
    color = COLOR_DOWN if change < 0 else COLOR_UP
    ax.text(bar.get_x() + bar.get_width()/2., label_y,
            f'{change:.2f}%', ha='center', va='top' if height < 0 else 'bottom', 
            fontsize=11, color=color, fontweight='bold')

# 添加大盘参考线
ax.axhline(y=-1.40, color='#999999', linestyle='--', linewidth=1.5, label='上证指数 -1.40%')
ax.legend(loc='lower right', fontsize=10)

plt.tight_layout()
plt.savefig(f'{output_dir}/chart3_sectors.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print('✓ 图表3: 板块涨跌幅对比图（红涨绿跌）')

# 4. 市场情绪仪表盘
fig, axes = plt.subplots(2, 2, figsize=(10, 8))
fig.suptitle('市场情绪指标仪表盘', fontsize=16, color='black', y=0.98)

# 涨跌家数比
ax1 = axes[0, 0]
labels = ['上涨(35%)', '下跌(65%)']
sizes = [35, 65]
# 上涨红色，下跌绿色
colors1 = [COLOR_UP, COLOR_DOWN]
ax1.pie(sizes, labels=labels, autopct='%1.0f%%', colors=colors1, 
        startangle=90, textprops={'fontsize': 11, 'color': 'black'})
ax1.set_title('涨跌家数比', fontsize=12, color='black')

# 成交额变化
ax2 = axes[0, 1]
weeks = ['上周', '本周']
amounts = [8400, 7400]
bars = ax2.bar(weeks, amounts, color=['#999999', '#3366cc'], edgecolor='white', linewidth=2)
ax2.set_ylabel('成交额 (亿元)', fontsize=10, color='black')
ax2.set_title('两市成交额', fontsize=12, color='black')
for bar, amt in zip(bars, amounts):
    ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 100,
             f'{amt}亿', ha='center', va='bottom', fontsize=10, color='black')

# 涨停跌停数
ax3 = axes[1, 0]
categories = ['涨停', '跌停']
this_week = [45, 12]
last_week = [68, 5]
x = range(len(categories))
width = 0.35
ax3.bar([i - width/2 for i in x], last_week, width, label='上周', color='#999999')
ax3.bar([i + width/2 for i in x], this_week, width, label='本周', color='#3366cc')
ax3.set_ylabel('家数', fontsize=10, color='black')
ax3.set_title('涨停跌停对比', fontsize=12, color='black')
ax3.set_xticks(x)
ax3.set_xticklabels(categories, color='black')
ax3.legend()

# 换手率分布
ax4 = axes[1, 1]
labels = ['<1%', '1-3%', '3-5%', '>5%']
sizes = [25, 45, 20, 10]
colors4 = ['#99cc99', '#66cc66', '#33cc33', '#009900']
ax4.pie(sizes, labels=labels, autopct='%1.0f%%', colors=colors4, 
        startangle=90, textprops={'fontsize': 11, 'color': 'black'})
ax4.set_title('换手率分布', fontsize=12, color='black')

plt.tight_layout()
plt.savefig(f'{output_dir}/chart4_sentiment.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print('✓ 图表4: 市场情绪仪表盘')

print(f'\n所有图表已保存到: {output_dir}/')
print('图表列表:')
for f in sorted(os.listdir(output_dir)):
    print(f'  - {f}')
