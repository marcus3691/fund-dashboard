#!/bin/bash
# =============================================================================
# 基金产品库报告全量推送脚本
# 每次生成报告后自动推送到GitHub Pages
# =============================================================================

set -e

WORKSPACE_DIR="/root/.openclaw/workspace"
MONITOR_DIR="$WORKSPACE_DIR/fund_data/monitor"
REPORTS_DIR="$MONITOR_DIR/reports"
WEB_DIR="$WORKSPACE_DIR/web_reports"
LOG_DIR="$MONITOR_DIR/logs"
DATE=$(date +%Y%m%d)
TIME=$(date +%H:%M:%S)
LOG_FILE="$LOG_DIR/push_${DATE}.log"

# 创建Web报告目录
mkdir -p "$WEB_DIR/daily"
mkdir -p "$WEB_DIR/weekly"
mkdir -p "$WEB_DIR/signals"
mkdir -p "$WEB_DIR/logs"

log() {
    echo "[$TIME] $1" | tee -a "$LOG_FILE"
}

log "========================================="
log "开始执行报告全量推送"
log "========================================="

# 1. 复制最新报告到Web目录
log "步骤1: 复制最新报告到Web目录..."

# 复制日报
if [ -f "$REPORTS_DIR/consensus_report_daily_${DATE}.html" ]; then
    cp "$REPORTS_DIR/consensus_report_daily_${DATE}.html" "$WEB_DIR/daily/"
    log "  ✅ 日报已复制: consensus_report_daily_${DATE}.html"
fi

# 复制周报（如果是周一）
if [ "$(date +%u)" -eq 1 ]; then
    if [ -f "$REPORTS_DIR/consensus_report_weekly_${DATE}.html" ]; then
        cp "$REPORTS_DIR/consensus_report_weekly_${DATE}.html" "$WEB_DIR/weekly/"
        log "  ✅ 周报已复制: consensus_report_weekly_${DATE}.html"
    fi
fi

# 复制信号数据
if [ -f "$MONITOR_DIR/manager_consensus_signals.json" ]; then
    cp "$MONITOR_DIR/manager_consensus_signals.json" "$WEB_DIR/signals/"
    log "  ✅ 信号数据已复制"
fi

# 2. 生成报告索引页面
log "步骤2: 生成报告索引页面..."

cat > "$WEB_DIR/index.html" << 'EOF'
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>基金产品库报告中心</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif; 
            background: #0d1117; 
            color: #c9d1d9; 
            line-height: 1.6; 
        }
        .navbar { 
            background: #161b22; 
            padding: 15px 30px; 
            border-bottom: 1px solid #30363d; 
            position: sticky; 
            top: 0; 
            z-index: 100; 
        }
        .navbar h1 { font-size: 18px; color: #58a6ff; }
        .nav-links { margin-top: 10px; }
        .nav-links a { 
            color: #8b949e; 
            text-decoration: none; 
            margin-right: 20px; 
            font-size: 14px; 
        }
        .nav-links a:hover { color: #58a6ff; }
        .container { max-width: 1200px; margin: 0 auto; padding: 30px; }
        .section { margin-bottom: 40px; }
        .section h2 { 
            font-size: 20px; 
            color: #e6edf3; 
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #30363d;
        }
        .report-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 15px;
        }
        .report-card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 20px;
            transition: all 0.3s;
        }
        .report-card:hover {
            border-color: #58a6ff;
            transform: translateY(-2px);
        }
        .report-card .date {
            font-size: 12px;
            color: #8b949e;
            margin-bottom: 8px;
        }
        .report-card .title {
            font-size: 16px;
            color: #e6edf3;
            margin-bottom: 10px;
        }
        .report-card .type {
            display: inline-block;
            background: #238636;
            color: white;
            font-size: 11px;
            padding: 2px 8px;
            border-radius: 10px;
            margin-right: 5px;
        }
        .report-card .type.weekly {
            background: #1f6feb;
        }
        .report-card a {
            color: #58a6ff;
            text-decoration: none;
            font-size: 14px;
        }
        .report-card a:hover {
            text-decoration: underline;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
        }
        .stat-card .value {
            font-size: 32px;
            font-weight: 600;
            color: #58a6ff;
            margin: 10px 0;
        }
        .stat-card .label {
            font-size: 12px;
            color: #8b949e;
        }
        .empty-state {
            text-align: center;
            padding: 40px;
            color: #8b949e;
        }
        @media (max-width: 768px) {
            .stats-grid { grid-template-columns: repeat(2, 1fr); }
            .report-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="navbar">
        <h1>📊 基金产品库报告中心</h1>
        <div class="nav-links">
            <a href="https://marcus3691.github.io/fund-dashboard">← 返回产品库</a>
            <a href="#daily">日报</a>
            <a href="#weekly">周报</a>
            <a href="#signals">信号数据</a>
        </div>
    </div>
    
    <div class="container">
        <div class="stats-grid">
            <div class="stat-card">
                <div class="value" id="daily-count">-</div>
                <div class="label">日报数量</div>
            </div>
            <div class="stat-card">
                <div class="value" id="weekly-count">-</div>
                <div class="label">周报数量</div>
            </div>
            <div class="stat-card">
                <div class="value" id="signal-count">-</div>
                <div class="label">信号更新</div>
            </div>
            <div class="stat-card">
                <div class="value" id="last-update">-</div>
                <div class="label">最后更新</div>
            </div>
        </div>
        
        <div class="section" id="daily">
            <h2>📈 基金经理共识日报</h2>
            <div class="report-grid" id="daily-list">
                <!-- 日报列表由JavaScript动态生成 -->
            </div>
        </div>
        
        <div class="section" id="weekly">
            <h2>📊 基金经理共识周报</h2>
            <div class="report-grid" id="weekly-list">
                <!-- 周报列表由JavaScript动态生成 -->
            </div>
        </div>
        
        <div class="section" id="signals">
            <h2>🎯 共识信号数据</h2>
            <div class="report-grid" id="signal-list">
                <!-- 信号数据列表 -->
            </div>
        </div>
    </div>
    
    <script>
        // 动态加载报告列表
        async function loadReports() {
            // 这里可以添加从服务器获取报告列表的逻辑
            // 目前使用静态示例
            const dailyReports = [];
            const weeklyReports = [];
            
            // 生成最近30天的日报列表
            for (let i = 0; i < 30; i++) {
                const date = new Date();
                date.setDate(date.getDate() - i);
                const dateStr = date.toISOString().slice(0, 10).replace(/-/g, '');
                dailyReports.push({
                    date: date.toISOString().slice(0, 10),
                    file: `daily/consensus_report_daily_${dateStr}.html`,
                    title: `基金经理共识日报 - ${date.toISOString().slice(0, 10)}`
                });
            }
            
            // 生成最近10周的周报列表
            for (let i = 0; i < 10; i++) {
                const date = new Date();
                date.setDate(date.getDate() - i * 7);
                const dateStr = date.toISOString().slice(0, 10).replace(/-/g, '');
                weeklyReports.push({
                    date: date.toISOString().slice(0, 10),
                    file: `weekly/consensus_report_weekly_${dateStr}.html`,
                    title: `基金经理共识周报 - 第${getWeekNumber(date)}周`
                });
            }
            
            // 更新统计
            document.getElementById('daily-count').textContent = dailyReports.length;
            document.getElementById('weekly-count').textContent = weeklyReports.length;
            document.getElementById('signal-count').textContent = '实时';
            document.getElementById('last-update').textContent = new Date().toLocaleDateString('zh-CN');
            
            // 渲染日报列表
            const dailyList = document.getElementById('daily-list');
            dailyReports.slice(0, 10).forEach(report => {
                dailyList.innerHTML += `
                    <div class="report-card">
                        <div class="date">${report.date}</div>
                        <div class="title">${report.title}</div>
                        <span class="type">日报</span>
                        <a href="${report.file}" target="_blank">查看报告 →</a>
                    </div>
                `;
            });
            
            // 渲染周报列表
            const weeklyList = document.getElementById('weekly-list');
            weeklyReports.slice(0, 5).forEach(report => {
                weeklyList.innerHTML += `
                    <div class="report-card">
                        <div class="date">${report.date}</div>
                        <div class="title">${report.title}</div>
                        <span class="type weekly">周报</span>
                        <a href="${report.file}" target="_blank">查看报告 →</a>
                    </div>
                `;
            });
            
            // 渲染信号数据
            const signalList = document.getElementById('signal-list');
            signalList.innerHTML += `
                <div class="report-card">
                    <div class="date">实时更新</div>
                    <div class="title">基金经理共识信号数据</div>
                    <span class="type">JSON</span>
                    <a href="signals/manager_consensus_signals.json" target="_blank">查看数据 →</a>
                </div>
            `;
        }
        
        function getWeekNumber(date) {
            const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
            const dayNum = d.getUTCDay() || 7;
            d.setUTCDate(d.getUTCDate() + 4 - dayNum);
            const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
            return Math.ceil((((d - yearStart) / 86400000) + 1) / 7);
        }
        
        loadReports();
    </script>
</body>
</html>
EOF

log "  ✅ 报告索引页面已生成"

# 3. 复制Web目录到Git仓库
cp -r "$WEB_DIR"/* "$WORKSPACE_DIR/"
log "  ✅ Web文件已复制到Git仓库"

# 4. Git提交和推送
log "步骤3: Git提交和推送..."
cd "$WORKSPACE_DIR"

# 检查是否有变更
if git diff --quiet HEAD -- . 2>/dev/null; then
    log "  ℹ️ 无变更需要提交"
else
    git add -A
    git commit -m "自动推送: 基金产品库报告更新 - $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE" 2>&1
    
    # 尝试推送（带重试）
    for i in 1 2 3; do
        if timeout 120 git push origin master >> "$LOG_FILE" 2>&1; then
            log "  ✅ Git推送成功"
            break
        else
            log "  ⚠️ 推送失败，第${i}次重试..."
            sleep 10
        fi
    done
fi

log "========================================="
log "报告全量推送完成"
log "========================================="
log ""
