#!/bin/bash
# World Monitor 本地启动脚本

echo "🌍 启动 World Monitor 本地情报仪表盘..."
echo ""
echo "访问地址: http://localhost:3456"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

cd "$(dirname "$0")"
python3 -m http.server 3456
