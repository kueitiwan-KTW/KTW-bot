"""
Notion AI 文檔整理助手 - GPT 版本

使用 OpenAI GPT-4 進行文檔分析與優化
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from notion_client import Client
from openai import OpenAI
import re
import json

# 載入環境變數
load_dotenv(Path(__file__).parent.parent / '.env')

NOTION_TOKEN = os.getenv('NOTION_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
PARENT_PAGE_ID = os.getenv('NOTION_PARENT_PAGE_ID', '2c5c3f7d0f51809aadd0cad363f798a5')

# 初始化
notion = Client(auth=NOTION_TOKEN)
openai_client = OpenAI(api_key=OPENAI_API_KEY)


class NotionGPTOrganizer:
    """使用 GPT-4 的 Notion 文檔整理器"""
    
    def __init__(self):
        self.client = openai_client
        print('🤖 使用 AI：GPT-4o（完整版）')
    
    def read_markdown(self, file_path):
        """讀取 Markdown 文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def analyze_and_optimize(self, content, add_ai_insights=True):
        """使用 GPT-4 分析並優化文檔"""
        
        insights_instruction = ""
        if add_ai_insights:
            insights_instruction = """
5. **添加 AI 建議與洞察**（重要！）：
   - 在適當位置添加 AI 的分析、建議或補充說明
   - 每個建議必須用特殊格式標記：
     {{"type": "callout", "icon": "🤖", "color": "purple_background", "content": "💡 AI 建議：[你的建議內容]"}}
   - 建議類型：
     * 最佳實踐建議
     * 潛在風險提醒
     * 優化建議
     * 相關知識補充
     * 實作注意事項
   - 原則：簡潔扼要，每個建議不超過 3 句話
"""
        
        prompt = f"""
你是一個專業的技術文檔編輯器 + 技術顧問。請將以下 Markdown 文檔轉換為結構化的 Notion 格式。

⚠️ 重要原則：
1. **保留所有原始內容** - 不要刪減任何段落、列表或細節
2. **保持完整性** - 所有版本號、日期、功能說明都要完整保留
3. **優化格式** - 添加適當的視覺元素（emoji、callout）但不改變內容
4. **原文與 AI 建議分離** - 用特殊顏色標記 AI 添加的內容

任務：
1. 提取文檔標題
2. 生成一個簡短摘要（2-3 句話）
3. 提取 3-5 個關鍵字
4. **完整轉換**所有內容為 Notion blocks，包括：
   - 所有標題（H1-H6）
   - 所有段落（完整保留）
   - 所有列表項目
   - 所有代碼塊
   - 重要提示用 callout 標記
{insights_instruction}

請用 JSON 格式回覆（sections 必須包含**所有**原始內容 + AI 建議）：
{{
  "title": "文檔標題",
  "summary": "簡短摘要",
  "keywords": ["關鍵字1", "關鍵字2"],
  "sections": [
    {{"type": "heading_1", "content": "完整標題"}},
    {{"type": "heading_2", "content": "子標題"}},
    {{"type": "paragraph", "content": "完整段落內容"}},
    
    // AI 建議必須用這個格式（紫色背景 + 🤖 圖示）
    {{"type": "callout", "icon": "🤖", "color": "purple_background", "content": "💡 AI 建議：這裡建議使用 XXX 方法，因為..."}},
    
    {{"type": "bulleted_list_item", "content": "列表項目"}},
    {{"type": "code", "language": "python", "content": "代碼內容"}},
    {{"type": "callout", "icon": "⚠️", "color": "yellow_background", "content": "重要提示"}}
  ]
}}

原始 Markdown 文檔：
```markdown
{content}
```

請確保：
1. sections 陣列包含文檔的**每一行內容**
2. AI 建議用紫色 callout + 🤖 圖示標記
3. AI 建議簡潔有用，每個 2-3 句話
"""
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "你是一個專業的技術文檔編輯器和技術顧問。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        return response.choices[0].message.content
    
    def create_notion_page(self, analysis_result, parent_id=PARENT_PAGE_ID):
        """根據分析結果創建 Notion 頁面"""
        # 解析 JSON
        data = json.loads(analysis_result)
        
        # 創建頁面標題加上 GPT 標記
        page_title = f"{data['title']} (GPT-4o)"
        
        # 創建頁面
        page = notion.pages.create(
            parent={'page_id': parent_id},
            icon={'type': 'emoji', 'emoji': '🤖'},
            properties={
                'title': {
                    'title': [{
                        'type': 'text',
                        'text': {'content': page_title}
                    }]
                }
            }
        )
        
        # 準備內容區塊
        blocks = []
        
        # 添加摘要
        blocks.append({
            'object': 'block',
            'type': 'callout',
            'callout': {
                'rich_text': [{
                    'type': 'text',
                    'text': {'content': f"摘要：{data['summary']}"}
                }],
                'icon': {'type': 'emoji', 'emoji': '📋'},
                'color': 'blue_background'
            }
        })
        
        # 添加關鍵字
        keywords_text = '、'.join(data['keywords'])
        blocks.append({
            'object': 'block',
            'type': 'paragraph',
            'paragraph': {
                'rich_text': [{
                    'type': 'text',
                    'text': {'content': f'🏷️ 關鍵字：{keywords_text}'}
                }]
            }
        })
        
        blocks.append({
            'object': 'block',
            'type': 'divider',
            'divider': {}
        })
        
        # 添加主要內容
        for section in data['sections']:
            block = self._create_block(section)
            if block:
                blocks.append(block)
        
        # 分批添加區塊
        batch_size = 100
        for i in range(0, len(blocks), batch_size):
            batch = blocks[i:i+batch_size]
            notion.blocks.children.append(
                block_id=page['id'],
                children=batch
            )
        
        return page
    
    def _create_block(self, section):
        """根據 section 類型創建對應的 Notion block"""
        block_type = section['type']
        content = section['content']
        
        if block_type == 'heading_1':
            return {
                'object': 'block',
                'type': 'heading_1',
                'heading_1': {
                    'rich_text': [{'type': 'text', 'text': {'content': content}}]
                }
            }
        elif block_type == 'heading_2':
            return {
                'object': 'block',
                'type': 'heading_2',
                'heading_2': {
                    'rich_text': [{'type': 'text', 'text': {'content': content}}]
                }
            }
        elif block_type == 'heading_3':
            return {
                'object': 'block',
                'type': 'heading_3',
                'heading_3': {
                    'rich_text': [{'type': 'text', 'text': {'content': content}}]
                }
            }
        elif block_type == 'paragraph':
            return {
                'object': 'block',
                'type': 'paragraph',
                'paragraph': {
                    'rich_text': [{'type': 'text', 'text': {'content': content}}]
                }
            }
        elif block_type == 'callout':
            return {
                'object': 'block',
                'type': 'callout',
                'callout': {
                    'rich_text': [{'type': 'text', 'text': {'content': content}}],
                    'icon': {'type': 'emoji', 'emoji': section.get('icon', '💡')},
                    'color': section.get('color', 'yellow_background')
                }
            }
        elif block_type == 'code':
            return {
                'object': 'block',
                'type': 'code',
                'code': {
                    'rich_text': [{'type': 'text', 'text': {'content': content}}],
                    'language': section.get('language', 'plain text')
                }
            }
        elif block_type == 'bulleted_list_item':
            return {
                'object': 'block',
                'type': 'bulleted_list_item',
                'bulleted_list_item': {
                    'rich_text': [{'type': 'text', 'text': {'content': content}}]
                }
            }
        
        return None
    
    def process_document(self, file_path, add_insights=True):
        """完整的文檔處理流程"""
        print(f'📖 讀取文檔: {file_path}')
        content = self.read_markdown(file_path)
        
        insights_text = '（含 AI 建議）' if add_insights else ''
        print(f'🤖 GPT-4 分析與優化中{insights_text}...')
        analysis = self.analyze_and_optimize(content, add_ai_insights=add_insights)
        
        print('📝 創建 Notion 頁面...')
        page = self.create_notion_page(analysis)
        
        print(f'✅ 完成！')
        if add_insights:
            print(f'💡 已添加 GPT-4 AI 建議（紫色標記 🤖）')
        print(f'🔗 頁面連結: {page["url"]}')
        
        return page


def main():
    """主程序"""
    if len(sys.argv) < 2:
        print('使用方式: python organize_and_upload_gpt.py <文檔路徑> [--no-insights]')
        print('\n範例:')
        print('  python organize_and_upload_gpt.py ../CHANGELOG.md')
        sys.exit(1)
    
    file_path = sys.argv[1]
    add_insights = '--no-insights' not in sys.argv
    
    if not os.path.exists(file_path):
        print(f'❌ 文件不存在: {file_path}')
        sys.exit(1)
    
    organizer = NotionGPTOrganizer()
    organizer.process_document(file_path, add_insights=add_insights)


if __name__ == '__main__':
    main()
