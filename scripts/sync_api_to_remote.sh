#!/bin/bash
# 同步 API 修改到遠端伺服器 (Windows Server)

echo "🔄 開始同步 pms-api 到遠端伺服器..."

# Windows Server 路徑
REMOTE_USER="Administrator"
REMOTE_HOST="192.168.8.3"
REMOTE_PATH="C:/pms-api/routes/bookings.js"

# 複製修改的 bookings.js
echo "📤 上傳 bookings.js..."
scp pms-api/routes/bookings.js ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}

if [ $? -eq 0 ]; then
    echo "✅ 檔案上傳成功"
    
    # 重啟遠端 API (Windows Service)
    echo "🔄 重啟遠端 PMS-API..."
    ssh ${REMOTE_USER}@${REMOTE_HOST} "Restart-Service pms-api"
    
    if [ $? -eq 0 ]; then
        echo "✅ API 已重啟"
        echo ""
        echo "🎉 同步完成！"
    else
        echo "❌ API 重啟失敗"
        exit 1
    fi
else
    echo "❌ 檔案上傳失敗"
    exit 1
fi
