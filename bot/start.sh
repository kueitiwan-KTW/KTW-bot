#!/bin/bash

# Bot 啟動腳本
# 使用方式：./start.sh

# 切換到 bot 目錄
cd "$(dirname "$0")"

# 載入環境變數
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

# 啟動 Bot
echo "🤖 KTW Bot 啟動中..."
python app.py
