# KTW Bot - 通用 SaaS Bot 框架

> 建立日期：2025-12-24
> 版本：v0.2.0

---

## 產品願景

> **任何服務業都能使用的 AI 客服 + 老闆秘書 SaaS Bot**

---

## SSOT 三層分離

| 層           | 位置            | 職責         |
| :----------- | :-------------- | :----------- |
| **How**      | `capabilities/` | 能力怎麼執行 |
| **What**     | `plugins/`      | 產業要做什麼 |
| **Override** | `tenants/`      | 租戶差異化   |

---

## 五層架構

```
bot/
├── L1_adapters/              → 平台接入
├── L2_core/                  → 契約層
├── L3_business/
│   ├── capabilities/         → How（能力框架）
│   ├── plugins/              → What（產業規格）
│   └── apps/                 → 入口層
├── L4_services/              → 引擎層
├── L5_storage/               → 資料層
└── tenants/                  → Override
```

---

## 快速開始

```bash
cd /Users/ktw/ktw-projects/KTW-bot/bot
pip install -r requirements.txt
cp .env.example .env
python app.py
```

---

## 詳細規則

請參閱 [SSOT_RULES.md](./SSOT_RULES.md)

---

_此文檔記錄於 2025-12-24_
