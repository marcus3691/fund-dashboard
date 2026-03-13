#!/bin/bash
# 基金经理数据自动更新脚本
# 每周一早上8点执行

cd /root/.openclaw/workspace/fund_data/analysis

echo "=== 基金经理数据更新 $(date) ==="

# 1. 获取最新基金经理数据
echo "正在获取基金经理数据..."
python3 get_fund_managers.py > /tmp/fund_manager_update.log 2>&1

if [ $? -eq 0 ]; then
    echo "✓ 基金经理数据获取成功"
    cat /tmp/fund_manager_update.log
    
    # 2. 更新 index.html
    echo "正在更新网页..."
    python3 update_managers.py > /tmp/update_managers.log 2>&1
    
    if [ $? -eq 0 ]; then
        echo "✓ 网页更新成功"
        cat /tmp/update_managers.log
        
        # 3. 提交并推送
        git add index.html fund_manager_data.json
        git commit -m "Auto: 更新基金经理数据 $(date +%Y-%m-%d)"
        
        # 尝试推送（最多3次）
        for i in 1 2 3; do
            echo "尝试推送第 $i 次..."
            timeout 120 git push origin main
            if [ $? -eq 0 ]; then
                echo "✓ 推送成功"
                break
            else
                echo "✗ 推送失败，等待重试..."
                sleep 30
            fi
        done
        
    else
        echo "✗ 网页更新失败"
        cat /tmp/update_managers.log
    fi
else
    echo "✗ 基金经理数据获取失败"
    cat /tmp/fund_manager_update.log
fi

echo "=== 更新完成 $(date) ==="
