#!/bin/bash

# 取得目前腳本所在的目錄
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==========================================="
echo "🚀 啟動 KTW 飯店系統 V2 (Hybrid Stack)"
echo "==========================================="

# 定義清理函數
cleanup_services() {
    echo ""
    echo "⏹️  停止所有服務..."
    
    # 終止 Python 程序
    pkill -9 -f "python3.*app.py" 2>/dev/null || true
    pkill -9 -f "python3.*admin_dashboard.py" 2>/dev/null || true
    
    # 終止 Node 程序
    pkill -f "node.*src/index.js" 2>/dev/null || true
    pkill -f "vite" 2>/dev/null || true
    
    # 清理 Port
    lsof -ti:5001 2>/dev/null | xargs kill -9 2>/dev/null || true
    lsof -ti:5002 2>/dev/null | xargs kill -9 2>/dev/null || true
    lsof -ti:3000 2>/dev/null | xargs kill -9 2>/dev/null || true
    
    # 清理 Ngrok
    pkill -9 ngrok 2>/dev/null || true
    
    echo "✅ 服務已停止"
}

# 執行清理
cleanup_services

echo "🧹 清理完成，準備啟動..."
sleep 2

# 1. 啟動 Python LINE Bot (Port 5001)
echo "🤖 啟動 LINE Bot (Port 5001)..."
osascript -e "tell application \"Terminal\" to do script \"cd '$PROJECT_DIR' && source .venv/bin/activate && python3 app.py\""

# 2. 啟動 Node.js Core (Port 3000)
echo "🧠 啟動 KTW Backend Core (Port 3000)..."
osascript -e "tell application \"Terminal\" to do script \"cd '$PROJECT_DIR/KTW-backend' && npm run dev\""

# 3. 啟動 Vue.js Admin (Port 5002)
echo "🖥️ 啟動 KTW Admin Web (Port 5002)..."
osascript -e "tell application \"Terminal\" to do script \"cd '$PROJECT_DIR/KTW-admin-web' && npm run dev\""

# 4. 啟動 Ngrok (Port 5001)
if [ -f "./ngrok" ]; then
    echo "🌐 啟動 Ngrok..."
    osascript -e "tell application \"Terminal\" to do script \"cd '$PROJECT_DIR' && ./ngrok http 5001\""
elif command -v ngrok &> /dev/null; then
    echo "🌐 啟動 Ngrok..."
    osascript -e "tell application \"Terminal\" to do script \"cd '$PROJECT_DIR' && ngrok http 5001\""
fi

echo ""
echo "==========================================="
echo "✅ 所有服務已在獨立視窗啟動！"
echo "==========================================="
echo "📍 LINE Bot:       http://localhost:5001"
echo "📍 Node Core:      http://localhost:3000"
echo "📍 Admin Web:      http://localhost:5002"
echo "==========================================="
