# Backend API - Changelog

> 後端 API 服務的詳細變更記錄

---

## [1.0.1] - 2025-12-17

### ✨ 新功能：已 KEY 訂單自動匹配驗證

#### API 端點修改
**檔案**: `src/index.js`

**端點**: `PATCH /api/pms/same-day-bookings/:order_id/checkin` (L542-625)

#### 實作細節

1. **查詢臨時訂單** (L549-567)
   ```javascript
   const sameDayRes = await fetch('http://192.168.8.3:3000/api/bookings/same-day-list')
   const targetBooking = bookings.find(b => 
     b.item_id === order_id || b.order_id === order_id
   )
   ```

2. **查詢 PMS 今日入住名單** (L569-578)
   ```javascript
   const pmsRes = await fetch('http://192.168.8.3:3000/api/bookings/today-checkin')
   ```

3. **電話號碼匹配** (L580-598)
   - **匹配邏輯**: 電話號碼後 9 碼相同
   - **容錯**: 最少 8 碼即可匹配
   ```javascript
   const targetPhone = (targetBooking.phone || '').replace(/\D/g, '').slice(-9)
   const pmsPhone = (pms.contact_phone || '').replace(/\D/g, '').slice(-9)
   if (pmsPhone === targetPhone && targetPhone.length >= 8) {
     matched = true
   }
   ```

4. **狀態處理** (L600-625)
   - **匹配成功**: 呼叫 PMS API `/checkin` 端點，標記為 `checked_in`
   - **匹配失敗**: 呼叫 PMS API `/mismatch` 端點，返回錯誤訊息
   ```javascript
   return res.json({ 
     success: false, 
     mismatch: true,
     error: 'PMS 中找不到同電話的訂單，請確認 PMS 資料是否正確'
   })
   ```

### 🔗 整合更新
- **PMS API 整合**: 新增 `/mismatch` 端點呼叫
- **錯誤處理**: 統一回傳格式，包含 `mismatch` flag

### 📝 修改的文件
- `src/index.js` (L542-625) - Checkin API 重構

---

## [1.0.0] - 2025-12-10

### 初始版本
- Express.js 基礎架構
- 通知推送端點
- 服務狀態監控
- WebSocket 支援
