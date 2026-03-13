import tushare as ts
import pandas as pd
import json
import time
import re

# 设置 token
TS_TOKEN = '33996190080200cd63a01732ad443c390d9d580913ec938d4e1d704d'
pro = ts.pro_api(TS_TOKEN)

# 读取基金代码列表
with open('/root/.openclaw/workspace/fund_data/analysis/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 提取基金代码（唯一）
codes = list(set(re.findall(r'"(\d{6}\.OF)"', content)))
print(f'找到 {len(codes)} 只唯一基金')

# 尝试加载已有的经理数据
try:
    with open('/root/.openclaw/workspace/fund_data/analysis/fund_manager_data.json', 'r', encoding='utf-8') as f:
        manager_data = json.load(f)
    print(f'已加载现有数据: {len(manager_data)} 只基金')
except:
    manager_data = {}
    print('创建新的数据文件')

# 只处理尚未获取数据的基金
codes_to_fetch = [c for c in codes if c not in manager_data]
print(f'需要获取数据的基金: {len(codes_to_fetch)} 只')

# 获取基金经理数据
for i, code in enumerate(codes_to_fetch):
    try:
        df = pro.fund_manager(ts_code=code)
        if not df.empty:
            # 获取当前在任的基金经理（end_date 为 None）
            current = df[df['end_date'].isna()]
            if not current.empty:
                manager_name = current.iloc[0]['name']
                begin_date = current.iloc[0]['begin_date']
                manager_data[code] = {
                    'manager': manager_name,
                    'begin_date': begin_date
                }
            else:
                # 如果没有在任的，取最近一位
                df_sorted = df.sort_values('end_date', ascending=False)
                manager_name = df_sorted.iloc[0]['name']
                begin_date = df_sorted.iloc[0]['begin_date']
                end_date = df_sorted.iloc[0]['end_date']
                manager_data[code] = {
                    'manager': manager_name,
                    'begin_date': begin_date,
                    'end_date': end_date
                }
        else:
            manager_data[code] = {'manager': '未知', 'begin_date': ''}
        
        if (i + 1) % 10 == 0 or (i + 1) == len(codes_to_fetch):
            print(f'已处理 {i + 1}/{len(codes_to_fetch)} 只基金')
        time.sleep(0.15)  # 避免请求过快
        
    except Exception as e:
        print(f'获取 {code} 失败: {e}')
        manager_data[code] = {'manager': '未知', 'begin_date': ''}
        time.sleep(0.5)

# 保存数据
with open('/root/.openclaw/workspace/fund_data/analysis/fund_manager_data.json', 'w', encoding='utf-8') as f:
    json.dump(manager_data, f, ensure_ascii=False, indent=2)

print(f'\n完成！共获取 {len(manager_data)} 只基金的基金经理数据')

# 统计
known = [v for v in manager_data.values() if v.get('manager') != '未知']
print(f'已知经理: {len(known)} 只')
print(f'未知经理: {len(manager_data) - len(known)} 只')

print('\n前10条数据预览:')
for code, info in list(manager_data.items())[:10]:
    print(f'  {code}: {info}')
