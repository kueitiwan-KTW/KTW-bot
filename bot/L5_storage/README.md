# L5 資料儲存層 (Storage)

> 職責：資料庫操作、快取管理、檔案儲存

---

## 架構

```
L5_storage/
├── database/           ← 資料庫操作
├── cache/              ← 快取管理（Redis）
└── files/              ← 檔案儲存
```

---

## 元件說明

### database/

- Session 持久化
- 對話記錄
- 採集資料儲存

### cache/

- Session 快取（Redis）
- 常用資料快取
- 意圖快取

### files/

- 上傳檔案儲存
- 報表檔案

---

## 資料庫規劃

| 階段   | 方案               |
| :----- | :----------------- |
| 開發   | SQLite             |
| 正式   | PostgreSQL         |
| 多實例 | Redis + PostgreSQL |

---

## 設計原則

> Admin-Web 可直接讀取此層，共用資料

---

_此文檔記錄於 2025-12-24_
