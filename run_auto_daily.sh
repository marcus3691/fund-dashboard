#!/bin/bash
# =============================================================================
# 基金数据自动更新定时任务脚本
# 本地执行 + 飞书推送
# =============================================================================

set -e

WORKSPACE_DIR="/root/.openclaw/workspace"
LOG_DIR="$WORKSPACE_DIR/logs"
DATE=$(date +%Y%m%d)
TIME=$(date +%H:%M:%S)
LOG_FILE="$LOG_DIR/auto_daily_${DATE}.log"

# 创建日志目录
mkdir -p "$LOG_DIR"

echo "[$TIME] =========================================" | tee -a "$LOG_FILE"
echo "[$TIME] 基金数据自动更新任务开始" | tee -a "$LOG_FILE"
echo "[$TIME] =========================================" | tee -a "$LOG_FILE"

# 1. 运行自动更新脚本
echo "[$TIME] 执行数据更新和策略分析..." | tee -a "$LOG_FILE"
cd "$WORKSPACE_DIR"

# 捕获输出
NOTIFICATION=$(python3 fund_auto_runner.py 2>>"$LOG_FILE" || echo "执行失败")

# 保存通知内容
echo "$NOTIFICATION" > "$WORKSPACE_DIR/last_notification.txt"

TIME=$(date +%H:%M:%S)
echo "[$TIME] 数据更新完成" | tee -a "$LOG_FILE"

# 2. 发送飞书通知（通过OpenClaw消息工具）
echo "[$TIME] 发送飞书通知..." | tee -a "$LOG_FILE"

# 检查通知内容是否存在
if [ -f "$WORKSPACE_DIR/last_notification.txt" ]; then
    # 发送消息标记（OpenClaw会监控这个文件）
    touch "$WORKSPACE_DIR/notify_feishu.flag"
    echo "[$TIME] 飞书通知标记已创建" | tee -a "$LOG_FILE"
fi

TIME=$(date +%H:%M:%S)
echo "[$TIME] =========================================" | tee -a "$LOG_FILE"
echo "[$TIME] 任务执行完成" | tee -a "$LOG_FILE"
echo "[$TIME] =========================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
