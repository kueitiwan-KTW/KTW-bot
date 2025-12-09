#!/bin/bash

# 載入環境變數
source .env

# 定義清理函數
cleanup_services() {
    echo ""
    echo "⏹️  停止所有服務..."
    
    # 終止程序
    if [ -n "$BOT_PID" ] && kill -0 $BOT_PID 2>/dev/null; then
        kill $BOT_PID 2>/dev/null
    fi
    
    if [ -n "$ADMIN_PID" ] && kill -0 $ADMIN_PID 2>/dev/null; then
        kill $ADMIN_PID 2>/dev/null
    fi
    
    # 清理 Port
    lsof -ti:5001 2>/dev/null | xargs kill -9 2>/dev/null || true
    lsof -ti:5002 2>/dev/null | xargs kill -9 2>/dev/null || true
    
    echo "✅ 服務已停止"
}

# 定義啟動函數
start_services() {
    echo "==========================================="
    echo "🏨 LINE Bot 客服系統 + 管理後台"
    echo "==========================================="
    
    # 徹底清理所有舊程序和 Port
    echo "🧹 清理舊程序和 Port..."
    
    # 清理 Port 5001 和 5002
    echo "   🔍 檢查 Port 5001..."
    lsof -ti:5001 2>/dev/null | xargs kill -9 2>/dev/null || true
    echo "   🔍 檢查 Port 5002..."
    lsof -ti:5002 2>/dev/null | xargs kill -9 2>/dev/null || true
    lsof -ti:4040 2>/dev/null | xargs kill -9 2>/dev/null || true  # ngrok web interface
    
    # 清理 Python 程序
    echo "   🔍 終止舊的 Python 程序..."
    pkill -9 -f "python3.*app.py" 2>/dev/null || true
    pkill -9 -f "python3.*admin_dashboard.py" 2>/dev/null || true
    pkill -9 -f "python.*app.py" 2>/dev/null || true
    pkill -9 -f "python.*admin_dashboard.py" 2>/dev/null || true
    
    # 清理 ngrok 程序（包括在終端視窗中執行的）
    echo "   🔍 終止舊的 ngrok 程序..."
    pkill -9 -f "ngrok http" 2>/dev/null || true
    pkill -9 ngrok 2>/dev/null || true
    
    # 等待 Port 完全釋放
    echo "⏳ 等待 Port 釋放..."
    sleep 3
    
    # 驗證 Port 已釋放
    if lsof -ti:5001 &>/dev/null; then
        echo "   ⚠️  Port 5001 仍在使用中"
    else
        echo "   ✅ Port 5001 已釋放"
    fi
    
    if lsof -ti:5002 &>/dev/null; then
        echo "   ⚠️  Port 5002 仍在使用中"
    else
        echo "   ✅ Port 5002 已釋放"
    fi
    
    # 建立日誌目錄
    mkdir -p chat_logs
    
    echo "==========================================="
    echo "🚀 啟動服務..."
    echo "==========================================="
    
    # 啟動 LINE Bot（Port 5001）
    echo ""
    echo "🤖 啟動 LINE Bot (Port 5001)..."
    python3 app.py 2>&1 | tee -a chat_logs/server.log &
    BOT_PID=$!
    echo "   進程 ID: $BOT_PID"
    
    # 等待 Bot 啟動
    sleep 3
    
    # 啟動管理後台（Port 5002）
    echo ""
    echo "🏨 啟動管理後台 (Port 5002)..."
    python3 admin_dashboard.py 2>&1 &
    ADMIN_PID=$!
    echo "   進程 ID: $ADMIN_PID"
    
    # 等待管理後台啟動
    sleep 2
    
    # 嘗試啟動 ngrok（如果安裝了的話）
    echo ""
    if [ -f "./ngrok" ]; then
        echo "🌐 在新視窗啟動 ngrok 隧道..."
        osascript -e "tell application \"Terminal\" to do script \"cd '$PWD' && ./ngrok http 5001\""
        NGROK_PID="terminal"
        echo "   ✅ 已在新的終端視窗中開啟"
    elif command -v ngrok &> /dev/null; then
        echo "🌐 在新視窗啟動 ngrok 隧道..."
        osascript -e "tell application \"Terminal\" to do script \"cd '$PWD' && ngrok http 5001\""
        NGROK_PID="terminal"
        echo "   ✅ 已在新的終端視窗中開啟"
    else
        echo "⚠️  ngrok 未安裝，跳過（不影響本地使用）"
        NGROK_PID=""
    fi
    
    echo ""
    echo "==========================================="
    echo "✅ 服務啟動完成！"
    echo "==========================================="
    echo ""
    echo "📍 LINE Bot:       http://localhost:5001"
    echo "📍 管理後台:       http://localhost:5002"
    if [ -n "$NGROK_PID" ]; then
        echo "🌐 ngrok 網址:     請查看 ngrok 視窗"
    fi
    echo ""
    echo "📋 日誌檔案: chat_logs/server.log"
    echo ""
    echo "⏹️  按 Ctrl+C 停止所有服務"
    echo ""
}

# 設置中斷信號處理
trap cleanup_services INT TERM

# 主循環
while true; do
    # 啟動服務
    start_services
    
    # 等待程序結束或中斷信號
    wait $BOT_PID $ADMIN_PID 2>/dev/null
    
    # 服務已停止，詢問是否重啟
    echo ""
    echo "==========================================="
    echo "🔄 按 Enter 重新啟動，或按 Ctrl+C 退出"
    echo "==========================================="
    read -r
    
    echo ""
    echo "🔄 重新啟動服務..."
    echo ""
done
