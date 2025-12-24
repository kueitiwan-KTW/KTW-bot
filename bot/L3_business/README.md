# L3 業務邏輯層 (Business)

> 職責：行業插件 + 可訂閱模組

---

## 架構

```
L3_business/
├── plugins/            ← 行業插件（按行業分）
│   ├── hotel/          ← 飯店插件
│   ├── restaurant/     ← 餐廳插件（未來）
│   └── clinic/         ← 診所插件（未來）
│
└── modules/            ← 可訂閱模組
    ├── event_triggers/     ← 事件觸發包
    ├── review_management/  ← 評論管理包
    ├── local_info/         ← 在地資訊包
    └── multi_platform/     ← 跨平台包
```

---

## 行業插件結構

每個行業插件包含：

```
plugins/hotel/
├── machines/       ← 行業專屬狀態機
├── triggers/       ← 事件觸發
├── tasks/          ← 常態式任務
├── collectors/     ← 資訊採集
├── models/         ← 資料模型
└── formatters/     ← 格式化輸出
```

---

## 可訂閱模組

| 模組              | 說明                   |
| :---------------- | :--------------------- |
| event_triggers    | 入住提醒、邀請評價     |
| review_management | Google 評論監控        |
| local_info        | 周邊活動、美食推薦     |
| multi_platform    | WhatsApp、網站 Chatbot |

---

## 設計原則

> 新增行業 → 加 plugins 資料夾
> 新增功能 → 加 modules 資料夾

---

_此文檔記錄於 2025-12-24_
