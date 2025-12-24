# Tenants 租戶配置

> 職責：儲存各租戶的專屬配置

---

## 架構

```
tenants/
└── {tenant_id}/
    ├── config.json         ← 通用設定
    ├── prompts.json        ← AI 提示詞（未來從 Payload 讀取）
    ├── messages.json       ← 訊息模板（未來從 Payload 讀取）
    ├── triggers.json       ← 事件觸發設定
    ├── tasks.json          ← 常態式任務設定
    └── collectors.json     ← 資訊採集設定
```

---

## 配置說明

### config.json

```json
{
  "tenantId": "ktw_hotel",
  "name": "KTW Hotel",
  "industry": "hotel",
  "location": { "lat": 25.03, "lng": 121.56, "radiusKm": 50 }
}
```

---

## 配置來源

| 階段    | 來源                       |
| :------ | :------------------------- |
| Phase 1 | 本地 JSON 檔案             |
| Phase 2 | Payload CMS API + 本地快取 |

---

## 設計原則

> 新增租戶 → 加新資料夾
> 未來改從 Payload 即時讀取

---

_此文檔記錄於 2025-12-24_
