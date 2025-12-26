# KTW-Bot 日誌系統指南

> 查詢 LOG 檔案以診斷系統問題

---

## 📁 日誌位置總覽

| LOG 類型 | 位置 | 保留期 | 用途 |
|:---------|:-----|:------:|:-----|
| 對話記錄 | `data/chat_logs/{user_id}.txt` | 永久 | 查看客人對話 |
| Bot 內部 | `data/bot_logs/bot_YYYY-MM-DD.log` | 7 天 | Bot 運作追蹤 |
| API 調用 (Bot端) | `data/api_logs/pms_api_YYYY-MM-DD.log` | 永久 | 診斷網路問題 |
| API 伺服器 | `C:/ktw-bot/pms-api/logs/pms_api_YYYY-MM-DD.log` | 3 天 | Oracle 錯誤診斷 |

---

## 🔍 查詢指令

### 1. 查看客人對話記錄
```bash
# 本地查看
cat data/chat_logs/{user_id}.txt

# 範例：查看林宛錡的對話
cat data/chat_logs/U45320f69f3cc6321287e6cfb469bcbbb.txt
```

### 2. 查看 Bot 內部運作 LOG
```bash
# 今日 LOG
cat data/bot_logs/bot_$(date +%Y-%m-%d).log

# 搜尋特定訂單
grep "1671721966" data/bot_logs/bot_*.log
```

### 3. 查看 API 調用 LOG (Bot 端)
```bash
# 今日 LOG
cat data/api_logs/pms_api_$(date +%Y-%m-%d).log

# 搜尋 Timeout 錯誤
grep "TIMEOUT" data/api_logs/pms_api_*.log

# 搜尋 404 錯誤
grep "status=404" data/api_logs/pms_api_*.log
```

### 4. 查看 PMS API 伺服器 LOG (遠端)
```bash
# SSH 連線查看今日 LOG
ssh Administrator@192.168.8.3 "type C:\\ktw-bot\\pms-api\\logs\\pms_api_2025-12-21.log"

# 搜尋 Oracle 錯誤
ssh Administrator@192.168.8.3 "findstr \"ERROR\" C:\\ktw-bot\\pms-api\\logs\\pms_api_2025-12-21.log"
```

---

## 🚨 常見問題診斷

### 問題：客人查訂單說「查不到」

**步驟 1**：查 Bot 端 API LOG
```bash
grep "order_id=客人提供的編號" data/api_logs/pms_api_*.log
```

**可能看到的錯誤**：
| LOG 內容 | 問題原因 | 解決方案 |
|:---------|:---------|:---------|
| `type=TIMEOUT` | 網路逾時 | 檢查網路 / 增加 timeout |
| `type=CONNECTION` | API 沒運行 | 重啟 PMS API 服務 |
| `status=404` | 訂單不存在 | 確認訂單是否在 PMS |
| `status=500` | Oracle 錯誤 | 查遠端 API LOG |

**步驟 2**：查 PMS API 伺服器 LOG
```bash
ssh Administrator@192.168.8.3 "type C:\\ktw-bot\\pms-api\\logs\\pms_api_$(date +%Y-%m-%d).log"
```

---

## 📋 LOG 格式說明

### Bot 內部 LOG
```
10:13:58 | RECEIVE | user=U45320... | type=text | content="我要查訂單"
10:13:58 | INTENT | detected=order_query | confidence=0.95
10:13:58 | TOOL_CALL | tool=check_order_status | params={order_id=1671721966}
10:13:58 | TOOL_RESULT | tool=check_order_status | status=success
10:13:58 | RESPONSE | user=U45320... | text="您的訂單已找到..."
10:13:58 | ERROR | type=GEMINI_API | message=...
```

### API 調用 LOG (Bot 端)
```
10:13:58 | PMS_QUERY_START | user=U45320... | order_id=1671721966
10:13:58 | PMS_REQUEST | method=GET | url=http://192.168.8.3:3000/api/bookings/1671721966
10:13:58 | PMS_RESPONSE | status=200 | elapsed=0.02s | result=found
10:13:58 | PMS_ERROR | type=TIMEOUT | order_id=... | error=...
```

### PMS API 伺服器 LOG
```
10:24:58 | REQUEST | GET /bookings/1671721966
10:24:58 | ORACLE | FIND_ORDER | elapsed=5ms | rows=1
10:24:58 | RESPONSE | GET /bookings/1671721966 | status=200 | elapsed=60ms
10:24:58 | ERROR | ORACLE_QUERY_BOOKING | code=ORA-01034 | message=ORACLE not available
```

---

*最後更新：2025-12-21*
