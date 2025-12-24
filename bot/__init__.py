# Bot 五層架構主模組
# 建立日期：2025-12-24

"""
KTW Bot - 通用 SaaS Bot 框架

五層架構：
- L1_adapters: 平台適配層（LINE、WhatsApp、Web）
- L2_core: 核心邏輯層（狀態機、AI、Session）
- L3_business: 業務邏輯層（行業插件 + 可訂閱模組）
- L4_services: 後台服務層（排程、爬蟲、採集）
- L5_storage: 資料儲存層（資料庫、快取、檔案）
"""

__version__ = "0.1.0"
