# 基金产品库筛选SOP（标准操作流程）

**版本**: v2.0  
**更新日期**: 2026-03-10  
**适用范围**: 股票型、混合型公募基金产品库建设

---

## 一、流程概览

```
原始数据(6277只)
    ↓
去重处理 → 3778只（去除A/C/E重复份额）
    ↓
一级筛选（3项必须满足）→ 208只
    ↓
二级筛选（质量分≥70）→ 196只
    ↓
产品库分级 → 核心库121只 + 观察库75只
```

---

## 二、详细步骤

### Step 1: 数据准备

**输入文件**: `fund_screening_all.csv`

**必要字段**:
| 字段 | 说明 | 用途 |
|:---|:---|:---|
| ts_code | 基金代码 | 唯一标识 |
| name | 基金名称 | 去重依据 |
| category | 基金分类 | 筛选对象 |
| return_1y | 近1年收益 | 业绩筛选 |
| percentile_1y | 1年排名百分位 | 一级筛选 |
| percentile_6m | 6月排名百分位 | 一级筛选 |
| volatility | 年化波动率 | 风险筛选 |
| quality_score | 质量评分 | 二级筛选 |
| ~~fund_size~~ | ~~基金规模(亿元)~~ | ~~【TODO:待补充】规模筛选~~ |

> **⚠️ TODO: 基金规模数据待补充**
> 
> 当前版本缺少规模字段，需后续补充。建议筛选标准：
> - **一票否决**: 规模 < 1亿元（清盘风险）
> - **优选区间**: 5-50亿元（策略有效）
> - **观察区间**: 1-5亿元或 >100亿元（业绩可能不可持续或灵活性下降）

### Step 2: 去重处理

**去重逻辑**:
1. 提取基金基础名称（去掉A/C/E等份额后缀和持有期标识）
2. 同一基础名称的基金视为同一只基金的不同份额
3. 保留质量分最高的一只

**代码实现**:
```python
def get_base_name(name):
    base = re.sub(r'[A-Z]$', '', name)  # 去掉末尾份额标识
    base = re.sub(r'(一年|三个月|六个月|两年|三年)持有$', '', base)
    base = re.sub(r'定期开放$', '', base)
    return base.strip()

# 保留质量分最高的一只
df_sorted = df.sort_values(['base_name', 'quality_score'], ascending=[True, False])
df_dedup = df_sorted.drop_duplicates(subset=['base_name'], keep='first')
```

**输出**: 去重后基金数量（约原数据的60%）

### Step 3: 类别筛选

**筛选对象**: 以下3个类别纳入产品库范围
- `主动股票型` — 股票仓位>80%
- `混合型-偏股` — 股票仓位60-80%
- `混合型-平衡` — 股票仓位40-60%

**排除类别**:
- 债券型（单独评估体系）
- 指数型（被动跟踪，不纳入主动产品库）
- FOF（基金中基金，单独评估）
- QDII（海外投资，单独评估）

### Step 4: 一级筛选（必须全部满足）

**筛选条件**（3项必须同时满足）:

| 条件 | 标准 | 逻辑 |
|:---|:---|:---|
| 近1年业绩 | 同类排名前10% | `percentile_1y >= 90` |
| 近6月业绩 | 同类排名前20% | `percentile_6m >= 80` |
| 波动率 | 不高于同类90%分位 | `volatility <= category_vol_90` |

**高波动阈值参考**（2025年数据）:
- 主动股票型: ≤25.0%
- 混合型-偏股: ≤24.0%
- 混合型-平衡: ≤25.0%

### Step 5: 二级筛选（质量评分）

**入选标准**: `quality_score >= 70`

**质量分构成**（原始数据已计算）:
| 指标 | 权重 | 说明 |
|:---|:---:|:---|
| 夏普比率 | 30% | 风险调整后收益 |
| 最大回撤 | 25% | 极端风险控制 |
| 年化波动率 | 20% | 波动水平 |
| 月度胜率 | 15% | 盈利稳定性 |
| 盈亏比 | 10% | 收益风险比 |

### Step 6: 产品库分级

**核心库**（严格标准）:
- 质量分: ≥80分
- 定位: 重点跟踪、深度研究、优先推荐
- 更新频率: 季度深度分析

**观察库**（潜力基金）:
- 质量分: 70-80分
- 定位: 持续观察、待提升空间
- 更新频率: 月度监控

**备选库**（后续扩展）:
- 曾进入前10%但目前退出
- 定位: 监控反弹机会
- 更新频率: 双周监控

### Step 7: 结果输出

**生成文件**:
| 文件名 | 内容 | 数量 |
|:---|:---|:---:|
| `fund_selected_v2.csv` | 全部入选基金 | 196只 |
| `fund_core_library_v2.csv` | 核心库 | 121只 |
| `fund_watch_library_v2.csv` | 观察库 | 75只 |

**字段规范**:
```
ts_code, name, category, return_3m, return_6m, return_1y, 
volatility, max_drawdown, sharpe, quality_score, 
percentile_1y, percentile_6m
```

---

## 三、关键指标说明

### 排名百分位解读
- `percentile_1y = 95` 表示该基金近1年业绩超过95%的同类基金（前5%）
- 数值越大越好
- 筛选阈值: 前10% → ≥90，前20% → ≥80

### 波动率计算
- 基于日净值收益率的年化标准差
- 计算方法: 对数收益率法
- 数据窗口: 近1年（约250个交易日）

### 质量评分逻辑
- 各指标先进行Z-score标准化（同类比较）
- 按权重加权求和
- 映射到0-100分区间

---

## 四、更新机制

### 更新频率
| 任务 | 频率 | 内容 |
|:---|:---:|:---|
| 净值数据更新 | 每日 | 更新所有基金净值 |
| 业绩排名计算 | 双周 | 重新计算6月/1年排名 |
| 候选筛选 | 月度 | 筛选进入前10%的基金 |
| 质量评分更新 | 月度 | 重新计算质量分 |
| 深度入库 | 季度 | 核心库基金深度研究 |

### 动态调整规则
**升入核心库**:
- 观察库基金质量分连续2个月≥80
- 近1年排名持续前10%

**降出核心库**:
- 核心库基金质量分连续2个月<80
- 近1年排名跌出前20%

**移出产品库**:
- 质量分连续3个月<70
- 近1年排名跌出前30%
- 触发一票否决项

---

## 五、注意事项

### 数据质量检查
- [ ] 确认净值数据完整性（无缺失月份）
- [ ] 验证排名计算正确性（百分位方向）
- [ ] 检查异常值（如单日净值波动>5%）

### 常见错误
1. **未去重直接筛选** → 导致同一基金多只入选
2. **排名百分位方向错误** → 把后10%当成前10%
3. **忽略类别差异** → 股票型和债券型用同一套标准
4. **质量分阈值过高** → 初期可适当降低至65分，逐步提升

### 待补充数据
- [ ] 基金经理任职时间（当前缺失）
- [ ] 基金规模数据（防止迷你基金）
- [ ] 机构持仓比例（流动性风险评估）

---

## 六、附录：代码模板

```python
import pandas as pd
import re

# 加载数据
df = pd.read_csv('fund_screening_all.csv')

# 去重
def get_base_name(name):
    base = re.sub(r'[A-Z]$', '', name)
    base = re.sub(r'(一年|三个月|六个月|两年|三年)持有$', '', base)
    base = re.sub(r'定期开放$', '', base)
    return base.strip()

df['base_name'] = df['name'].apply(get_base_name)
df_sorted = df.sort_values(['base_name', 'quality_score'], ascending=[True, False])
df_dedup = df_sorted.drop_duplicates(subset=['base_name'], keep='first')

# 筛选股票+混合型
target_types = ['主动股票型', '混合型-偏股', '混合型-平衡']
df_target = df_dedup[df_dedup['category'].isin(target_types)]

# 一级筛选
vol_90 = df_target.groupby('category')['volatility'].quantile(0.9)
df_target['vol_90_threshold'] = df_target['category'].map(vol_90)
df_target['high_vol'] = df_target['volatility'] > df_target['vol_90_threshold']

mask_1y = df_target['percentile_1y'] >= 90
mask_6m = df_target['percentile_6m'] >= 80
df_target['pass_level1'] = mask_1y & mask_6m & ~df_target['high_vol']
df_level1 = df_target[df_target['pass_level1']]

# 二级筛选
df_level1['pass_level2'] = df_level1['quality_score'] >= 70
df_level2 = df_level1[df_level1['pass_level2']]

# 分级
df_core = df_level2[df_level2['quality_score'] >= 80]
df_watch = df_level2[(df_level2['quality_score'] >= 70) & (df_level2['quality_score'] < 80)]

# 保存
df_core.to_csv('fund_core_library_v2.csv', index=False)
df_watch.to_csv('fund_watch_library_v2.csv', index=False)

print(f"核心库: {len(df_core)}只")
print(f"观察库: {len(df_watch)}只")
```

---

**执行记录**:
- 2026-03-10: v2.0版本，新增去重步骤，核心库121只，观察库75只
- 2026-03-08: v1.0版本，初始版本

**审核人**: _______________  
**执行人**: Kimi Claw
