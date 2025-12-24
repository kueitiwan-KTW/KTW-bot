# L2 核心邏輯層 (Core)

> 職責：狀態機、AI、格式化、Session 管理

---

## 架構

```
L2_core/
├── machines/           ← 狀態機
│   └── base_machine.py
├── models/             ← 資料模型
├── formatters/         ← 格式化輸出
│   └── base_formatter.py
├── ai/                 ← AI 相關
└── adapters/           ← 外部服務適配
    └── payload_adapter.py
```

---

## 核心元件

### 狀態機 (machines/)

- `base_machine.py` - 狀態機基類，提供序列化/反序列化

### 格式化 (formatters/)

- `base_formatter.py` - 通用格式化工具（列表、表格、Emoji）

### 適配器 (adapters/)

- `payload_adapter.py` - Payload CMS API 適配器

---

## 設計原則

> 此層為**所有行業共用**的通用邏輯，不包含任何業務特定程式

---

_此文檔記錄於 2025-12-24_
