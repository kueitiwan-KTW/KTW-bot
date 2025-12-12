"""
Notion 指令系統 - 主程式

功能：
1. 掃描指定 Notion 頁面的留言
2. 解析用戶指令
3. 生成變更提案
4. 執行確認後的操作

使用方式：
    python3 notion_commander.py --scan                    # 掃描所有頁面
    python3 notion_commander.py --page-id=<id> --preview  # 預覽特定頁面的指令
    python3 notion_commander.py --execute --task-id=<id>  # 執行已批准的任務
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from notion_client import Client
import google.generativeai as genai
from datetime import datetime
import json

# 載入環境變數
load_dotenv(Path(__file__).parent.parent / '.env')

NOTION_TOKEN = os.getenv('NOTION_TOKEN')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
PARENT_PAGE_ID = '2c5c3f7d0f51809aadd0cad363f798a5'  # 您的 Notion 父頁面

# 初始化
notion = Client(auth=NOTION_TOKEN)
genai.configure(api_key=GOOGLE_API_KEY)


class NotionCommander:
    """Notion 指令執行器"""
    
    def __init__(self):
        self.notion = notion
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.pending_tasks = []
    
    def get_all_pages(self, parent_id=PARENT_PAGE_ID):
        """獲取所有子頁面"""
        print(f'🔍 掃描 Notion 頁面...\n')
        
        children = self.notion.blocks.children.list(block_id=parent_id)
        pages = []
        
        for block in children['results']:
            if block['type'] == 'child_page':
                page_id = block['id']
                page = self.notion.pages.retrieve(page_id=page_id)
                title = page['properties']['title']['title'][0]['plain_text'] if page['properties']['title']['title'] else 'Untitled'
                
                pages.append({
                    'id': page_id,
                    'title': title,
                    'url': page['url']
                })
        
        print(f'✅ 找到 {len(pages)} 個頁面\n')
        return pages
    
    def get_page_comments(self, page_id):
        """獲取頁面所有留言"""
        try:
            # Notion API: 獲取留言
            comments = self.notion.comments.list(block_id=page_id)
            
            parsed_comments = []
            for comment in comments.get('results', []):
                # 提取留言文本
                text = ''
                for rich_text in comment.get('rich_text', []):
                    text += rich_text.get('plain_text', '')
                
                if text.strip():
                    parsed_comments.append({
                        'id': comment['id'],
                        'text': text.strip(),
                        'created_time': comment.get('created_time'),
                        'created_by': comment.get('created_by', {}).get('id')
                    })
            
            return parsed_comments
        
        except Exception as e:
            print(f'⚠️ 讀取留言時發生錯誤：{e}')
            return []
    
    def scan_all_comments(self):
        """掃描所有頁面的留言"""
        pages = self.get_all_pages()
        
        results = []
        for page in pages:
            print(f'📄 掃描頁面：{page["title"]}')
            comments = self.get_page_comments(page['id'])
            
            if comments:
                print(f'   💬 找到 {len(comments)} 個留言')
                results.append({
                    'page': page,
                    'comments': comments
                })
            else:
                print(f'   📭 無留言')
        
        return results
    
    def parse_command(self, comment_text):
        """使用 AI 解析留言是否為指令"""
        prompt = f"""
你是一個指令解析器。請判斷以下用戶留言是否為可執行的指令。

用戶留言：
```
{comment_text}
```

請分析：
1. 這是否為一個明確的指令或請求？
2. 如果是，是什麼類型的指令？
3. 包含哪些具體資訊？

支援的指令類型：
- update_knowledge_base：更新知識庫（新增/修改/刪除 FAQ）
- modify_config：修改設定檔
- update_doc：更新文檔
- other：其他類型

請用 JSON 格式回覆：
{{
    "is_command": true/false,
    "command_type": "類型",
    "confidence": 0.0-1.0,
    "summary": "簡短說明",
    "details": {{
        // 根據指令類型的詳細資訊
    }}
}}

如果不是指令，is_command 設為 false。
"""
        
        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            # 清理 JSON
            import re
            cleaned = re.sub(r'```json\s*|\s*```', '', result_text)
            
            result = json.loads(cleaned)
            return result
        
        except Exception as e:
            print(f'⚠️ 解析指令時發生錯誤：{e}')
            return {'is_command': False, 'error': str(e)}
    
    def display_findings(self, scan_results):
        """顯示掃描結果"""
        print('\n' + '=' * 80)
        print('📊 掃描結果總覽')
        print('=' * 80 + '\n')
        
        total_pages = len(scan_results)
        total_comments = sum(len(r['comments']) for r in scan_results)
        
        print(f'📄 掃描頁面：{total_pages} 個')
        print(f'💬 總留言數：{total_comments} 個\n')
        
        if not scan_results:
            print('❌ 沒有找到任何留言\n')
            return
        
        # 分析每個留言
        commands_found = []
        
        for result in scan_results:
            page = result['page']
            comments = result['comments']
            
            print(f'📄 {page["title"]}')
            print(f'   🔗 {page["url"]}\n')
            
            for i, comment in enumerate(comments, 1):
                print(f'   💬 留言 {i}：')
                print(f'      {comment["text"][:100]}{"..." if len(comment["text"]) > 100 else ""}')
                
                # 解析是否為指令
                print(f'      🤖 分析中...')
                parsed = self.parse_command(comment['text'])
                
                if parsed.get('is_command'):
                    confidence = parsed.get('confidence', 0)
                    cmd_type = parsed.get('command_type', 'unknown')
                    summary = parsed.get('summary', '')
                    
                    print(f'      ✅ 識別為指令（信心度：{confidence:.0%}）')
                    print(f'      📝 類型：{cmd_type}')
                    print(f'      💡 {summary}')
                    
                    commands_found.append({
                        'page': page,
                        'comment': comment,
                        'parsed': parsed
                    })
                else:
                    print(f'      ℹ️ 非指令性留言')
                
                print()
        
        print('=' * 80)
        print(f'✅ 找到 {len(commands_found)} 個可執行指令\n')
        
        return commands_found


def main():
    """主程序"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Notion 指令系統')
    parser.add_argument('--scan', action='store_true', help='掃描所有頁面的留言')
    parser.add_argument('--page-id', help='指定要掃描的頁面 ID')
    parser.add_argument('--preview', action='store_true', help='預覽模式（不執行）')
    
    args = parser.parse_args()
    
    commander = NotionCommander()
    
    if args.scan or args.page_id:
        print('🚀 Notion 指令系統啟動\n')
        
        if args.page_id:
            # 掃描特定頁面
            print(f'🔍 掃描頁面：{args.page_id}\n')
            comments = commander.get_page_comments(args.page_id)
            
            if not comments:
                print('❌ 該頁面沒有留言\n')
                return
            
            scan_results = [{
                'page': {'id': args.page_id, 'title': '指定頁面', 'url': 'N/A'},
                'comments': comments
            }]
        else:
            # 掃描所有頁面
            scan_results = commander.scan_all_comments()
        
        # 顯示結果
        commands = commander.display_findings(scan_results)
        
        if commands and args.preview:
            print('💡 這是預覽模式，未執行任何操作')
            print('   使用 --execute 參數來執行指令\n')
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
