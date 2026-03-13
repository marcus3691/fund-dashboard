import json
import re

# 读取基金经理数据
with open('/root/.openclaw/workspace/fund_data/analysis/fund_manager_data.json', 'r', encoding='utf-8') as f:
    manager_data = json.load(f)

# 读取 index.html
with open('/root/.openclaw/workspace/fund_data/analysis/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

print(f'读取到 {len(manager_data)} 条基金经理数据')
print(f'index.html 大小: {len(content)} 字符')

# 统计更新情况
updated_count = 0
unknown_count = 0

for code, info in manager_data.items():
    manager_name = info.get('manager', '未知')
    
    # 先移除可能存在的重复 manager 字段
    # 匹配模式: "manager": "...",
    pattern_remove = f'"{code}": {{"name": "([^"]+)", "code": "{code}", "manager": "[^"]*"(?:, "manager": "[^"]*")*'
    
    # 检查是否存在该基金的定义
    if f'"{code}": {{"name":' in content:
        # 移除所有现有的 manager 字段，然后添加正确的
        # 使用更精确的模式：找到完整的基金对象并替换
        
        # 方法：查找该基金对象的文本，替换其中的 manager 字段
        # 先找到该基金定义的开始位置
        fund_start = f'"{code}": {{"name": "'
        if fund_start in content:
            # 构建替换模式：将 "manager": "..." 替换为 "manager": "正确名字"
            # 需要处理可能没有 manager 字段的情况
            
            # 尝试替换已有的 manager 字段
            old_pattern = f'("{code}": {{"name": "[^"]+", "code": "{code}", )(?!"manager")'
            new_pattern = f'\\1"manager": "{manager_name}", '
            
            # 先检查是否已经有 manager 字段
            if f'"{code}": {{"name": "' in content and f'"code": "{code}", "manager"' in content:
                # 替换现有的 manager 值
                content = re.sub(
                    f'"{code}": {{"name": "([^"]+)", "code": "{code}", "manager": "[^"]*"',
                    f'"{code}": {{"name": "\\1", "code": "{code}", "manager": "{manager_name}"',
                    content
                )
            elif f'"{code}": {{"name": "' in content:
                # 在 code 后面添加 manager 字段
                content = re.sub(
                    f'"{code}": {{"name": "([^"]+)", "code": "{code}"(?!,)',
                    f'"{code}": {{"name": "\\1", "code": "{code}", "manager": "{manager_name}"',
                    content
                )
                content = re.sub(
                    f'"{code}": {{"name": "([^"]+)", "code": "{code}", (?!"manager")',
                    f'"{code}": {{"name": "\\1", "code": "{code}", "manager": "{manager_name}", ',
                    content
                )
            
            if manager_name != '未知':
                updated_count += 1
            else:
                unknown_count += 1

print(f'已更新基金数据:')
print(f'  - 已知经理: {updated_count} 只')
print(f'  - 未知经理: {unknown_count} 只')

# 保存更新后的文件
with open('/root/.openclaw/workspace/fund_data/analysis/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('已保存更新后的 index.html')

# 验证更新
with open('/root/.openclaw/workspace/fund_data/analysis/index.html', 'r', encoding='utf-8') as f:
    updated = f.read()
    
# 检查是否有 manager 字段
manager_count = updated.count('"manager":')
print(f'验证: 找到 {manager_count} 个 manager 字段')

# 统计已知经理数量
known_managers = updated.count('"manager": "') - updated.count('"manager": "未知"')
print(f'其中已知经理: {known_managers} 个')

# 显示前5个示例
matches = re.findall(r'"\d{6}\.OF": {"name": "([^"]+)", "code": "\d{6}\.OF", "manager": "([^"]+)"', updated)
print(f'\n前5个示例:')
for name, manager in matches[:5]:
    print(f'  {name}: {manager}')
