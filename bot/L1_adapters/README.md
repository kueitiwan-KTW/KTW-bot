# L1 平台適配層 (Adapters)

> 職責：接收各平台訊息，轉換為統一格式

---

## 架構

```
L1_adapters/
├── base_adapter.py   ← 統一訊息格式 + 適配器基類
├── line/             ← LINE 適配器
├── whatsapp/         ← WhatsApp 適配器（未來）
└── web/              ← 網站 Chatbot（未來）
```

---

## 核心概念

### 統一訊息格式

```python
@dataclass
class UnifiedMessage:
    text: str
    images: List[str]
    buttons: List[Dict]
    quick_replies: List[str]
```

### 適配器職責

1. **parse_event()** - 將平台事件轉為統一格式
2. **to_platform()** - 將統一訊息轉為平台格式
3. **send_message()** - 發送回覆
4. **send_push()** - 主動推送

---

## 設計原則

> 核心邏輯層 (L2) 不關心平台差異，Adapter 負責格式轉換

---

_此文檔記錄於 2025-12-24_
