# L4 後台服務層 (Services)

> 職責：排程系統、爬蟲、資料採集

---

## 架構

```
L4_services/
├── scheduler/          ← 排程系統
│   └── base_scheduler.py
├── scrapers/           ← 爬蟲腳本（JS/Python）
└── collectors/         ← 通用資料採集
```

---

## 排程系統

### 事件觸發調度 (EventScheduler)

- 入住前提醒
- 退房後邀評
- 訂單確認通知

### 定時任務調度 (CronScheduler)

- Google 評論監控
- OTA 評價採集
- 月報生成

---

## 爬蟲腳本 (scrapers/)

可放置 JS 或 Python 爬蟲腳本：

```
scrapers/
├── google-reviews/     ← Google 評論爬蟲
├── ota-monitor/        ← OTA 評價監控
└── event-collector/    ← 活動資訊採集
```

---

## 設計原則

> 此層透過 Payload 讀取排程設定，自動執行任務

---

_此文檔記錄於 2025-12-24_
