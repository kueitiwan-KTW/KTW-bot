# Bot 架構 SSOT 規則（最終版）

> 建立日期：2025-12-24
> 依據：GPT 架構審查建議 + 討論確認

---

## 核心原則

> **業務邏輯 SSOT 只能在一個軸上；其他軸只能做封裝/入口，不得複製邏輯。**

---

## SSOT 三層分離

| SSOT 層           | 位置            | 負責什麼     | 範例                            |
| :---------------- | :-------------- | :----------- | :------------------------------ |
| **How SSOT**      | `capabilities/` | 能力怎麼執行 | 排程策略、去重/節流、重試、觀測 |
| **What SSOT**     | `plugins/`      | 產業要做什麼 | 觸發條件、模板、欄位映射        |
| **Override SSOT** | `tenants/`      | 租戶差異化   | 文案覆寫、頻率上限、開關        |

### 範例：入住提醒

| 層       | 位置                             | 內容                             |
| :------- | :------------------------------- | :------------------------------- |
| How      | `capabilities/reminder/`         | 怎麼提醒：排程、去重、重試、發送 |
| What     | `plugins/hotel/triggers/`        | 提醒什麼：入住前 1 天、模板      |
| Override | `tenants/A_hotel/overrides.json` | A 飯店改成 2 天前                |

---

## 穩定邊界

| 層              | 職責                               |
| :-------------- | :--------------------------------- |
| **L2_core**     | 定義契約（events/spec/interfaces） |
| **L3_business** | 可組裝的能力 + 行業規格            |
| **L4_services** | 可水平擴展的引擎實作               |

> **契約鎖死**：事件格式、ScheduleSpec、Publisher interface、Collector interface

---

## apps/ 職責（唯一）

- 接收事件 → 授權/租戶辨識 → 選擇 flow → 回傳統一輸出

### 禁止放在 apps/

- ❌ 產業規則
- ❌ 排程實作
- ❌ 第三方 API business rules

---

## Scheduler SSOT

| 層                       | 職責                                  |
| :----------------------- | :------------------------------------ |
| `L4_services/scheduler/` | **唯一**能建立/取消/查詢 job          |
| `capabilities/*`         | 只產出 ScheduleSpec                   |
| `plugins/*`              | 只產出「事件 → schedule spec 的規則」 |

---

## 訂閱控制落點

- **落點**：`apps/` 或 `CapabilityRegistry`
- **規則**：capability 不知道「付費」，只知道「給我 spec 我就執行」

```python
# apps/registry.py
def load_capabilities(tenant_id: str):
    subscription = payload_api.get_subscription(tenant_id)
    for module in subscription['modules']:
        registry.enable(module)  # 啟用對應 capability
```

---

## 完整資料夾結構

```
bot/
├── L1_adapters/              → 平台接入
│
├── L2_core/                  → 契約層
│   ├── events/               → 統一事件格式
│   ├── specs/                → ScheduleSpec, PublisherSpec
│   ├── machines/             → Machine 基類
│   └── formatters/           → 跨產業共用格式化
│
├── L3_business/
│   ├── capabilities/         → How SSOT
│   │   ├── reminder/         → 提醒能力
│   │   ├── review_monitor/   → 評論監控
│   │   ├── auto_publish/     → 自動發佈
│   │   └── smart_push/       → 智慧推送
│   │
│   ├── plugins/              → What SSOT
│   │   ├── hotel/
│   │   │   ├── triggers/     → 入住提醒、退房提醒
│   │   │   ├── tasks/        → 評論抓取
│   │   │   ├── machines/     → 訂房、查詢狀態機
│   │   │   └── formatters/   → 產業格式化
│   │   ├── restaurant/
│   │   └── clinic/
│   │
│   └── apps/                 → 入口層
│       ├── customer/         → 客服入口
│       ├── assistant/        → 助理入口
│       └── registry.py       → 訂閱控制
│
├── L4_services/              → 引擎層
│   ├── scheduler/            → 唯一排程引擎
│   ├── publishers/           → 發佈引擎
│   └── collectors/           → 採集引擎
│
├── L5_storage/
│
└── tenants/                  → Override SSOT
    ├── ktw_hotel/
    │   ├── config.json
    │   └── overrides.json    → 租戶覆寫
    └── ...
```

---

---

## 資料路徑原則

> **資料路徑越短越單純越好**

### 核心原則

| 原則                 | 說明                              |
| :------------------- | :-------------------------------- |
| **直接讀取 SSOT**    | 從資料源直接讀取，不做中繼複製    |
| **模組獨立呼叫**     | Bot、Admin-Web 各自有獨立 Adapter |
| **只存獨有資料**     | 各模組只儲存自己產生的資料        |
| **共用資料集中快取** | 房型、價格等常用資料一次載入      |
| **減少呼叫次數**     | 需要的自己來拿，不重複呼叫        |

### 資料分類

| 資料類型     | 存放位置         | 誰是 SSOT | 誰來讀取                     |
| :----------- | :--------------- | :-------- | :--------------------------- |
| 訂單主資料   | PMS Database     | PMS       | 各模組獨立呼叫 API           |
| Bot 補充資料 | Session / SQLite | Bot       | Bot 自己、Admin-Web 合併顯示 |
| 共用設定     | L5_storage/cache | Config    | 各模組自己來拿               |

### 正確架構

```
┌─────────────────────────────────────────────────────┐
│              PMS Database (SSOT)                     │
└─────────────────────────────────────────────────────┘
         ↑                              ↑
    獨立呼叫                         獨立呼叫
         ↑                              ↑
┌────────┴────────┐            ┌────────┴────────┐
│      Bot        │            │   Admin-Web     │
│  (L1 Adapter)   │            │  (獨立 Adapter) │
└─────────────────┘            └─────────────────┘
         │
         ↓
┌─────────────────┐
│  Session (L5)   │  ← 只存 Bot 獨有的資料
│ - 對話狀態       │
│ - 補充欄位       │
└─────────────────┘

┌─────────────────────────────────────────────────────┐
│  共用快取 (L5_storage/cache)                         │
│  - 房型對照表、價格表、租戶設定                        │
│  - 一次載入，各模組自己來拿                           │
└─────────────────────────────────────────────────────┘
```

### 禁止事項

- ❌ 把訂單主資料複製到 `guest_orders.json`
- ❌ Bot 和 Admin-Web 共用同一個 API Client
- ❌ 同一份資料在多處手動同步
- ❌ 每次需要都重新呼叫 API（應使用快取）

---

_此文檔記錄於 2025-12-24_
_資料路徑原則新增於 2025-12-24_
