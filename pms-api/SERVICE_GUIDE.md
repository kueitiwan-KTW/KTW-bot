# PMS API Windows Service 安裝指南 (開機即啟動)

要讓 PMS API 在開機時（即使未登入）自動啟動，我們使用 **NSSM (Non-Sucking Service Manager)** 工具將其註冊為 Windows 服務。

## 📥 步驟 1：下載必備工具

1. 下載 **NSSM 2.24**：
   - 下載連結：[https://nssm.cc/release/nssm-2.24.zip](https://nssm.cc/release/nssm-2.24.zip)
2. 解壓縮檔案。
3. 進入 `win64` 資料夾。
4. 將 `nssm.exe` 複製到您的專案目錄：
   - 目標位置：`C:\ktw-bot\pms-api\nssm.exe`

## 💿 步驟 2：安裝服務

1. 以 **系統管理員身分** 開啟檔案總管。
2. 進入 `C:\ktw-bot\pms-api`。
3. 右鍵點擊 `install-service.bat`，選擇 **「以系統管理員身分執行」**。
4. 等待腳本執行完成，出現 "SUCCESS" 字樣。

## ✅ 步驟 3：驗證

1. 按 `Win + R`，輸入 `services.msc`。
2. 找到服務名稱：**KTW Hotel PMS API**。
3. 確認狀態為 **「執行中」 (Running)**。
4. 確認啟動類型為 **「自動」 (Automatic)**。

現在，即使您將電腦重開機並停留在登入畫面，API 也會在後台自動運作！

## 🛠 管理服務

- **停止服務**：`net stop KTW_PMS_API` (管理員權限 CMD)
- **啟動服務**：`net start KTW_PMS_API`
- **查看日誌**：`C:\ktw-bot\pms-api\logs\service.log`
