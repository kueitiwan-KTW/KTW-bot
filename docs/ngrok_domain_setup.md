# Ngrok 固定網域設定指南 (Custom Domain Setup)

本文件說明如何將您的網域 **`ktwhotel.com`** 綁定至 Ngrok，讓 LINE Bot 擁有固定的 Webhook URL。

## 前置準備
請確認您擁有：
1.  **Ngrok 帳號** (需已登入)。
2.  **網域管理權限** (購買 `ktwhotel.com` 的平台，如 GoDaddy, Namecheap 等)。

---

## 第一步：在 Ngrok 官網註冊網域
1.  登入 [Ngrok Dashboard](https://dashboard.ngrok.com/cloud-edge/domains)。
2.  在左側選單點擊 **Cloud Edge** -> **Domains**。
3.  點擊右上角的 **+ New Domain**。
4.  在 Domain 欄位輸入：`ktwhotel.com` (或您想使用的子網域，如 `bot.ktwhotel.com`)。
5.  點擊 **Create Domain**。
6.  系統會顯示一組 **CNAME Target** (例如 `21345-ktwhotel-com.ngrok.app`)，**請複製這串網址**。

## 第二步：設定 DNS (在您的網域註冊商)
1.  登入您購買網域的平台 (例如 GoDaddy)。
2.  進入 **DNS 管理 (DNS Management)** 頁面。
3.  新增一筆紀錄 (Add Record)：
    *   **類型 (Type)**: `CNAME`
    *   **名稱 (Host/Name)**: `@` (若要用根網域) 或 `bot` (若要用子網域)。
    *   **值 (Value/Points to)**: 貼上剛剛在 Ngrok 複製的 **CNAME Target**。
    *   **TTL**: 設定為最小值 (如 600秒 或 1小時)。
4.  儲存設定。

> ⏳ **等待生效**：DNS 設定通常需要 10 分鐘至 1 小時才會生效。

---

## 第三步：修改啟動設定 (ecosystem.config.js)
當上述兩步都完成且 DNS 生效後，請回到這台主機修改設定，讓 Ngrok 知道要使用這個網域。

1.  開啟 `/Users/ktw/ktw-projects/KTW-bot/ecosystem.config.js`。
2.  找到 `Ngrok-Tunnel` 的設定區塊，修改 `args` 參數：

```javascript
{
    name: "Ngrok-Tunnel",
    script: "./ngrok",
    // 修改前: args: "http 5001",
    // 修改後 (加入 --domain):
    args: "http --domain=ktwhotel.com 5001",
    cwd: "./",
    watch: false
}
```

3.  重啟服務以生效：
    ```bash
    npx pm2 restart Ngrok-Tunnel
    npx pm2 save
    ```

## 第四步：更新 LINE Developer Console
最後，別忘了到 LINE Developers Console 更新 Webhook URL：
*   **Webhook URL**: `https://ktwhotel.com/callback`
