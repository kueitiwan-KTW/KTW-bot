#!/bin/bash

# 取得目前腳本所在的目錄
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "正在啟動服務..."
echo "專案路徑: $PROJECT_DIR"

# 開啟一個新視窗執行 Flask Server
osascript -e "tell application \"Terminal\" to do script \"cd '$PROJECT_DIR' && ./run_dev.sh\""

# 開啟一個新視窗執行 ngrok
osascript -e "tell application \"Terminal\" to do script \"cd '$PROJECT_DIR' && ./ngrok http 5001\""

echo "✅ 成功！已開啟兩個新視窗分別執行 Server 和 ngrok。"
