# 變更記錄 (Changelog)

遵循 [Semantic Versioning](https://semver.org/) 規範。

---

## [0.2.1] - 2025-12-25

### ✨ SDK 升級

**升級 Google GenAI SDK**

- **檔案**: `L2_core/ai/intent_recognizer.py` (L48-56, L90-94)
- **變更**: 從舊版 `google-generativeai` 升級至新版 `google-genai`
- **原因**: 舊版 SDK 即將停止維護，新版採用 Client 模式更符合 Google Cloud 標準
- **影響**: 意圖識別功能改用 `genai.Client()` 呼叫

**升級 LINE Bot SDK 至 v3.x**

- **檔案**:
  - `app.py` (L17-27, L40-42, L65-86)
  - `L1_adapters/line/adapter.py` (L36-56, L89-130, L132-197)
  - `requirements.txt`
- **變更**:
  - `line-bot-sdk>=2.0.0` → `line-bot-sdk>=3.0.0`
  - import 從 `linebot` 改為 `linebot.v3`
  - API 呼叫改用 `ApiClient` context manager
- **原因**: v2.x 已停止維護，v3.x 基於 OpenAPI 自動生成，同步快
- **影響**: 所有 LINE 相關 API 呼叫方式已更新

### 📝 修改的文件

- `requirements.txt` - 升級依賴版本
- `app.py` - 升級 LINE SDK import 和 API 呼叫
- `L1_adapters/line/adapter.py` - 升級所有 LINE API 方法
- `L2_core/ai/intent_recognizer.py` - 升級 GenAI SDK

---

## [0.2.0] - 2025-12-24

### ✨ 初始架構建立

- 建立五層架構 (L1~L5)
- 實現 LINE 適配器
- 實現意圖識別器
- 實現簡化版狀態機

---

## [0.1.0] - 2025-12-24

- 專案初始化
