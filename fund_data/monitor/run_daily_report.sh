#!/bin/bash
# 日报自动生成和发送脚本
# 每晚8点执行

WORKSPACE_DIR="/root/.openclaw/workspace"
MONITOR_DIR="$WORKSPACE_DIR/fund_data/monitor"
LOG_DIR="$MONITOR_DIR/logs"
DATE=$(date +%Y%m%d)
TIME=$(date +%H:%M:%S)
LOG_FILE="$LOG_DIR/daily_${DATE}.log"

echo "[$TIME] =========================================" >> "$LOG_FILE"
echo "[$TIME] 开始执行日报生成任务" >> "$LOG_FILE"

# 1. 先运行信号生成器
echo "[$TIME] 步骤1: 生成最新共识信号..." >> "$LOG_FILE"
cd "$MONITOR_DIR"
python3 consensus_signal_generator.py >> "$LOG_FILE" 2>&1

# 2. 生成日报
echo "[$TIME] 步骤2: 生成日报..." >> "$LOG_FILE"
python3 consensus_report_generator.py daily >> "$LOG_FILE" 2>&1

# 3. 发送日报邮件
echo "[$TIME] 步骤3: 发送日报邮件..." >> "$LOG_FILE"
python3 consensus_email_sender.py daily >> "$LOG_FILE" 2>&1

TIME=$(date +%H:%M:%S)
echo "[$TIME] 日报任务执行完成" >> "$LOG_FILE"

# 4. 推送到网站
echo "[$TIME] 步骤4: 推送到网站..." >> "$LOG_FILE"
bash "$MONITOR_DIR/push_reports_to_web.sh" >> "$LOG_FILE" 2>&1

echo "[$TIME] =========================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
