"""
日誌工具

包含：
- 控制台輸出（INFO 以上）
- 一般日誌檔案（DEBUG 以上，每日輪替，保留 7 天）
- 錯誤日誌檔案（ERROR 以上，每日輪替，保留 30 天）
"""

from loguru import logger
import sys
import os

# 確保日誌目錄存在
os.makedirs("logs", exist_ok=True)

# 移除預設 handler
logger.remove()

# 控制台輸出（INFO 以上）
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)

# 一般日誌檔案（DEBUG 以上）
logger.add(
    "logs/fish_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="7 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    encoding="utf-8"
)

# 錯誤日誌檔案（ERROR 以上，專門記錄錯誤）
logger.add(
    "logs/error_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="30 days",  # 錯誤日誌保留更久
    level="ERROR",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}\n{exception}",
    encoding="utf-8",
    backtrace=True,  # 顯示完整堆疊追蹤
    diagnose=True    # 顯示變數值
)

# Session 專用日誌（記錄登入狀態變化）
logger.add(
    "logs/session_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="14 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
    filter=lambda record: "session" in record["extra"].get("category", "") or 
                          "Keep-Alive" in record["message"] or
                          "登入" in record["message"] or
                          "session" in record["message"].lower(),
    encoding="utf-8"
)

__all__ = ["logger"]
