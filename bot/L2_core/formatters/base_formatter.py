# L2_core 基礎格式化器
# 建立日期：2025-12-24

"""
格式化輸出工具

提供通用的訊息格式化方法，如表格、列表、分隔線等
"""

from typing import List, Dict, Any


class BaseFormatter:
    """基礎格式化器"""
    
    # 通用 Emoji
    EMOJI = {
        'check': '✅',
        'cross': '❌',
        'warning': '⚠️',
        'info': 'ℹ️',
        'star': '⭐',
        'calendar': '📅',
        'clock': '🕐',
        'phone': '📞',
        'house': '🏠',
        'person': '👤',
        'money': '💰',
        'note': '📝',
    }
    
    @classmethod
    def divider(cls, char: str = "─", length: int = 20) -> str:
        """分隔線"""
        return char * length
    
    @classmethod
    def header(cls, title: str) -> str:
        """標題"""
        return f"【{title}】"
    
    @classmethod
    def bullet_list(cls, items: List[str], bullet: str = "•") -> str:
        """項目列表"""
        return "\n".join([f"{bullet} {item}" for item in items])
    
    @classmethod
    def numbered_list(cls, items: List[str]) -> str:
        """編號列表"""
        return "\n".join([f"{i+1}. {item}" for i, item in enumerate(items)])
    
    @classmethod
    def key_value(cls, data: Dict[str, Any], separator: str = "：") -> str:
        """鍵值對格式"""
        lines = [f"{key}{separator}{value}" for key, value in data.items()]
        return "\n".join(lines)
    
    @classmethod
    def table(cls, headers: List[str], rows: List[List[str]]) -> str:
        """簡單表格（純文字）"""
        lines = [" | ".join(headers)]
        lines.append("-" * len(lines[0]))
        for row in rows:
            lines.append(" | ".join(row))
        return "\n".join(lines)
    
    @classmethod
    def success(cls, message: str) -> str:
        """成功訊息"""
        return f"{cls.EMOJI['check']} {message}"
    
    @classmethod
    def error(cls, message: str) -> str:
        """錯誤訊息"""
        return f"{cls.EMOJI['cross']} {message}"
    
    @classmethod
    def warning(cls, message: str) -> str:
        """警告訊息"""
        return f"{cls.EMOJI['warning']} {message}"
