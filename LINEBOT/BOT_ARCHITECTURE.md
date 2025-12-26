# LINE Bot 完整架構圖（詳細版）

> 最後更新：2025-12-22

---

## 一、系統總覽

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              LINE Platform                                  │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │ Webhook POST /callback
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         app.py (Flask 入口)                                 │
│  ├── callback()           # 接收 Webhook，驗證簽名                         │
│  ├── handle_message()     # 處理文字訊息                                   │
│  ├── handle_image()       # 處理圖片訊息                                   │
│  ├── handle_audio_message() # 處理語音訊息                                 │
│  ├── handle_sticker()     # 處理貼圖訊息                                   │
│  └── push_notification()  # 推送到 Admin Dashboard                         │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │ 調用 bot.generate_response()
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         bot.py (主控制器 1821 行)                           │
│                                                                             │
│  【初始化 & 設定】                                                          │
│  ├── __init__()           # 初始化 Gemini、載入知識庫、註冊工具             │
│  ├── _load_json()         # 載入 JSON 檔案                                  │
│  └── _load_text()         # 載入文字檔案                                    │
│                                                                             │
│  【Gemini Function Calling 工具】                                           │
│  ├── check_order_status() # 查詢訂單狀態（核心工具）                       │
│  ├── update_guest_info()  # 更新客人資訊（電話/抵達時間/需求）             │
│  ├── check_today_availability() # 查詢今日可預訂房型                       │
│  ├── create_same_day_booking()  # 建立當日預訂                             │
│  ├── get_weather_forecast()     # 查詢特定日期天氣                         │
│  └── get_weekly_forecast()      # 查詢週末天氣預報                         │
│                                                                             │
│  【訊息處理】                                                               │
│  ├── generate_response()  # 主要入口，路由判斷                             │
│  ├── handle_image()       # 處理圖片（OCR 辨識訂單）                       │
│  ├── handle_audio()       # 處理語音（轉文字）                             │
│  └── get_user_session()   # 取得 Gemini 對話 Session                       │
│                                                                             │
│  【意圖判斷 & 路由】                                                        │
│  ├── _is_booking_intent_without_order()  # 偵測訂房意圖                    │
│  ├── _has_order_number()                 # 偵測訂單編號                    │
│  └── _get_recent_conversation_summary()  # 對話摘要                        │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              ▼                     ▼                     ▼
┌──────────────────────┐ ┌──────────────────────┐ ┌──────────────────────┐
│   訂單查詢流程       │ │   當日預訂流程       │ │   VIP 內部功能       │
│ order_query_handler  │ │ same_day_booking     │ │ vip_service_handler  │
│      (605 行)        │ │     (1550 行)        │ │      (~450 行)       │
└──────────────────────┘ └──────────────────────┘ └──────────────────────┘
```

---

## 二、核心模組詳細說明

### 2.1 app.py (Flask 入口，218 行)

| 函數 | 行號 | 用途 |
|:-----|:----:|:-----|
| `callback()` | 56-72 | 接收 LINE Webhook，驗證簽名 |
| `handle_message()` | 74-138 | 處理文字訊息，調用 bot.generate_response() |
| `handle_image()` | 140-161 | 處理圖片訊息，調用 bot.handle_image() |
| `handle_audio_message()` | 163-184 | 處理語音訊息，調用 bot.handle_audio() |
| `handle_sticker()` | 186-213 | 處理貼圖訊息，回應 LINE 官方貼圖 |
| `push_notification()` | 41-54 | 推送新訊息通知到 Admin Dashboard |

---

### 2.2 bot.py (主控制器，1821 行，21 個函數)

#### 【Gemini Function Calling 工具】

| 工具名稱 | 行號 | 用途 | 參數 |
|:---------|:----:|:-----|:-----|
| `check_order_status` | 552-1072 | 查詢訂單狀態 | order_id, guest_name?, phone?, user_confirmed? |
| `update_guest_info` | 1075-1116 | 更新客人資訊 | order_id, info_type, content |
| `check_today_availability` | 1122-1178 | 查詢今日可預訂房型 | (無) |
| `create_same_day_booking` | 1180-1344 | 建立當日預訂 | rooms, guest_name, phone, arrival_time, bed_type?, special_requests? |
| `get_weather_forecast` | 1346-1352 | 查詢特定日期天氣 | date_str |
| `get_weekly_forecast` | 1354-1360 | 查詢週末天氣預報 | (無) |

#### 【訊息處理】

| 函數 | 行號 | 用途 |
|:-----|:----:|:-----|
| `generate_response()` | 1584-1742 | 主入口，路由至各 Handler 或 Gemini AI |
| `handle_image()` | 1362-1430 | 圖片 OCR，辨識訂單截圖 |
| `handle_audio()` | 1744-1792 | 語音轉文字，送入 generate_response() |
| `get_user_session()` | 1503-1531 | 取得或建立 Gemini 對話 Session |
| `reset_conversation()` | 1533-1547 | 重置用戶對話 |

#### 【路由邏輯】 (generate_response 內 L1600-1650)

```python
# 1. 檢查是否有訂單編號 → order_query_handler
if self.order_query_handler.is_active(user_id) or has_order:
    order_response = self.order_query_handler.handle_message(...)

# 2. 檢查是否在預訂流程中 → same_day_booking
if self.state_machine.get_active_handler_type(user_id) == 'same_day_booking':
    booking_response = self.same_day_handler.handle_message(...)

# 3. 檢查是否為 VIP → vip_service_handler
if self.vip_service and self.vip_service.is_internal(user_id):
    vip_response = self.vip_service.handle_message(...)

# 4. 其他 → Gemini AI 處理
response = chat_session.send_message(...)
```

---

### 2.3 handlers/conversation_state_machine.py (狀態機，347 行，19 個函數)

#### 【狀態常數】

```python
STATE_IDLE = 'idle'                                    # 閒置
STATE_ORDER_QUERY_CONFIRMING = 'order_query.confirming'  # 訂單確認中
STATE_ORDER_QUERY_COLLECTING_PHONE = 'order_query.collecting_phone'  # 收集電話
STATE_ORDER_QUERY_COLLECTING_ARRIVAL = 'order_query.collecting_arrival'  # 收集抵達時間
STATE_ORDER_QUERY_COLLECTING_REQUESTS = 'order_query.collecting_requests'  # 收集需求
STATE_BOOKING_SHOW_ROOMS = 'booking.show_rooms'        # 顯示房型
STATE_BOOKING_COLLECT_COUNT = 'booking.collect_count'  # 收集數量
STATE_BOOKING_COLLECT_BED = 'booking.collect_bed'      # 收集床型
STATE_BOOKING_COLLECT_REQUESTS = 'booking.collect_requests'  # 收集需求
STATE_BOOKING_COLLECT_INFO = 'booking.collect_info'    # 收集資訊
STATE_BOOKING_CONFIRM = 'booking.confirm'              # 確認預訂
```

#### 【核心函數】

| 函數 | 用途 |
|:-----|:-----|
| `get_session(user_id)` | 取得或建立用戶 session（先查 SQLite） |
| `transition(user_id, target_state, data)` | 狀態轉換（含 SQLite 同步） |
| `get_state(user_id)` | 取得當前狀態 |
| `get_active_handler_type(user_id)` | 根據狀態返回 Handler 類型 |
| `set_pending_intent(user_id, intent)` | 設定跨流程待處理意圖 |
| `execute_pending_intent(user_id)` | 執行待處理意圖（流程結束後跳轉） |
| `reset_session(user_id)` | 重置 session（含 SQLite 刪除） |

#### 【SQLite 持久化】

| 函數 | 用途 |
|:-----|:-----|
| `_load_from_backend(user_id)` | 從 ktw-backend API 載入 session |
| `_sync_to_backend(user_id)` | 同步 session 到 ktw-backend API |
| `_delete_from_backend(user_id)` | 從 ktw-backend 刪除 session |

---

### 2.4 handlers/order_query_handler.py (訂單查詢，605 行，28 個函數)

#### 【主要流程】

```
用戶提供訂單編號
    ↓
_extract_order_number() → 提取訂單編號
    ↓
_query_order() → 查詢 PMS API / Gmail API
    ├── _query_pms() → PMS 查詢
    └── _query_gmail() → Gmail 查詢
    ↓
_format_order_details() → 格式化訂單資訊
    ↓
「請問是這筆訂單嗎？」
    ↓
_handle_order_confirmation() → 處理確認
    ↓ (確認後)
_start_collecting_info() → 開始收集資訊
    ↓
_handle_phone_collection() → 收集電話
    ↓
_handle_arrival_collection() → 收集抵達時間
    ↓
_handle_special_requests() → 收集特殊需求
    ↓
_complete_collection() → 完成，儲存資料
    └── _save_to_guest_orders() → 儲存到 JSON + SQLite
```

#### 【核心函數】

| 函數 | 行號 | 用途 |
|:-----|:----:|:-----|
| `handle_message()` | 61-95 | 主入口，根據狀態分發 |
| `_query_order()` | 120-177 | 查詢訂單（PMS + Gmail） |
| `_query_pms()` | 179-237 | 查詢 PMS API |
| `_query_gmail()` | 239-248 | 查詢 Gmail API |
| `_format_order_details()` | 272-329 | 格式化訂單顯示 |
| `_handle_order_confirmation()` | 331-354 | 處理訂單確認 |
| `_save_to_guest_orders()` | 534-562 | 儲存資料（sync_order_details） |

---

### 2.5 handlers/same_day_booking.py (當日預訂，1550 行，35 個函數)

#### 【主要流程】

```
用戶說「今天訂房」
    ↓
is_booking_intent() → 偵測訂房意圖
    ↓
is_within_booking_hours() → 檢查時間（22:00 前）
    ↓
_start_booking() → 查詢房況 API
    ↓
顯示房型列表
    ↓
_handle_room_selection() → 處理房型選擇
    ├── 單一房型 → _handle_count_collection()
    └── 多房型 → _parse_multi_room_input() → _check_multi_room_availability()
    ↓
_handle_bed_selection() 或 _handle_multi_bed_select() → 床型選擇
    ↓
_handle_requests_collection() → 收集特殊需求
    ↓
_handle_info_collection() → 收集姓名/電話/抵達時間
    ↓
_handle_confirmation() → 確認預訂
    ↓
_create_booking() → 建立預訂
    ├── _create_single_room_booking()
    └── _create_multi_room_booking()
    ↓
_save_to_guest_orders() → 儲存到 JSON
```

#### 【意圖偵測函數】

| 函數 | 行號 | 用途 | 關鍵字 |
|:-----|:----:|:-----|:-------|
| `is_booking_intent()` | 131-158 | 訂房意圖（含排除邏輯） | 訂房, 預訂, 住, 有房... |
| `is_same_day_intent()` | 160-183 | 當日意圖（時間+訂房） | 今天, 今晚, 現在... |
| `is_cancel_intent()` | 185-200 | 取消意圖 | 取消訂單, 不住了... |
| `_is_interrupt_intent()` | 202-218 | 中斷意圖 | 算了, 謝謝, 改天... |
| `_is_query_intent()` | 332-335 | 查詢意圖 | 查訂單, 我有訂房... |

#### 【時間驗證函數】

| 函數 | 行號 | 用途 |
|:-----|:----:|:-----|
| `is_within_booking_hours()` | 220-228 | 檢查是否在 22:00 前 |
| `_is_invalid_arrival_time()` | 230-306 | 檢查抵達時間是否無效 |
| `_is_vague_arrival_time()` | 308-330 | 檢查時間是否模糊 |

---

### 2.6 handlers/internal_query.py (內部報表，828 行，16 個函數)

#### 【報表查詢函數】

| 函數 | 行號 | 用途 | 觸發關鍵字 |
|:-----|:----:|:-----|:-----------|
| `query_today_status()` | 17-119 | 今日房況 | 今日房況、今天入住 |
| `query_yesterday_status()` | 121-192 | 昨日房況 | 昨日入住、昨天房況 |
| `query_specific_date()` | 261-360 | 特定日期房況 | 12/27入住、明天入住 |
| `query_week_forecast()` | 362-445 | 週報/週末預測 | 本週入住、週末房況 |
| `query_month_forecast()` | 447-562 | 月報 | 本月入住 |
| `query_today_checkin_list()` | 564-605 | 今日入住名單 | 今日名單 |
| `query_booking_by_name()` | 607-652 | 依姓名查詢 | 查XX的訂單 |
| `query_room_status()` | 654-686 | 房間狀態（清潔/停用） | 房間狀態 |
| `query_same_day_bookings()` | 688-736 | 今日臨時訂單 | 臨時訂單 |

---

### 2.7 handlers/vip_service_handler.py (VIP 服務，~450 行)

#### 【功能】

| 功能 | 用途 |
|:-----|:-----|
| 房況查詢 | 調用 internal_query 報表功能 |
| 天氣查詢 | 調用 weather_helper |
| 訂單查詢 | 內部 VIP 可查詢任意訂單 |
| 權限管理 | 管理 VIP 權限（需管理員） |

---

## 三、Helpers 模組詳細說明

### 3.1 helpers/pms_client.py (PMS API 客戶端，520 行)

| 函數 | 用途 |
|:-----|:-----|
| `get_booking_details(booking_id)` | 查詢訂單詳情 |
| `search_by_name(name)` | 依姓名搜尋訂單 |
| `search_by_phone(phone)` | 依電話搜尋訂單 |
| `check_health()` | API 健康檢查 |
| `get_today_availability()` | 查詢今日可用房型 |
| `create_same_day_booking(data)` | 建立當日預訂 |
| `get_same_day_bookings()` | 查詢當日預訂列表 |
| `cancel_same_day_booking(order_id)` | 取消當日預訂 |
| `update_supplement(booking_id, data)` | 更新訂單擴充資料 |
| `save_user_order_link(user_id, pms_id, ota_id)` | 儲存用戶訂單關聯 |

### 3.2 helpers/order_helper.py (訂單共用函數，190 行)

| 項目 | 用途 |
|:-----|:-----|
| `ROOM_TYPES` | 房型對照表（SSOT） |
| `normalize_phone(phone)` | 電話號碼標準化 |
| `clean_ota_id(ota_id)` | 清理 OTA 編號前綴 |
| `detect_booking_source(remarks, ota_id)` | 偵測訂房來源 |
| `get_breakfast_info(remarks, rooms)` | 判斷早餐資訊 |
| `get_resume_message(pending_intent)` | 取得中斷恢復訊息 |
| `sync_order_details(order_id, data)` | 同步訂單到 JSON + SQLite |

### 3.3 helpers/intent_detector.py (意圖偵測，200 行)

| 函數 | 用途 | 使用狀況 |
|:-----|:-----|:---------|
| `has_order_number(message)` | 偵測訂單編號 | ✅ 被 bot.py 使用 |
| `extract_order_number(message)` | 提取訂單編號 | ❌ 未使用 |
| `is_booking_intent(message)` | 偵測訂房意圖 | ❌ 各模組自己實作 |
| `is_query_intent(message)` | 偵測查詢意圖 | ❌ 各模組自己實作 |
| `is_cancel_intent(message)` | 偵測取消意圖 | ❌ 各模組自己實作 |
| `is_confirmation(message)` | 偵測確認意圖 | ❌ 未使用 |
| `is_rejection(message)` | 偵測否定意圖 | ❌ 未使用 |
| `extract_phone_number(message)` | 提取電話號碼 | ❌ 未使用 |

### 3.4 其他 Helpers

| 檔案 | 行數 | 用途 |
|:-----|:----:|:-----|
| `gmail_helper.py` | ~350 | Gmail 搜尋訂房確認信 |
| `weather_helper.py` | ~350 | 氣象署 API 查詢 |
| `pending_guest.py` | ~220 | 待入住客人清單 |
| `bot_logger.py` | ~200 | Bot 日誌記錄 |
| `api_logger.py` | ~150 | API 調用日誌 |
| `google_services.py` | ~80 | Google OAuth 認證 |

---

## 四、資料流向圖

```
客人訊息
    ↓
    ┌─────────────────────────────────────────────────────────────┐
    │                     app.py                                   │
    │   接收 Webhook → 解析訊息 → 調用 bot.generate_response()    │
    └─────────────────────────────────────────────────────────────┘
    ↓
    ┌─────────────────────────────────────────────────────────────┐
    │                     bot.py 路由判斷                          │
    │                                                              │
    │   ┌───────────────────────────────────────────────────────┐ │
    │   │ 1. 有訂單號？ → order_query_handler.handle_message()  │ │
    │   │ 2. 在預訂流程？ → same_day_handler.handle_message()   │ │
    │   │ 3. 是 VIP？ → vip_service.handle_message()            │ │
    │   │ 4. 其他 → Gemini AI (send_message)                    │ │
    │   └───────────────────────────────────────────────────────┘ │
    └─────────────────────────────────────────────────────────────┘
    ↓
    ┌───────────────────────────────────────────────────────────────┐
    │                     conversation_state_machine                 │
    │                                                                │
    │   ┌─────────────────────────────────────────────────────────┐ │
    │   │ 狀態管理（記憶體 + SQLite 持久化）                      │ │
    │   │ ├─ get_state()     → 取得當前狀態                       │ │
    │   │ ├─ transition()    → 狀態轉換                           │ │
    │   │ └─ pending_intent  → 跨流程意圖跳轉                     │ │
    │   └─────────────────────────────────────────────────────────┘ │
    └───────────────────────────────────────────────────────────────┘
    ↓
    ┌───────────────────────────────────────────────────────────────┐
    │                     外部 API 調用                             │
    │                                                                │
    │   ├── pms_client → PMS API (192.168.8.3:3000)                │
    │   ├── gmail_helper → Gmail API                                │
    │   ├── weather_helper → 氣象署 API                            │
    │   └── Gemini AI → Google AI                                   │
    └───────────────────────────────────────────────────────────────┘
    ↓
    ┌───────────────────────────────────────────────────────────────┐
    │                     資料儲存                                   │
    │                                                                │
    │   ├── data/chat_logs/guest_orders.json  → Bot 訂單記錄       │
    │   ├── data/chat_logs/conversations/     → 對話記錄           │
    │   ├── data/chat_logs/user_profiles.json → 用戶資料           │
    │   └── ktw-backend SQLite                → 擴充資料持久化     │
    └───────────────────────────────────────────────────────────────┘
```

---

## 五、待優化項目

| 問題 | 影響範圍 | 解決方案 |
|:-----|:---------|:---------|
| `bot.py` 1821 行太肥 | 維護困難 | 抽離至 chat_handler、intent_router |
| `same_day_booking.py` 1550 行太肥 | 維護困難 | 抽離時間驗證、多房型解析 |
| 意圖偵測函數重複 | bot.py、same_day_booking、order_query | 統一到 intent_detector.py |
| `ROOM_TYPE_MAP` 重複 | same_day_booking | 統一使用 order_helper.ROOM_TYPES |
| `intent_detector.py` 大部分未使用 | 浪費 | 強化並統一使用 |

---

*此架構圖記錄於 2025-12-22，供後續重構參考*
