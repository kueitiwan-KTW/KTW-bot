import json
import os

KB_PATH = "knowledge_base.json"

def load_kb():
    if not os.path.exists(KB_PATH):
        return {"faq": []}
    with open(KB_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_kb(data):
    with open(KB_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("知識庫已更新！(Knowledge Base Updated)")

def add_question():
    print("\n--- 新增問答 (Add New Q&A) ---")
    question = input("請輸入常見問題 (Question): ")
    answer = input("請輸入標準回答 (Answer): ")
    keywords_str = input("請輸入關鍵字 (用逗號分隔) (Keywords): ")
    keywords = [k.strip() for k in keywords_str.split(",") if k.strip()]

    data = load_kb()
    new_entry = {
        "keywords": keywords,
        "question": question,
        "answer": answer
    }
    data["faq"].append(new_entry)
    save_kb(data)

def list_questions():
    data = load_kb()
    print(f"\n--- 目前共有 {len(data['faq'])} 條問答 ---")
    for i, item in enumerate(data['faq']):
        print(f"[{i+1}] Q: {item['question']}")
        print(f"    A: {item['answer']}")
        print(f"    Keys: {item['keywords']}")

def modify_question():
    list_questions()
    data = load_kb()
    try:
        idx = int(input("\n請輸入要修改的編號 (Enter ID to modify): ")) - 1
        if 0 <= idx < len(data['faq']):
            item = data['faq'][idx]
            print(f"\n正在修改: {item['question']}")
            
            new_q = input(f"新問題 (Enter不修改): ")
            if new_q.strip(): item['question'] = new_q
            
            new_a = input(f"新回答 (Enter不修改): ")
            if new_a.strip(): item['answer'] = new_a
            
            new_k = input(f"新關鍵字 (Enter不修改): ")
            if new_k.strip(): 
                item['keywords'] = [k.strip() for k in new_k.split(",") if k.strip()]
            
            save_kb(data)
        else:
            print("無效的編號")
    except ValueError:
        print("請輸入數字")

def delete_question():
    list_questions()
    data = load_kb()
    try:
        idx = int(input("\n請輸入要刪除的編號 (Enter ID to delete): ")) - 1
        if 0 <= idx < len(data['faq']):
            confirm = input(f"確定要刪除 '{data['faq'][idx]['question']}' 嗎？(y/n): ")
            if confirm.lower() == 'y':
                del data['faq'][idx]
                save_kb(data)
        else:
            print("無效的編號")
    except ValueError:
        print("請輸入數字")

def main():
    while True:
        print("\n=== 旅館機器人訓練後台 (Bot Training Console) ===")
        print("1. 新增問答 (Add Q&A)")
        print("2. 查看所有 (List All)")
        print("3. 修改問答 (Modify)")
        print("4. 刪除問答 (Delete)")
        print("5. 離開 (Exit)")
        
        choice = input("請選擇功能 (1-5): ")
        
        if choice == '1':
            add_question()
        elif choice == '2':
            list_questions()
        elif choice == '3':
            modify_question()
        elif choice == '4':
            delete_question()
        elif choice == '5':
            break
        else:
            print("無效的選擇 (Invalid choice)")

if __name__ == "__main__":
    main()
