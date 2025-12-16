from chat_logger import ChatLogger
import os

def main():
    logger = ChatLogger()
    
    while True:
        print("\n=== 對話紀錄查看器 (Chat Log Viewer) ===")
        users = logger.list_users()
        
        if not users:
            print("目前沒有任何對話紀錄。")
            break
            
        print("請選擇要查看的使用者 (User ID):")
        for i, user in enumerate(users):
            # user is now a dict: {'id': '...', 'name': '...'}
            print(f"{i+1}. {user['name']} ({user['id']})")
        print("0. 離開 (Exit)")
        
        choice = input("請輸入編號: ")
        
        if choice == '0':
            break
            
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(users):
                user_id = users[idx]['id']
                user_name = users[idx]['name']
                print(f"\n--- {user_name} ({user_id}) 的對話紀錄 ---")
                print(logger.get_logs(user_id))
                input("\n按 Enter 返回選單...")
            else:
                print("無效的編號")
        except ValueError:
            print("請輸入數字")

if __name__ == "__main__":
    main()
