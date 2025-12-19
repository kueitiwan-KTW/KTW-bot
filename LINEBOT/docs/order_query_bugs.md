# 訂單查詢模組 Bug 彙整表 (Bug Report)

以下是目前模組化後，經檢查發現的技術問題清單：

| 編號 | 所在檔案 | 問題描述 | 影響程度 | 預計修復說明 |
|:---:|:---|:---|:---:|:---|
| 01 | `order_query_handler.py` | 呼叫了 `ChatLogger` 中不存在的方法 `update_order_info`。 | 🔴 致命 | 修正為呼叫 `update_guest_request` 並對齊參數。 |
| 02 | `order_query_handler.py` | `save_to_guest_orders` 呼叫 `logger.save_order` 時參數數量不符。 | 🔴 致命 | 修正參數傳遞，將 session 內容封裝成單一 Dict 傳入。 |
| 03 | `pms_client.py` | `check_health` 的 URL 拼湊邏輯錯誤（會出現重複的 `/api`）。 | 🟡 中等 | 重新校準 API 健康檢查的路徑拼接字串。 |
| 04 | `bot.py` | 進入 `OrderQueryHandler` 的觸發門檻太高，導致首則訊息會被 AI 攔截。 | 🟠 關鍵 | 優化 `bot.py` 路由，當偵測到數字（疑似訂單號）時，優先詢問處理器是否要承接。 |
| 05 | `gmail_helper.py` | 搜尋邏輯中的 Deep Scan 可能會掃描到舊訂單。 | 🟢 輕微 | 加入更嚴格的日期範圍與關鍵字白名單過濾。 |

---
**說明：**
*   **🔴 致命**：會導致程式執行到一半直接中斷或報錯。
*   **🟠 關鍵**：功能尚可運作，但邏輯不順暢，會造成使用者體驗斷層。
*   **🟡 中等**：後台監控或健康度檢查會顯示異常。

---
> [!IMPORTANT]
> **建議行動：**
> 如果您確認此清單無誤，我建議立刻執行修復（尤其是 01 與 02），以確保流程能跑完而不當機。
