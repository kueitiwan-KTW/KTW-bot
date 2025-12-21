"""
Bot Logger - Bot 內部運作日誌記錄器

記錄 Bot 的所有內部動作，方便問題追蹤與診斷。
自動清理 7 天前的 LOG 檔案。
"""

import os
import glob
import logging
from datetime import datetime, timedelta
from typing import Optional

class BotLogger:
    """
    Bot 內部運作日誌記錄器
    
    日誌格式：
    10:05:12 | RECEIVE | user=U45320... | type=text | message="我要查訂單"
    """
    
    # LOG 保留天數
    RETENTION_DAYS = 7
    
    def __init__(self, log_dir: Optional[str] = None):
        """
        初始化 Bot Logger
        
        Args:
            log_dir: 日誌目錄，預設為 data/bot_logs
        """
        if log_dir is None:
            # 找到專案根目錄
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            log_dir = os.path.join(project_root, "data", "bot_logs")
        
        self.log_dir = log_dir
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 設定 logger
        self.logger = logging.getLogger("BotLogger")
        self.logger.setLevel(logging.DEBUG)
        
        # 避免重複添加 handler
        if not self.logger.handlers:
            # Console Handler (簡化格式)
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_format = logging.Formatter('%(message)s')
            console_handler.setFormatter(console_format)
            self.logger.addHandler(console_handler)
        
        # 更新每日檔案 handler
        self._update_file_handler()
        
        # 啟動時清理舊 LOG
        self._cleanup_old_logs()
    
    def _update_file_handler(self):
        """更新每日日誌檔案 handler"""
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(self.log_dir, f"bot_{today}.log")
        
        # 移除舊的 FileHandler
        for handler in self.logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                self.logger.removeHandler(handler)
        
        # 添加新的 FileHandler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter('%(asctime)s | %(message)s', 
                                         datefmt='%H:%M:%S')
        file_handler.setFormatter(file_format)
        self.logger.addHandler(file_handler)
        
        self.current_date = today
    
    def _check_date(self):
        """檢查日期是否變更，需要輪換日誌檔案"""
        today = datetime.now().strftime("%Y-%m-%d")
        if not hasattr(self, 'current_date') or self.current_date != today:
            self._update_file_handler()
            self._cleanup_old_logs()
    
    def _cleanup_old_logs(self):
        """清理超過 7 天的 LOG 檔案"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.RETENTION_DAYS)
            log_files = glob.glob(os.path.join(self.log_dir, "bot_*.log"))
            
            for log_file in log_files:
                # 從檔名提取日期
                basename = os.path.basename(log_file)
                try:
                    # bot_2025-12-21.log -> 2025-12-21
                    date_str = basename.replace("bot_", "").replace(".log", "")
                    file_date = datetime.strptime(date_str, "%Y-%m-%d")
                    
                    if file_date < cutoff_date:
                        os.remove(log_file)
                        print(f"🗑️ 已清理舊 LOG: {basename}")
                except ValueError:
                    pass  # 檔名格式不符，跳過
        except Exception as e:
            print(f"⚠️ 清理 LOG 時發生錯誤: {e}")
    
    def _truncate(self, text: str, max_len: int = 50) -> str:
        """截斷過長的文字"""
        if text and len(text) > max_len:
            return text[:max_len] + "..."
        return text or ""
    
    def _short_user(self, user_id: str) -> str:
        """縮短 user_id 顯示"""
        if user_id and len(user_id) > 12:
            return user_id[:12] + "..."
        return user_id or "unknown"
    
    # ===== 訊息接收 =====
    def log_receive(self, user_id: str, msg_type: str, content: str):
        """記錄收到訊息"""
        self._check_date()
        self.logger.info(f"RECEIVE | user={self._short_user(user_id)} | type={msg_type} | content=\"{self._truncate(content)}\"")
    
    # ===== 意圖判斷 =====
    def log_intent(self, intent: str, confidence: Optional[float] = None, details: str = ""):
        """記錄意圖判斷"""
        self._check_date()
        conf_str = f" | confidence={confidence:.2f}" if confidence else ""
        detail_str = f" | {details}" if details else ""
        self.logger.info(f"INTENT | detected={intent}{conf_str}{detail_str}")
    
    # ===== 狀態機轉換 =====
    def log_state(self, user_id: str, from_state: str, to_state: str, reason: str = ""):
        """記錄狀態機轉換"""
        self._check_date()
        reason_str = f" | reason={reason}" if reason else ""
        self.logger.info(f"STATE | user={self._short_user(user_id)} | from={from_state} | to={to_state}{reason_str}")
    
    # ===== 工具調用 =====
    def log_tool_call(self, tool_name: str, params: dict):
        """記錄工具調用"""
        self._check_date()
        # 簡化 params 顯示
        param_str = ", ".join([f"{k}={self._truncate(str(v), 30)}" for k, v in params.items()])
        self.logger.info(f"TOOL_CALL | tool={tool_name} | params={{{param_str}}}")
    
    def log_tool_result(self, tool_name: str, success: bool, result: str = ""):
        """記錄工具結果"""
        self._check_date()
        status = "success" if success else "failed"
        result_str = f" | result={self._truncate(result, 80)}" if result else ""
        self.logger.info(f"TOOL_RESULT | tool={tool_name} | status={status}{result_str}")
    
    # ===== 回應 =====
    def log_response(self, user_id: str, response: str):
        """記錄 Bot 回應"""
        self._check_date()
        self.logger.info(f"RESPONSE | user={self._short_user(user_id)} | text=\"{self._truncate(response, 80)}\"")
    
    # ===== 錯誤 =====
    def log_error(self, error_type: str, message: str, user_id: str = ""):
        """記錄錯誤"""
        self._check_date()
        user_str = f" | user={self._short_user(user_id)}" if user_id else ""
        self.logger.error(f"ERROR | type={error_type}{user_str} | message={self._truncate(message, 150)}")
    
    # ===== VIP 功能 =====
    def log_vip(self, user_id: str, action: str, details: str = ""):
        """記錄 VIP 相關動作"""
        self._check_date()
        detail_str = f" | {details}" if details else ""
        self.logger.info(f"VIP | user={self._short_user(user_id)} | action={action}{detail_str}")
    
    # ===== 一般資訊 =====
    def log_info(self, message: str):
        """記錄一般資訊"""
        self._check_date()
        self.logger.info(f"INFO | {message}")
    
    def log_debug(self, message: str):
        """記錄除錯資訊 (只寫入檔案)"""
        self._check_date()
        self.logger.debug(f"DEBUG | {message}")


# 單例模式
_bot_logger_instance = None

def get_bot_logger() -> BotLogger:
    """取得 Bot Logger 單例"""
    global _bot_logger_instance
    if _bot_logger_instance is None:
        _bot_logger_instance = BotLogger()
    return _bot_logger_instance
