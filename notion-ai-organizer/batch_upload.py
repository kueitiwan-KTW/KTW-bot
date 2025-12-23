#!/usr/bin/env python3
"""
批量上傳腳本 - 智能整理所有專案檔案到 Notion

功能：
1. 掃描專案重要檔案
2. 匹配現有 Notion 頁面
3. 使用更新模式處理已存在的頁面
4. 創建新頁面處理新檔案
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from notion_client import Client
import time

# 載入環境變數
load_dotenv(Path(__file__).parent.parent / '.env')

NOTION_TOKEN = os.getenv('NOTION_TOKEN')
PARENT_PAGE_ID = '2c5c3f7d0f51809aadd0cad363f798a5'

notion = Client(auth=NOTION_TOKEN)

# 優先處理的檔案類型
PRIORITY_EXTENSIONS = ['.md', '.txt']

# 要排除的目錄
EXCLUDE_DIRS = [
    'node_modules', '__pycache__', '.git', 'venv', 'env',
    '.gemini', 'dist', 'build', '.pytest_cache'
]

def get_existing_notion_pages():
    """獲取現有 Notion 頁面的檔案名稱映射"""
    print('🔍 掃描現有 Notion 頁面...\n')
    
    children = notion.blocks.children.list(block_id=PARENT_PAGE_ID)
    pages = {}
    
    for block in children['results']:
        if block['type'] == 'child_page':
            page_id = block['id']
            page = notion.pages.retrieve(page_id=page_id)
            title = page['properties']['title']['title'][0]['plain_text'] if page['properties']['title']['title'] else ''
            
            # 讀取頁面內容，找來源檔案資訊
            blocks = notion.blocks.children.list(block_id=page_id)
            
            source_file = None
            for b in blocks['results'][:3]:
                if b['type'] == 'callout' and b['callout'].get('color') == 'gray_background':
                    text = b['callout']['rich_text'][0]['plain_text'] if b['callout']['rich_text'] else ''
                    if '路徑：' in text:
                        # 提取路徑
                        source_file = text.split('路徑：')[1].strip()
                        break
            
            if source_file:
                pages[source_file] = {
                    'page_id': page_id,
                    'title': title,
                    'url': page['url']
                }
    
    print(f'✅ 找到 {len(pages)} 個已有來源標記的頁面\n')
    return pages

def find_important_files(project_dir):
    """掃描專案重要檔案"""
    print(f'📂 掃描專案檔案：{project_dir}\n')
    
    important_files = []
    
    for root, dirs, files in os.walk(project_dir):
        # 排除目錄
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            # 優先處理文檔檔案
            if any(file.endswith(ext) for ext in PRIORITY_EXTENSIONS):
                file_path = os.path.join(root, file)
                
                # 排除太小的檔案
                if os.path.getsize(file_path) > 100:  # > 100 bytes
                    important_files.append(file_path)
    
    print(f'✅ 找到 {len(important_files)} 個重要檔案\n')
    return important_files

def batch_upload_files(files, existing_pages, limit=None):
    """批量上傳檔案"""
    from organize_and_upload import NotionAIOrganizer
    
    organizer = NotionAIOrganizer()
    
    # 分類檔案
    to_update = []
    to_create = []
    
    for file_path in files:
        if file_path in existing_pages:
            to_update.append((file_path, existing_pages[file_path]))
        else:
            to_create.append(file_path)
    
    print('=' * 80)
    print('📊 批量處理計劃')
    print('=' * 80)
    print(f'🔄 更新現有頁面：{len(to_update)} 個')
    print(f'➕ 創建新頁面：{len(to_create)} 個')
    print(f'📝 總計：{len(to_update) + len(to_create)} 個檔案')
    
    if limit:
        print(f'\n⚠️ 限制處理數量：{limit} 個\n')
    
    print('=' * 80 + '\n')
    
    # 處理更新
    if to_update:
        print('🔄 開始更新現有頁面...\n')
        
        for i, (file_path, page_info) in enumerate(to_update[:limit], 1):
            print(f'[{i}/{min(len(to_update), limit or len(to_update))}] 更新：{Path(file_path).name}')
            
            try:
                # 使用更新模式
                organizer.process_document(file_path, add_insights=True, mode='update')
                print(f'   ✅ 完成\n')
                time.sleep(2)  # 避免 API 速率限制
            except Exception as e:
                print(f'   ❌ 錯誤：{e}\n')
    
    # 處理新建
    remaining = (limit - len(to_update)) if limit else None
    
    if to_create and (remaining is None or remaining > 0):
        print('\n➕ 開始創建新頁面...\n')
        
        create_limit = remaining if remaining else len(to_create)
        
        for i, file_path in enumerate(to_create[:create_limit], 1):
            print(f'[{i}/{create_limit}] 創建：{Path(file_path).name}')
            
            try:
                # 使用新建模式
                organizer.process_document(file_path, add_insights=True, mode='new')
                print(f'   ✅ 完成\n')
                time.sleep(2)  # 避免 API 速率限制
            except Exception as e:
                print(f'   ❌ 錯誤：{e}\n')
    
    print('=' * 80)
    print('✅ 批量處理完成！')
    print('=' * 80)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='批量上傳專案檔案到 Notion')
    parser.add_argument('--project-dir', default='/Users/ktw/ktw-projects/KTW-bot', help='專案目錄')
    parser.add_argument('--limit', type=int, help='限制處理數量（測試用）')
    parser.add_argument('--dry-run', action='store_true', help='試運行（不實際上傳）')
    
    args = parser.parse_args()
    
    print('🚀 Notion 批量上傳工具\n')
    
    # 1. 獲取現有頁面
    existing_pages = get_existing_notion_pages()
    
    # 2. 掃描專案檔案
    important_files = find_important_files(args.project_dir)
    
    if args.dry_run:
        print('💡 試運行模式 - 不會實際上傳\n')
        
        # 分類統計
        to_update = [f for f in important_files if f in existing_pages]
        to_create = [f for f in important_files if f not in existing_pages]
        
        print(f'將更新：{len(to_update)} 個檔案')
        print(f'將創建：{len(to_create)} 個檔案')
        return
    
    # 3. 批量上傳
    batch_upload_files(important_files, existing_pages, limit=args.limit)

if __name__ == '__main__':
    main()
