#!/usr/bin/env python3
"""
LINE 對話記錄分析腳本
從 line_history_data 資料夾中抽樣並分析對話記錄
"""

import os
import csv
import json
import random
from collections import defaultdict, Counter
from pathlib import Path
from datetime import datetime

class LineConversationAnalyzer:
    def __init__(self, data_dir, sample_size=100):
        self.data_dir = Path(data_dir)
        self.sample_size = sample_size
        self.conversations = []
        self.qna_pairs = []
        self.stats = defaultdict(int)
        self.categories = defaultdict(list)
        
    def find_valid_files(self):
        """找出所有有效的 CSV 檔案 (>1KB)"""
        valid_files = []
        for csv_file in self.data_dir.glob("*.csv"):
            if csv_file.stat().st_size > 1024:  # >1KB
                valid_files.append(csv_file)
        return valid_files
    
    def sample_files(self, valid_files):
        """隨機抽樣指定數量的檔案"""
        if len(valid_files) <= self.sample_size:
            return valid_files
        return random.sample(valid_files, self.sample_size)
    
    def parse_csv(self, csv_file):
        """解析單一 CSV 檔案"""
        conversation = {
            'file': csv_file.name,
            'messages': [],
            'user_messages': [],
            'bot_messages': []
        }
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                # 跳過前 4 行標題
                for _ in range(4):
                    next(f)
                
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 5:
                        sender_type, sender_name, date, time, content = row[:5]
                        
                        message = {
                            'type': sender_type,
                            'sender': sender_name,
                            'datetime': f"{date} {time}",
                            'content': content.strip()
                        }
                        
                        conversation['messages'].append(message)
                        
                        if sender_type == 'User':
                            conversation['user_messages'].append(content.strip())
                        elif sender_type == 'Account':
                            conversation['bot_messages'].append(content.strip())
        
        except Exception as e:
            print(f"Error parsing {csv_file.name}: {e}")
            return None
        
        return conversation if conversation['messages'] else None
    
    def extract_qna_pairs(self, conversation):
        """從對話中提取問答對"""
        pairs = []
        messages = conversation['messages']
        
        for i in range(len(messages) - 1):
            if messages[i]['type'] == 'User' and messages[i+1]['type'] == 'Account':
                question = messages[i]['content']
                answer = messages[i+1]['content']
                
                # 過濾無意義的對話
                if self.is_valid_qna(question, answer):
                    pairs.append({
                        'question': question,
                        'answer': answer,
                        'source': conversation['file']
                    })
        
        return pairs
    
    def is_valid_qna(self, question, answer):
        """判斷問答對是否有效"""
        # 過濾條件
        invalid_keywords = ['照片已傳送', '貼圖已傳送', 'Unknown', '系統忙碌', '連線有點問題']
        
        if len(question) < 2 or len(answer) < 10:
            return False
        
        for keyword in invalid_keywords:
            if keyword in question or keyword in answer:
                return False
        
        return True
    
    def categorize_question(self, question):
        """分類問題類型"""
        categories = {
            '訂房查詢': ['訂單', '編號', '預訂', '訂房', '成功'],
            '天氣查詢': ['天氣', '氣溫', '下雨', '晴天'],
            '設施服務': ['停車', '早餐', 'wifi', '網路', 'check-in', 'check-out', '退房', '入住'],
            '位置交通': ['地址', '怎麼去', '車站', '交通', '導覽'],
            '房型價格': ['房型', '房間', '價格', '多少錢', '費用'],
            '一般問候': ['你好', '您好', '嗨', 'hi', 'hello'],
        }
        
        q_lower = question.lower()
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in q_lower:
                    return category
        
        return '其他'
    
    def analyze(self):
        """執行完整分析"""
        print("🔍 開始分析 LINE 對話記錄...")
        
        # 1. 找出有效檔案
        print("📁 搜尋有效檔案...")
        valid_files = self.find_valid_files()
        print(f"   找到 {len(valid_files)} 個有效檔案")
        
        # 2. 隨機抽樣
        print(f"🎲 隨機抽樣 {self.sample_size} 個檔案...")
        sampled_files = self.sample_files(valid_files)
        print(f"   抽樣完成：{len(sampled_files)} 個檔案")
        
        # 3. 解析對話
        print("📊 解析對話內容...")
        for i, csv_file in enumerate(sampled_files, 1):
            if i % 20 == 0:
                print(f"   進度：{i}/{len(sampled_files)}")
            
            conv = self.parse_csv(csv_file)
            if conv:
                self.conversations.append(conv)
                self.stats['total_messages'] += len(conv['messages'])
                self.stats['total_user_messages'] += len(conv['user_messages'])
                self.stats['total_bot_messages'] += len(conv['bot_messages'])
                
                # 提取問答對
                pairs = self.extract_qna_pairs(conv)
                self.qna_pairs.extend(pairs)
                
                # 分類統計
                for msg in conv['user_messages']:
                    category = self.categorize_question(msg)
                    self.categories[category].append(msg)
        
        self.stats['analyzed_files'] = len(self.conversations)
        self.stats['valid_qna_pairs'] = len(self.qna_pairs)
        
        print(f"✅ 分析完成！")
        print(f"   - 分析檔案：{self.stats['analyzed_files']}")
        print(f"   - 總訊息數：{self.stats['total_messages']}")
        print(f"   - 提取問答對：{self.stats['valid_qna_pairs']}")
    
    def generate_report(self, output_file):
        """產生 Markdown 分析報告"""
        report = []
        report.append("# LINE 對話記錄分析報告\n")
        report.append(f"**分析時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.append(f"**資料來源**: line_history_data 資料夾\n")
        report.append(f"**分析範圍**: {self.stats['analyzed_files']} 個對話檔案\n\n")
        
        # 統計摘要
        report.append("## 📊 統計摘要\n\n")
        report.append(f"- **總訊息數**: {self.stats['total_messages']:,}\n")
        report.append(f"- **客人訊息**: {self.stats['total_user_messages']:,}\n")
        report.append(f"- **Bot 回應**: {self.stats['total_bot_messages']:,}\n")
        report.append(f"- **有效問答對**: {self.stats['valid_qna_pairs']:,}\n")
        report.append(f"- **平均每對話訊息數**: {self.stats['total_messages'] / max(self.stats['analyzed_files'], 1):.1f}\n\n")
        
        # 問題分類統計
        report.append("## 📋 問題分類統計\n\n")
        report.append("| 類別 | 問題數量 | 佔比 |\n")
        report.append("|------|----------|------|\n")
        
        total_user_msgs = self.stats['total_user_messages']
        for category in sorted(self.categories.keys(), key=lambda x: len(self.categories[x]), reverse=True):
            count = len(self.categories[category])
            percentage = (count / total_user_msgs * 100) if total_user_msgs > 0 else 0
            report.append(f"| {category} | {count} | {percentage:.1f}% |\n")
        
        # 常見問題 TOP 30
        report.append("\n## 🔥 常見問題 TOP 30\n\n")
        user_questions = [msg for conv in self.conversations for msg in conv['user_messages']]
        question_counter = Counter(user_questions)
        
        for i, (question, count) in enumerate(question_counter.most_common(30), 1):
            if len(question) > 100:
                question = question[:97] + "..."
            report.append(f"{i}. **{question}** ({count} 次)\n")
        
        # 高品質問答對範例
        report.append("\n## 💎 高品質問答對範例 (前 20 組)\n\n")
        for i, pair in enumerate(self.qna_pairs[:20], 1):
            report.append(f"### {i}. Q: {pair['question']}\n\n")
            answer = pair['answer']
            if len(answer) > 300:
                answer = answer[:297] + "..."
            report.append(f"**A**: {answer}\n\n")
            report.append(f"*來源: {pair['source']}*\n\n")
            report.append("---\n\n")
        
        # 改進建議
        report.append("## 💡 改進建議\n\n")
        report.append("### 1. 知識庫擴充\n")
        report.append(f"- 已提取 {min(len(self.qna_pairs), 100)} 組高品質問答對\n")
        report.append("- 建議將這些問答對加入 knowledge_base.json\n\n")
        
        report.append("### 2. 常見問題優化\n")
        for category in ['訂房查詢', '天氣查詢', '設施服務']:
            if category in self.categories:
                report.append(f"- **{category}**: {len(self.categories[category])} 次提問，建議優化此類回應\n")
        
        # 寫入檔案
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(''.join(report))
        
        print(f"📝 報告已產生：{output_file}")
    
    def update_knowledge_base(self, kb_file, output_file):
        """更新知識庫"""
        # 讀取現有知識庫
        try:
            with open(kb_file, 'r', encoding='utf-8') as f:
                kb = json.load(f)
        except:
            kb = {}
        
        # 提取前 100 組高品質問答對
        new_entries = {}
        for i, pair in enumerate(self.qna_pairs[:100], 1):
            key = f"line_history_{i}"
            new_entries[key] = {
                "question": pair['question'],
                "answer": pair['answer'],
                "source": "LINE對話記錄分析",
                "date_added": datetime.now().strftime('%Y-%m-%d')
            }
        
        # 合併（不覆蓋現有資料）
        kb.update(new_entries)
        
        # 寫入新檔案
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(kb, f, ensure_ascii=False, indent=2)
        
        print(f"📚 知識庫已更新：{output_file}")
        print(f"   新增 {len(new_entries)} 組問答對")


if __name__ == "__main__":
    # 設定參數
    DATA_DIR = "line_history_data"
    SAMPLE_SIZE = 100
    OUTPUT_REPORT = "/Users/like/.gemini/antigravity/brain/e6f49f5c-d2d4-42f9-b533-a65c3916b997/line_chat_analysis.md"
    KB_FILE = "knowledge_base.json"
    KB_OUTPUT = "knowledge_base_updated.json"
    
    # 執行分析
    analyzer = LineConversationAnalyzer(DATA_DIR, SAMPLE_SIZE)
    analyzer.analyze()
    
    # 產生報告
    analyzer.generate_report(OUTPUT_REPORT)
    
    # 更新知識庫（產生新檔案，不直接覆蓋）
    analyzer.update_knowledge_base(KB_FILE, KB_OUTPUT)
    
    print("\n✅ 全部完成！")
