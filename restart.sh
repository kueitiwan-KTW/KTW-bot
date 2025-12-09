#!/bin/bash

# 重啟服務腳本（不開新視窗）

echo "🔄 重啟 KTW-bot 服務..."

# 1. 停止舊服務
echo "⏹️  停止舊服務..."
lsof -ti:5001 | xargs kill -9 2>/dev/null
lsof -ti:5002 | xargs kill -9 2>/dev/null

# 等待 Port 釋放
sleep 2

echo "✅ 舊服務已停止"

# 2. 在背景啟動新服務
echo "🚀 啟動新服務..."

# 啟動 LINE Bot
nohup python3 app.py > chat_logs/server.log 2>&1 &
BOT_PID=$!
echo "   🤖 Bot Server (PID: $BOT_PID) - Port 5001"

# 等待啟動
sleep 2

# 啟動管理後台
nohup python3 admin_dashboard.py > /dev/null 2>&1 &
ADMIN_PID=$!
echo "   🏨 Admin Dashboard (PID: $ADMIN_PID) - Port 5002"

# 等待啟動
sleep 2

# 3. 驗證服務
echo ""
echo "🔍 驗證服務狀態..."

if lsof -ti:5001 > /dev/null 2>&1; then
    echo "   ✅ Bot Server (Port 5001) 運行中"
else
    echo "   ❌ Bot Server 啟動失敗"
fi

if lsof -ti:5002 > /dev/null 2>&1; then
    echo "   ✅ Admin Dashboard (Port 5002) 運行中"
else
    echo "   ❌ Admin Dashboard 啟動失敗"
fi

echo ""
echo "✅ 重啟完成！"
echo ""
echo "📍 訪問網址："
echo "   • Bot Server: http://localhost:5001"
echo "   • 管理後台: http://localhost:5002"
echo ""
echo "📋 日誌位置："
echo "   • Bot: chat_logs/server.log"
echo ""
