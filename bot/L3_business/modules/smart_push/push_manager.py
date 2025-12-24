# L3_business/modules/smart_push 智慧推送模組
# 建立日期：2025-12-24

"""
智慧推送模組

根據：會員等級 × 活動重要性 × 日期急迫性 → 分級推送
"""

from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime, date
from enum import Enum


class MemberTier(Enum):
    """會員等級"""
    NORMAL = "normal"
    VIP = "vip"
    VVIP = "vvip"


class Priority(Enum):
    """推送優先級"""
    LOW = 1       # 延後推送
    MEDIUM = 2    # 一般推送
    HIGH = 3      # 優先推送
    URGENT = 4    # 立即推送


@dataclass
class PushContent:
    """推送內容"""
    title: str
    message: str
    importance: int       # 1-5, 5 最重要
    deadline: date = None # 截止日期
    target_tiers: List[MemberTier] = None  # 目標會員等級


class PriorityCalculator:
    """
    優先級計算器
    
    優先級 = 會員等級 × 活動重要性 × 日期急迫性
    """
    
    TIER_WEIGHT = {
        MemberTier.NORMAL: 1,
        MemberTier.VIP: 2,
        MemberTier.VVIP: 3
    }
    
    @classmethod
    def calculate(cls, member_tier: MemberTier, content: PushContent) -> Priority:
        """計算推送優先級"""
        # 會員等級權重
        tier_score = cls.TIER_WEIGHT.get(member_tier, 1)
        
        # 活動重要性 (1-5)
        importance_score = content.importance
        
        # 日期急迫性
        urgency_score = 1
        if content.deadline:
            days_until = (content.deadline - date.today()).days
            if days_until <= 1:
                urgency_score = 4  # 明天截止
            elif days_until <= 3:
                urgency_score = 3
            elif days_until <= 7:
                urgency_score = 2
        
        # 綜合分數
        total_score = tier_score * importance_score * urgency_score / 5
        
        if total_score >= 8:
            return Priority.URGENT
        elif total_score >= 5:
            return Priority.HIGH
        elif total_score >= 2:
            return Priority.MEDIUM
        else:
            return Priority.LOW


class SmartPushManager:
    """
    智慧推送管理器
    """
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.calculator = PriorityCalculator()
    
    def queue_push(self, content: PushContent, members: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        將推送加入佇列，並根據優先級排序
        """
        push_queue = []
        
        for member in members:
            tier = MemberTier(member.get('tier', 'normal'))
            
            # 檢查是否在目標等級
            if content.target_tiers and tier not in content.target_tiers:
                continue
            
            priority = self.calculator.calculate(tier, content)
            
            push_queue.append({
                'member_id': member.get('id'),
                'line_user_id': member.get('line_user_id'),
                'priority': priority.value,
                'content': content
            })
        
        # 按優先級排序（高優先級先發）
        push_queue.sort(key=lambda x: x['priority'], reverse=True)
        
        return push_queue
    
    def execute_push(self, push_queue: List[Dict[str, Any]]) -> int:
        """
        執行推送
        
        Returns:
            int: 成功推送數量
        """
        success_count = 0
        
        for item in push_queue:
            # TODO: 呼叫 LINE 推送 API
            # line_adapter.send_push(item['line_user_id'], item['content'])
            success_count += 1
        
        return success_count
