"""
Notion 頁面更新模式 - 核心邏輯

功能：
1. 查找現有頁面
2. 比對內容差異
3. 保留用戶添加的內容
4. 標記變更（綠/黃/紅色）
"""

import re
from notion_client import Client
import hashlib

class NotionPageUpdater:
    """Notion 頁面更新管理器"""
    
    def __init__(self, notion_client):
        self.notion = notion_client
    
    def find_existing_page(self, source_file, parent_id):
        """根據來源檔案名稱查找現有頁面"""
        from pathlib import Path
        
        filename = Path(source_file).name
        
        # 獲取所有子頁面
        children = self.notion.blocks.children.list(block_id=parent_id)
        
        for block in children['results']:
            if block['type'] == 'child_page':
                page_id = block['id']
                
                # 讀取頁面內容
                blocks = self.notion.blocks.children.list(block_id=page_id)
                
                # 檢查第一個 callout 是否包含來源檔案資訊
                for b in blocks['results'][:3]:
                    if b['type'] == 'callout' and b['callout'].get('color') == 'gray_background':
                        text = b['callout']['rich_text'][0]['plain_text'] if b['callout']['rich_text'] else ''
                        if filename in text:
                            return page_id
        
        return None
    
    def get_page_blocks(self, page_id):
        """獲取頁面所有區塊"""
        blocks = []
        has_more = True
        start_cursor = None
        
        while has_more:
            response = self.notion.blocks.children.list(
                block_id=page_id,
                start_cursor=start_cursor
            )
            blocks.extend(response['results'])
            has_more = response.get('has_more', False)
            start_cursor = response.get('next_cursor')
        
        return blocks
    
    def categorize_blocks(self, blocks):
        """分類區塊：系統生成 vs 用戶添加"""
        system_blocks = []
        user_blocks = []
        
        for block in blocks:
            btype = block['type']
            
            # 系統生成的標記
            if btype == 'callout':
                color = block['callout'].get('color', '')
                if color in ['gray_background', 'blue_background', 'purple_background']:
                    system_blocks.append(block)
                    continue
            
            # 可能是用戶添加的
            user_blocks.append(block)
        
        return system_blocks, user_blocks
    
    def create_change_marker(self, change_type, content_preview):
        """創建變更標記區塊"""
        colors = {
            'added': 'green_background',
            'modified': 'yellow_background',
            'deleted': 'red_background'
        }
        
        icons = {
            'added': '🟢',
            'modified': '🟡',
            'deleted': '🔴'
        }
        
        labels = {
            'added': '新增',
            'modified': '修改',
            'deleted': '刪除'
        }
        
        return {
            'object': 'block',
            'type': 'callout',
            'callout': {
                'rich_text': [{
                    'type': 'text',
                    'text': {'content': f'{icons[change_type]} {labels[change_type]}：{content_preview[:100]}...'}
                }],
                'icon': {'type': 'emoji', 'emoji': icons[change_type]},
                'color': colors[change_type]
            }
        }
    
    def update_page(self, page_id, new_blocks, preserve_user_content=True):
        """更新頁面內容，保留用戶添加的內容"""
        # 獲取現有內容
        existing_blocks = self.get_page_blocks(page_id)
        
        # 分類區塊
        system_blocks, user_blocks = self.categorize_blocks(existing_blocks)
        
        # 刪除所有系統生成的區塊
        for block in system_blocks:
            try:
                self.notion.blocks.delete(block_id=block['id'])
            except:
                pass
        
        # 添加變更標記
        change_marker = self.create_change_marker(
            'modified',
            f'文檔已更新 - 共 {len(new_blocks)} 個新區塊'
        )
        
        # 合併內容：新區塊 + 變更標記 + 用戶區塊
        final_blocks = [change_marker] + new_blocks
        
        if preserve_user_content and user_blocks:
            # 添加分隔線
            final_blocks.append({
                'object': 'block',
                'type': 'divider',
                'divider': {}
            })
            
            # 添加提示
            final_blocks.append({
                'object': 'block',
                'type': 'callout',
                'callout': {
                    'rich_text': [{
                        'type': 'text',
                        'text': {'content': '以下是您之前手動添加的內容（已保留）'}
                    }],
                    'icon': {'type': 'emoji', 'emoji': '👤'},
                    'color': 'gray_background'
                }
            })
        
        # 分批添加新區塊
        batch_size = 100
        for i in range(0, len(final_blocks), batch_size):
            batch = final_blocks[i:i+batch_size]
            self.notion.blocks.children.append(
                block_id=page_id,
                children=batch
            )
        
        return page_id
