#!/usr/bin/env python3
"""
知識庫問答對過濾腳本
自動清理 knowledge_base_updated.json 中的低品質問答對
"""

import json
import re
from pathlib import Path

class KnowledgeBaseFilter:
    def __init__(self, input_file, output_file):
        self.input_file = input_file
        self.output_file = output_file
        self.stats = {
            'total': 0,
            'filtered_out': 0,
            'kept': 0,
            'reasons': {}
        }
        
        # 過濾規則
        self.filter_patterns = {
            '自動回應': [
                'AI自動回應訊息',
                '自動回覆系統',
                'Sorry ~ 很抱歉',
                '目前人員忙錄中',
                '敬請耐心等候客服人員',
                '歡迎您加入龜地灣旅棧官方ＬＩＮＥ',
                'moon big smile',
                'moon wink',
                'moon oops',
                'cony kiss'
            ],
            '包含姓名': [
                r'[A-Z][a-z]+\s*[A-Z][a-z]+',  # 英文姓名
                r'您好!',  # 通常後面接姓名
            ],
            '無意義內容': [
                '照片已傳送',
                '貼圖已傳送',
                '謝謝',
                '好的',
                '好',
                '了解',
                '嗯',
                'Ok',
                '是的',
                '對',
                '已取消通話'
            ],
            '訂單編號': [
                r'RMPGP\d+',
                r'\d{10}',  # 純數字訂單編號
            ]
        }
    
    def should_filter(self, question, answer):
        """判斷是否應該過濾掉此問答對"""
        
        # 1. 檢查問題長度
        if len(question) < 3:
            self._add_reason('問題太短')
            return True
        
        # 2. 檢查答案長度
        if len(answer) < 15:
            self._add_reason('答案太短')
            return True
        
        # 3. 檢查無意義內容
        for phrase in self.filter_patterns['無意義內容']:
            if question.strip() == phrase:
                self._add_reason('無意義問題')
                return True
        
        # 4. 檢查自動回應
        for phrase in self.filter_patterns['自動回應']:
            if phrase in answer:
                self._add_reason('自動回應制式訊息')
                return True
        
        # 5. 檢查是否包含訂單編號
        for pattern in self.filter_patterns['訂單編號']:
            if re.search(pattern, question) or re.search(pattern, answer):
                self._add_reason('包含訂單編號')
                return True
        
        # 6. 檢查是否包含特定姓名模式（排除常見詞彙）
        # 排除名單：Agoda, Line Pay 等
        exclude_names = ['Agoda', 'LINE', 'Line Pay', 'Check-in', 'Check-out', 'Wi-Fi', 'Wifi']
        for pattern in self.filter_patterns['包含姓名']:
            matches = re.findall(pattern, answer)
            for match in matches:
                if match not in exclude_names and match not in answer[:50]:  # 忽略開頭的稱呼
                    # 檢查是否在句首（如「林恩琪歡迎您」）
                    if re.search(r'^[^，。！？]+' + re.escape(match), answer):
                        self._add_reason('包含客人姓名')
                        return True
        
        # 7. 檢查是否為單純的訂單編號詢問
        if re.match(r'^[\d\-]+$', question.strip()):
            self._add_reason('純訂單編號')
            return True
        
        return False
    
    def _add_reason(self, reason):
        """記錄過濾原因"""
        self.stats['reasons'][reason] = self.stats['reasons'].get(reason, 0) + 1
    
    def is_high_value_qa(self, question, answer):
        """判斷是否為高價值問答對"""
        
        # 高價值指標
        high_value_keywords = [
            '請問', '想', '需要', '可以', '如何', '怎麼', '幾點', '多少',
            '有沒有', '是否', '能不能', '房價', '房型', '早餐', '停車',
            '訂房', '退房', '入住', '床型', '設施', '服務'
        ]
        
        # 檢查問題是否包含高價值關鍵詞
        for keyword in high_value_keywords:
            if keyword in question:
                return True
        
        # 檢查答案長度（詳細的答案通常更有價值）
        if len(answer) > 100 and '。' in answer:
            return True
        
        return False
    
    def clean_answer(self, answer):
        """清理答案中的個人化稱呼"""
        # 移除開頭的姓名稱呼（例如：「林恩琪您好」）
        answer = re.sub(r'^[^\s，。！？]{2,5}(您好|歡迎|Sorry)', r'\1', answer)
        answer = re.sub(r'^[^\s，。！？]{2,5}很高興', r'很高興', answer)
        
        return answer.strip()
    
    def filter_knowledge_base(self):
        """執行過濾"""
        print("🔍 開始過濾知識庫...")
        
        # 讀取檔案
        with open(self.input_file, 'r', encoding='utf-8') as f:
            kb = json.load(f)
        
        # 準備輸出結構
        filtered_kb = {
            'faq': kb['faq']  # 保留原有的 FAQ
        }
        
        # 過濾 line_history 項目
        kept_count = 0
        for key, value in kb.items():
            if key.startswith('line_history_'):
                self.stats['total'] += 1
                
                question = value['question']
                answer = value['answer']
                
                # 判斷是否過濾
                if self.should_filter(question, answer):
                    self.stats['filtered_out'] += 1
                    continue
                
                # 保留高價值問答對
                if self.is_high_value_qa(question, answer):
                    # 清理答案
                    cleaned_answer = self.clean_answer(answer)
                    
                    # 重新編號
                    kept_count += 1
                    new_key = f'line_history_{kept_count}'
                    filtered_kb[new_key] = {
                        'question': question,
                        'answer': cleaned_answer,
                        'source': value['source'],
                        'date_added': value['date_added']
                    }
                    self.stats['kept'] += 1
                else:
                    self.stats['filtered_out'] += 1
                    self._add_reason('低價值問答')
        
        # 寫入檔案
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(filtered_kb, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 過濾完成！")
        self.print_stats()
        
        return filtered_kb
    
    def print_stats(self):
        """輸出統計資訊"""
        print(f"\n📊 過濾統計:")
        print(f"  - 總問答對數: {self.stats['total']}")
        print(f"  - 保留: {self.stats['kept']} ({self.stats['kept']/max(self.stats['total'],1)*100:.1f}%)")
        print(f"  - 過濾: {self.stats['filtered_out']} ({self.stats['filtered_out']/max(self.stats['total'],1)*100:.1f}%)")
        
        print(f"\n📋 過濾原因統計:")
        for reason, count in sorted(self.stats['reasons'].items(), key=lambda x: x[1], reverse=True):
            print(f"  - {reason}: {count}")


if __name__ == "__main__":
    INPUT_FILE = "knowledge_base_updated.json"
    OUTPUT_FILE = "knowledge_base_filtered.json"
    
    print("=" * 60)
    print("知識庫問答對過濾腳本")
    print("=" * 60)
    
    # 執行過濾
    filter_tool = KnowledgeBaseFilter(INPUT_FILE, OUTPUT_FILE)
    filtered_kb = filter_tool.filter_knowledge_base()
    
    print(f"\n📁 輸出檔案: {OUTPUT_FILE}")
    print(f"📊 保留的 FAQ 數量: {len(filtered_kb['faq'])}")
    print(f"📊 保留的 LINE 對話問答: {sum(1 for k in filtered_kb if k.startswith('line_history_'))}")
    print(f"📊 總問答對數: {len(filtered_kb['faq']) + sum(1 for k in filtered_kb if k.startswith('line_history_'))}")
    
    print("\n✅ 完成！下一步：")
    print("   1. 檢視 knowledge_base_filtered.json")
    print("   2. 如果滿意，替換原有的 knowledge_base.json")
    print("   3. 重啟 Bot 套用新知識庫")
