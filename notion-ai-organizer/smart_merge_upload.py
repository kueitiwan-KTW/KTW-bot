#!/usr/bin/env python3
"""
智能合併批量上傳腳本

功能：
1. 識別同性質檔案（CHANGELOG、README 等）
2. 合併為單一 Notion 頁面
3. 清楚標註所有來源出處
4. 用視覺元素區分不同來源
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from collections import defaultdict

# 載入環境變數
load_dotenv(Path(__file__).parent.parent / '.env')

# 合併規則：同類型的檔案名稱
MERGE_GROUPS = {
    'CHANGELOG': ['CHANGELOG.md', 'CHANGELOG', 'changelog.md'],
    'README': ['README.md', 'README', 'readme.md'],
    'QUICKSTART': ['QUICKSTART.md', 'quickstart.md'],
    'DEPLOYMENT': ['DEPLOYMENT.md', 'DEPLOY.md', 'deployment.md'],
}

# 專案圖示映射
PROJECT_ICONS = {
    'KTW-bot': '🤖',
    'pms-api': '🔌',
    'pms-api-poc': '🔬',
    'notion-ai-organizer': '📄',
}

# 專案分類（目錄）
PROJECT_CATEGORIES = {
    'KTW-bot': 'Bot',
    'pms-api': 'PMS',
    'pms-api-poc': 'PMS',
    'notion-ai-organizer': '工具',
}

# 相關專案組：這些專案可以合併同類型檔案
RELATED_PROJECT_GROUPS = [
    ['pms-api', 'pms-api-poc'],  # PMS 相關專案
    # 未來可擴展：['bot-v1', 'bot-v2']
]

def are_projects_related(proj1, proj2):
    """檢查兩個專案是否相關"""
    if proj1 == proj2:
        return True
    
    for group in RELATED_PROJECT_GROUPS:
        if proj1 in group and proj2 in group:
            return True
    
    return False

def get_project_category(projects):
    """獲取專案組的分類標籤"""
    # 如果有多個專案，取第一個的分類
    if isinstance(projects, list) and projects:
        return PROJECT_CATEGORIES.get(projects[0], '其他')
    return PROJECT_CATEGORIES.get(projects, '其他')

def categorize_files(files):
    """
    智能分類檔案（三層策略）：
    1. 按專案和檔案類型分組
    2. 合併相關專案的同類型檔案
    3. 單一檔案獨立上傳
    """
    # 第一層：按專案和類型分組
    project_groups = defaultdict(lambda: defaultdict(list))
    standalone_files = []
    
    for file_path in files:
        path = Path(file_path)
        filename = path.name
        
        # 提取專案名稱
        project = get_project_name(file_path)
        
        # 檢查是否屬於可合併類型
        merged = False
        for group_name, patterns in MERGE_GROUPS.items():
            if filename in patterns:
                project_groups[project][group_name].append(file_path)
                merged = True
                break
        
        if not merged:
            standalone_files.append(file_path)
    
    # 第二層：合併相關專案
    final_groups = {}
    
    # 按文檔類型處理
    for doc_type in MERGE_GROUPS.keys():
        # 收集所有有此類型文檔的專案
        projects_with_type = {}
        for project, groups in project_groups.items():
            if doc_type in groups:
                projects_with_type[project] = groups[doc_type]
        
        # 合併相關專案
        processed_projects = set()
        
        for project in projects_with_type.keys():
            if project in processed_projects:
                continue
            
            # 找出所有相關專案
            related_files = list(projects_with_type[project])
            related_projects = [project]
            
            for other_project in projects_with_type.keys():
                if other_project != project and other_project not in processed_projects:
                    if are_projects_related(project, other_project):
                        related_files.extend(projects_with_type[other_project])
                        related_projects.append(other_project)
                        processed_projects.add(other_project)
            
            processed_projects.add(project)
            
            # 如果有多個檔案，創建合併組
            if len(related_files) > 1:
                # 組名：如果是相關專案，用第一個專案名 + "(含相關)"
                if len(related_projects) > 1:
                    group_key = f"{'_'.join(sorted(related_projects))}_{doc_type}"
                    display_name = f"{' + '.join(sorted(related_projects))}"
                else:
                    group_key = f"{project}_{doc_type}"
                    display_name = project
                
                # 獲取分類
                category = get_project_category(related_projects)
                
                final_groups[group_key] = {
                    'projects': related_projects,
                    'display_name': display_name,
                    'category': category,
                    'type': doc_type,
                    'files': related_files
                }
            else:
                # 單一檔案 → 獨立上傳
                standalone_files.extend(related_files)
    
    return final_groups, standalone_files

def get_project_name(file_path):
    """從路徑提取專案名稱"""
    parts = Path(file_path).parts
    
    # 找到 KTW-bot 後的第一個目錄
    try:
        ktw_index = parts.index('KTW-bot')
        if ktw_index + 1 < len(parts):
            project = parts[ktw_index + 1]
            return project if project in PROJECT_ICONS else 'KTW-bot'
    except ValueError:
        pass
    
    return 'KTW-bot'

def merge_documents(group_info):
    """
    合併多個文檔為一個內容
    
    參數：
        group_info: dict with 'projects', 'display_name', 'category', 'type', 'files'
    
    返回：合併後的 markdown 內容
    """
    display_name = group_info['display_name']
    doc_type = group_info['type']
    file_paths = group_info['files']
    projects = group_info['projects']
    category = group_info.get('category', '')
    
    print(f'🔗 合併 [{category}] {display_name} - {doc_type} ({len(file_paths)} 個檔案)...')
    
    # 標題 - 加上分類標籤
    if len(projects) > 1:
        icons = ' + '.join(PROJECT_ICONS.get(p, '📁') for p in sorted(projects))
        merged_content = f'# [{category}] {icons} {display_name} - {doc_type}\n\n'
    else:
        icon = PROJECT_ICONS.get(projects[0], '📁')
        merged_content = f'# [{category}] {icon} {display_name} - {doc_type}\n\n'
    
    # 來源檔案列表
    merged_content += '> 📌 **來源檔案**：\n'
    for fp in file_paths:
        merged_content += f'> - `{fp}`\n'
    merged_content += '\n---\n\n'
    
    # 逐個添加檔案內容
    for i, file_path in enumerate(file_paths, 1):
        project = get_project_name(file_path)
        icon = PROJECT_ICONS.get(project, '📁')
        
        print(f'   [{i}/{len(file_paths)}] 讀取：{Path(file_path).name} ({project})')
        
        # 讀取檔案內容
        try:
            # 嘗試多種編碼讀取
            content = None
            for encoding in ['utf-8', 'utf-8-sig', 'big5', 'gbk', 'latin-1']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except (UnicodeDecodeError, LookupError):
                    continue
            
            if content is None:
                raise ValueError(f'無法以任何編碼讀取檔案')
            
            # 清理控制字元（保留換行和tab）
            import re
            content = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', content)
            
            # 獲取檔案的最後修改時間（原檔案時間，非上傳時間）
            import os
            from datetime import datetime
            file_mtime = os.path.getmtime(file_path)
            file_time = datetime.fromtimestamp(file_mtime).strftime('%Y-%m-%d %H:%M:%S')
            
            # 添加子章節標題（含原檔案時間）
            merged_content += f'## {icon} {project} - {Path(file_path).name} ({file_time})\n\n'
            merged_content += f'> 📂 完整路徑：`{file_path}`\n'
            merged_content += f'> ⏰ 檔案修改時間：{file_time}\n\n'
            
            # 添加內容
            merged_content += content.strip() + '\n\n'
            
            # 分隔線（除了最後一個）
            if i < len(file_paths):
                merged_content += '---\n\n'
        
        except Exception as e:
            print(f'   ⚠️ 讀取錯誤：{e}')
            merged_content += f'> ⚠️ 無法讀取此檔案：{e}\n\n'
    
    return merged_content

def create_merged_page(merged_content, group_name):
    """創建合併後的 Notion 頁面"""
    from organize_and_upload import NotionAIOrganizer
    
    # 儲存為臨時檔案
    temp_file = f'/tmp/merged_{group_name}.md'
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(merged_content)
    
    print(f'📝 創建 Notion 頁面...')
    
    # 使用現有的上傳工具
    organizer = NotionAIOrganizer()
    
    try:
        # 上傳（含 AI 建議）
        organizer.process_document(temp_file, add_insights=True, mode='new')
        print(f'✅ 完成！\n')
        
        # 清理臨時檔案
        os.remove(temp_file)
        
    except Exception as e:
        print(f'❌ 錯誤：{e}\n')

def smart_batch_upload(limit=None):
    """智能批量上傳（專案分組 + 內容相關性）"""
    from batch_upload import find_important_files
    
    print('🚀 智能合併批量上傳（專案分組模式）\n')
    
    # 1. 掃描檔案
    files = find_important_files('/Users/ktw/KTW-bot')
    
    # 2. 智能分類檔案
    merged_groups, standalone_files = categorize_files(files)
    
    print('=' * 80)
    print('📊 上傳計劃（按專案分組）')
    print('=' * 80)
    
    total_merged_files = sum(len(g['files']) for g in merged_groups.values())
    print(f'🔗 合併上傳：{total_merged_files} 個檔案 → {len(merged_groups)} 個頁面\n')
    
    for group_key, group_info in merged_groups.items():
        display_name = group_info['display_name']
        doc_type = group_info['type']
        file_count = len(group_info['files'])
        projects = group_info['projects']
        
        if len(projects) > 1:
            icons = ' + '.join(PROJECT_ICONS.get(p, '📁') for p in sorted(projects))
            print(f'   {icons} {display_name} - {doc_type}: {file_count} 個檔案')
        else:
            icon = PROJECT_ICONS.get(projects[0], '📁')
            print(f'   {icon} {display_name} - {doc_type}: {file_count} 個檔案')
    
    print(f'\n📄 獨立上傳：{len(standalone_files)} 個檔案')
    
    if limit:
        print(f'\n⚠️ 限制處理：前 {limit} 個操作\n')
    
    print('=' * 80 + '\n')
    
    # 3. 處理合併檔案
    operations = 0
    
    if merged_groups:
        print('🔗 開始合併上傳...\n')
        
        for group_key, group_info in merged_groups.items():
            if limit and operations >= limit:
                break
            
            display_name = group_info['display_name']
            doc_type = group_info['type']
            projects = group_info['projects']
            
            if len(projects) > 1:
                icons = ' + '.join(PROJECT_ICONS.get(p, '📁') for p in sorted(projects))
                print(f'📦 處理 {icons} {display_name} - {doc_type}...')
            else:
                icon = PROJECT_ICONS.get(projects[0], '📁')
                print(f'📦 處理 {icon} {display_name} - {doc_type}...')
            
            # 合併內容
            merged_content = merge_documents(group_info)
            
            # 創建頁面
            create_merged_page(merged_content, group_key)
            
            operations += 1
    
    # 4. 處理獨立檔案（如果還有配額）
    if limit:
        remaining = limit - operations
    else:
        remaining = len(standalone_files)
    
    if standalone_files and remaining > 0:
        print(f'\n📄 開始獨立上傳（前 {remaining} 個）...\n')
        
        from organize_and_upload import NotionAIOrganizer
        organizer = NotionAIOrganizer()
        
        for i, file_path in enumerate(standalone_files[:remaining], 1):
            print(f'[{i}/{remaining}] 上傳：{Path(file_path).name}')
            
            try:
                organizer.process_document(file_path, add_insights=True, mode='new')
                print(f'   ✅ 完成\n')
            except Exception as e:
                print(f'   ❌ 錯誤：{e}\n')
    
    print('=' * 80)
    print('✅ 批量上傳完成！')
    print('=' * 80)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='智能合併批量上傳')
    parser.add_argument('--limit', type=int, help='限制處理數量')
    
    args = parser.parse_args()
    
    smart_batch_upload(limit=args.limit)

if __name__ == '__main__':
    main()
