# KTW Bot 專案核心架構知識 (Architecture Knowledge)

本文檔記錄了 KTW Bot 專案的核心設計原則與架構規範，以實際案例說明。

---

## 📊 資料分層架構 (Data Layer Architecture)

### 實際案例：訂單 `RMAG1681488333` 客人「楊楊楊」

**情境**：客人在 12/24 22:27 透過 LINE Bot 確認訂單資訊，但流程卡在「收集特殊需求」階段。

```
客人說：「我有2筆訂單唷」
Bot 誤判為「特殊需求」→ 流程卡住
→ 資料只存在 Session，未同步到 guest_orders.json
→ Admin-Web 無法顯示 Bot 收集的資料
```

### 資料分層解決方案

```
┌─────────────────────────────────────────────────────────┐
│ 第 1 層：訂單主資料 (SSOT = PMS Database)               │
├─────────────────────────────────────────────────────────┤
│ • 訂單編號：RMAG1681488333                              │
│ • 入住日期：2025-12-28                                  │
│ • 房型：標準三人房 x1                                   │
│ • 電話：0915085163（OTA 原始資料）                      │
│ → 這是「原始事實」，從 PMS 查詢一定正確                 │
└─────────────────────────────────────────────────────────┘
                         ↓ Bot 負責收集補充資料
┌─────────────────────────────────────────────────────────┐
│ 第 2 層：Bot 補充資料 (SSOT = SessionManager)            │
├─────────────────────────────────────────────────────────┤
│ • 電話確認：0915085163（客人說「是」，確認正確）        │
│ • 抵達時間：「應該6.7點左右」（客人直接說的）           │
│ • 特殊需求：（流程卡住，未收集到）                      │
│ • LINE 姓名：楊楊楊（關聯到 LINE User ID）              │
│ → 這些是 Bot 與客人互動後「更新/補充」的資料            │
└─────────────────────────────────────────────────────────┘
                         ↓ Admin-Web 合併顯示
┌─────────────────────────────────────────────────────────┐
│ 第 3 層：展示層 (Admin-Web)                             │
├─────────────────────────────────────────────────────────┤
│ • 讀取 PMS 主資料                                       │
│ • 合併 Bot 補充資料（即使流程卡住也要顯示）             │
│ • 不做資料收集，純展示                                  │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 問題根因與修復

### 問題 1：Bot 流程卡住

**根因**：`_handle_special_requests` 只用關鍵字匹配，沒有 AI 意圖判斷

**修復**：在 `handle_message` 入口增加意圖檢測層

```python
# order_query_handler.py L72-97
if state != 'idle':
    # 1. 偵測「查詢新訂單」意圖
    if IntentDetector.is_new_order_query(message, current_order):
        self._complete_collection(user_id)
        return self._query_order(user_id, new_order)

    # 2. 偵測「中斷/取消」意圖
    if IntentDetector.is_interrupt_intent(message):
        self.state_machine.transition(user_id, 'idle')
        return "好的，已為您取消本次操作。"
```

### 問題 2：Admin-Web 沒顯示資料

**根因**：`processBookings` 只查 `guest_orders.json`，不查進行中的 Session

**修復**：新增查詢 `bot_sessions` 表

```javascript
// ktw-backend/src/index.js
async function processBookings(bookings, guestOrders, profiles = {}) {
    // 🔧 新增：查詢進行中的 Bot Sessions
    let activeSessions = [];
    try {
        activeSessions = await getAllActiveSessions();
    } catch (err) {
        console.error('查詢進行中 sessions 失敗:', err.message);
    }

    // 建立 session map
    const sessionMap = {};
    activeSessions.forEach(session => {
        const orderId = session.data?.order_id;
        if (orderId) sessionMap[orderId] = session.data;
    });

    // 優先級: SQLite supplement > 進行中 Session > guest_orders.json > PMS
    contact_phone: supplement?.confirmed_phone || sessionInfo?.phone || botInfo?.phone || formattedPhone,
    arrival_time_from_bot: supplement?.arrival_time || sessionInfo?.arrival_time || botInfo?.arrival_time || null,
}
```

---

## 🏗️ SSOT 核心原則 (Single Source of Truth)

### 三層分離架構

| 層級              | 位置            | 職責 (SSOT Role)             | 範例               |
| :---------------- | :-------------- | :--------------------------- | :----------------- |
| **How SSOT**      | `capabilities/` | 定義「怎麼做」（邏輯、排程） | 推送策略、重試機制 |
| **What SSOT**     | `plugins/`      | 定義「做什麼」（欄位、流程） | 訂單查詢流程       |
| **Override SSOT** | `tenants/`      | 定義「差異化」（文案、開關） | 飯店自訂歡迎語     |

### 資料路徑原則

> **資料路徑越短越單純越好**

| 原則              | 說明                   | 本案例應用                 |
| :---------------- | :--------------------- | :------------------------- |
| **直接讀取 SSOT** | 不做中繼複製           | PMS 資料直接從 API 取      |
| **只存獨有資料**  | 各模組只存自己產生的   | Bot 只存電話確認、抵達時間 |
| **即時同步**      | 每一步都同步，不等完成 | Session 即時寫入 SQLite    |

---

## 🌐 SaaS 多租戶設計

### 模組化考量

| 模組         | 功能              | 無模組時的顯示          |
| :----------- | :---------------- | :---------------------- |
| **基礎版**   | PMS 串接          | 必備，顯示 PMS 原始資料 |
| **Bot 模組** | 收集補充資料      | 欄位顯示「-」或不顯示   |
| **進階模組** | VIP 標籤、BI 分析 | 功能區塊不顯示          |

### 設計原則

```javascript
// 處理「沒有 Bot 模組」的情況
const result = {
  // 第 1 層：PMS 資料（一定有）
  contact_phone: formattedPhone,

  // 第 2 層：Bot 補充資料（可能沒有）
  contact_phone_confirmed: hasBotModule
    ? supplement?.confirmed_phone || sessionInfo?.phone
    : null,
};
```

---

## 📝 技術規範

- **語言**：全語境繁體中文（思考、參數、輸出）
- **流程控制**：AI 意圖判斷 → 狀態機 → 業務執行
- **更新機制**：程式碼變動必須同步更新 `CHANGELOG.md`

---

_文件建立日期：2025-12-24_
_案例：訂單 RMAG1681488333 客人「楊楊楊」流程卡住問題_
