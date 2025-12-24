# L3 業務邏輯層 - roles 資料夾

> 依角色區分業務邏輯

---

## 架構

```
L3_business/
├── plugins/            ← 行業插件（對應 PluginConfigs）
├── modules/            ← 訂閱模組（對應 Subscriptions）
└── roles/              ← 角色分離
    ├── customer/       ← 客服角色（面對客人）
    │   ├── handlers/
    │   ├── machines/   ← 對話狀態機
    │   └── formatters/
    └── assistant/      ← 助理角色（面對老闆/員工）
        ├── secretary/  ← 秘書功能（對應 OwnerConfigs）
        ├── triggers/   ← 事件觸發（對應 Triggers）
        ├── tasks/      ← 常態式任務（對應 Tasks）
        ├── scheduler/  ← 智慧推送
        └── publishers/ ← 自動發佈
```

---

## Payload 對應關係

| roles 資料夾            | Payload Collection |
| :---------------------- | :----------------- |
| `customer/machines/`    | -                  |
| `assistant/secretary/`  | OwnerConfigs       |
| `assistant/triggers/`   | Triggers           |
| `assistant/tasks/`      | Tasks              |
| `assistant/scheduler/`  | -                  |
| `assistant/publishers/` | -                  |

---

_此文檔記錄於 2025-12-24_
