# 服務狀態監控組件使用說明

## 📋 用途

這是一個可重用的組件，用於在管理後台的任何頁面顯示系統服務狀態。

## ✅ 已包含的頁面

- ✅ `/` - 入住客人管理頁面（today_checkins.html）
- ✅ `/rich-menu` - Rich Menu 管理頁面（rich_menu_manager.html）

## 🚀 如何在新頁面使用

### 方法 1：使用 {% include %}（推薦）

在新的 HTML 模板文件中，在 `<body>` 標籤下、導航列之前加入：

```html
<body>
    <div class="container">
        <!-- 狀態監控 - 直接引入組件 -->
        {% include 'status_monitor_component.html' %}

        <!-- 導航列 -->
        <div class="nav-bar">
            ...
        </div>
        ...
    </div>
</body>
```

### 方法 2：手動複製（不推薦）

如果無法使用 include，可以直接複製 `templates/status_monitor_component.html` 的全部內容到頁面中。

## 📍 放置位置

**重要**：狀態監控必須放在：
1. `<body>` 標籤之後
2. 導航列之前（如果有的話）
3. 在 `.container` div 內部

這樣可以確保在所有頁面的最上方都能看到狀態監控。

## 🎨 監控項目

組件會自動監控以下服務：

| 服務 | 綠燈條件 | 檢查方式 |
|------|---------|---------|
| Bot Server | Port 5001 有進程運行 | lsof 檢查 |
| 管理後台 | 能訪問此 API | 自動顯示運行中 |
| ngrok | Port 4040 API 有回應 | HTTP 檢查 |
| Gmail API | token.json 和 credentials.json 存在 | 文件檢查 |
| Gemini AI | GOOGLE_API_KEY 環境變數已設定 | 環境變數檢查 |

## ⚙️ API 依賴

組件依賴後端 API：`/api/system/status`

此 API 已在 `admin_dashboard.py` 中實作，會返回所有服務狀態的 JSON 數據。

## 🔄 自動更新

- 每 3 秒自動更新一次
- 顯示最後更新時間
- 呼吸燈動畫效果

## 💡 提示

- 組件使用 IIFE（立即執行函數），不會污染全局作用域
- CSS 和 JavaScript 都包含在組件中，無需額外引入
- 如果需要修改樣式或邏輯，只需修改 `status_monitor_component.html` 一個文件即可
