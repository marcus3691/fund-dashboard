#!/bin/bash
# =============================================================================
# 基金经理共识信号报告定时任务配置脚本
# 
# 配置说明:
# - 周报: 每周一早上9:00发送
# - 日报: 每天晚上20:00发送
# =============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 路径配置
WORKSPACE_DIR="/root/.openclaw/workspace"
MONITOR_DIR="$WORKSPACE_DIR/fund_data/monitor"
LOG_DIR="$MONITOR_DIR/logs"
CRON_LOG="$LOG_DIR/cron.log"

# 创建日志目录
mkdir -p "$LOG_DIR"

echo -e "${GREEN}==============================================${NC}"
echo -e "${GREEN}  基金经理共识信号报告定时任务配置${NC}"
echo -e "${GREEN}==============================================${NC}"
echo ""

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到 python3${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Python3 已安装: $(python3 --version)"

# 检查脚本文件
if [ ! -f "$MONITOR_DIR/consensus_report_generator.py" ]; then
    echo -e "${RED}错误: consensus_report_generator.py 不存在${NC}"
    exit 1
fi

if [ ! -f "$MONITOR_DIR/consensus_email_sender.py" ]; then
    echo -e "${RED}错误: consensus_email_sender.py 不存在${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} 报告生成器脚本存在"
echo -e "${GREEN}✓${NC} 邮件发送器脚本存在"

# 创建定时任务脚本
DAILY_SCRIPT="$MONITOR_DIR/run_daily_report.sh"
WEEKLY_SCRIPT="$MONITOR_DIR/run_weekly_report.sh"

cat > "$DAILY_SCRIPT" << 'EOF'
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
echo "[$TIME] =========================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
EOF

cat > "$WEEKLY_SCRIPT" << 'EOF'
#!/bin/bash
# 周报自动生成和发送脚本
# 每周一早上9点执行

WORKSPACE_DIR="/root/.openclaw/workspace"
MONITOR_DIR="$WORKSPACE_DIR/fund_data/monitor"
LOG_DIR="$MONITOR_DIR/logs"
DATE=$(date +%Y%m%d)
TIME=$(date +%H:%M:%S)
LOG_FILE="$LOG_DIR/weekly_${DATE}.log"

echo "[$TIME] =========================================" >> "$LOG_FILE"
echo "[$TIME] 开始执行周报生成任务" >> "$LOG_FILE"

# 1. 先运行信号生成器
echo "[$TIME] 步骤1: 生成最新共识信号..." >> "$LOG_FILE"
cd "$MONITOR_DIR"
python3 consensus_signal_generator.py >> "$LOG_FILE" 2>&1

# 2. 生成周报
echo "[$TIME] 步骤2: 生成周报..." >> "$LOG_FILE"
python3 consensus_report_generator.py weekly >> "$LOG_FILE" 2>&1

# 3. 发送周报邮件
echo "[$TIME] 步骤3: 发送周报邮件..." >> "$LOG_FILE"
python3 consensus_email_sender.py weekly >> "$LOG_FILE" 2>&1

TIME=$(date +%H:%M:%S)
echo "[$TIME] 周报任务执行完成" >> "$LOG_FILE"
echo "[$TIME] =========================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
EOF

# 赋予执行权限
chmod +x "$DAILY_SCRIPT"
chmod +x "$WEEKLY_SCRIPT"

echo -e "${GREEN}✓${NC} 已创建定时任务脚本:"
echo "  - $DAILY_SCRIPT"
echo "  - $WEEKLY_SCRIPT"

echo ""
echo -e "${YELLOW}定时任务配置:${NC}"
echo ""

# 显示将要添加的crontab条目
echo -e "${YELLOW}将要添加以下crontab条目:${NC}"
echo ""
echo "# 基金经理共识信号报告定时任务"
echo "# 日报: 每天20:00"
echo "0 20 * * * $DAILY_SCRIPT >> $CRON_LOG 2>&1"
echo ""
echo "# 周报: 每周一09:00"
echo "0 9 * * 1 $WEEKLY_SCRIPT >> $CRON_LOG 2>&1"
echo ""

# 询问是否安装
read -p "是否安装到crontab? [Y/n]: " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
    # 创建临时crontab文件
    TEMP_CRON=$(mktemp)
    
    # 导出当前crontab (如果有)
    crontab -l 2>/dev/null > "$TEMP_CRON" || true
    
    # 检查是否已存在相关任务
    if grep -q "consensus_report" "$TEMP_CRON" 2>/dev/null; then
        echo -e "${YELLOW}⚠ 已存在共识报告任务，将移除旧任务...${NC}"
        # 移除旧任务
        grep -v "consensus_report\|run_daily_report\|run_weekly_report" "$TEMP_CRON" > "$TEMP_CRON.new" || true
        mv "$TEMP_CRON.new" "$TEMP_CRON"
    fi
    
    # 添加新任务
    echo "" >> "$TEMP_CRON"
    echo "# === 基金经理共识信号报告定时任务 ===" >> "$TEMP_CRON"
    echo "# 日报: 每天20:00" >> "$TEMP_CRON"
    echo "0 20 * * * $DAILY_SCRIPT >> $CRON_LOG 2>&1" >> "$TEMP_CRON"
    echo "# 周报: 每周一09:00" >> "$TEMP_CRON"
    echo "0 9 * * 1 $WEEKLY_SCRIPT >> $CRON_LOG 2>&1" >> "$TEMP_CRON"
    
    # 安装crontab
    crontab "$TEMP_CRON"
    rm -f "$TEMP_CRON"
    
    echo -e "${GREEN}✓${NC} 定时任务已安装!"
    echo ""
    echo -e "${GREEN}当前crontab内容:${NC}"
    crontab -l | grep -A 10 "基金经理共识信号"
else
    echo -e "${YELLOW}已取消安装${NC}"
    echo ""
    echo "您可以手动添加以下到crontab:"
    echo "  crontab -e"
    echo ""
    echo "添加内容:"
    echo "0 20 * * * $DAILY_SCRIPT >> $CRON_LOG 2>&1"
    echo "0 9 * * 1 $WEEKLY_SCRIPT >> $CRON_LOG 2>&1"
fi

echo ""
echo -e "${GREEN}==============================================${NC}"
echo -e "${GREEN}  配置完成!${NC}"
echo -e "${GREEN}==============================================${NC}"
echo ""
echo "使用方法:"
echo "  1. 手动生成日报: python3 $MONITOR_DIR/consensus_report_generator.py daily"
echo "  2. 手动发送日报: python3 $MONITOR_DIR/consensus_email_sender.py daily"
echo "  3. 查看日志:     tail -f $LOG_DIR/daily_*.log"
echo "  4. 测试邮件:     python3 $MONITOR_DIR/consensus_email_sender.py test"
echo ""
echo "定时任务:"
echo "  • 日报: 每天 20:00"
echo "  • 周报: 每周一 09:00"
echo ""
