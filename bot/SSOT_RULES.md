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

_此文檔記錄於 2025-12-24_
