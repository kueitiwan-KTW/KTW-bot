import json
import os
from datetime import datetime
import uuid

class MessageManager:
    """管理後台留言板"""
    
    def __init__(self):
        self.messages_file = 'chat_logs/messages.json'
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """確保資料檔案存在"""
        os.makedirs('chat_logs', exist_ok=True)
        if not os.path.exists(self.messages_file):
            with open(self.messages_file, 'w', encoding='utf-8') as f:
                json.dump({'messages': []}, f, ensure_ascii=False, indent=2)
    
    def _load_messages(self):
        """載入所有留言"""
        try:
            with open(self.messages_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('messages', [])
        except Exception as e:
            print(f"Error loading messages: {e}")
            return []
    
    def _save_messages(self, messages):
        """儲存留言"""
        try:
            with open(self.messages_file, 'w', encoding='utf-8') as f:
                json.dump({'messages': messages}, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving messages: {e}")
            return False
    
    def get_all_messages(self):
        """取得所有留言（最新的在前）"""
        messages = self._load_messages()
        # 未完成的在前，已完成的在後，同類型按時間排序
        pending = [m for m in messages if not m.get('completed', False)]
        completed = [m for m in messages if m.get('completed', False)]
        
        pending.sort(key=lambda x: x['created_at'], reverse=True)
        completed.sort(key=lambda x: x.get('completed_at', x['created_at']), reverse=True)
        
        return pending + completed
    
    def add_message(self, msg_type, priority, title, content, created_by):
        """新增留言"""
        messages = self._load_messages()
        
        new_message = {
            'id': f"msg_{uuid.uuid4().hex[:8]}",
            'type': msg_type,  # todo, note, urgent
            'priority': priority,  # high, medium, low
            'title': title,
            'content': content,
            'created_by': created_by,
            'created_at': datetime.now().isoformat(),
            'completed': False,
            'completed_at': None
        }
        
        messages.append(new_message)
        
        if self._save_messages(messages):
            return new_message
        return None
    
    def toggle_complete(self, msg_id):
        """切換完成狀態"""
        messages = self._load_messages()
        
        for msg in messages:
            if msg['id'] == msg_id:
                msg['completed'] = not msg['completed']
                if msg['completed']:
                    msg['completed_at'] = datetime.now().isoformat()
                else:
                    msg['completed_at'] = None
                
                if self._save_messages(messages):
                    return msg
                return None
        
        return None
    
    def delete_message(self, msg_id):
        """刪除留言"""
        messages = self._load_messages()
        
        original_count = len(messages)
        messages = [m for m in messages if m['id'] != msg_id]
        
        if len(messages) < original_count:
            return self._save_messages(messages)
        
        return False
    
    def get_pending_count(self):
        """取得未完成數量"""
        messages = self._load_messages()
        return len([m for m in messages if not m.get('completed', False)])
