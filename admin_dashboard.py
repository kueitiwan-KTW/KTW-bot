"""
旅館管理後台系統
功能：
1. 入住客人資料管理
2. Rich Menu 視覺化管理

啟動方式：python3 admin_dashboard.py
訪問：http://localhost:5002
"""

from flask import Flask, render_template, jsonify, request
from chat_logger import ChatLogger
from message_manager import MessageManager
from linebot import LineBotApi
from linebot.models import RichMenu, RichMenuSize, RichMenuBounds, RichMenuArea
from linebot.models import MessageAction, URIAction
import datetime
import os
import json

app = Flask(__name__)
logger = ChatLogger()
msg_manager = MessageManager()

# LINE Bot API 初始化
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
RICH_MENU_CONFIG_PATH = 'chat_logs/rich_menu_config.json'

line_bot_api = None
if LINE_CHANNEL_ACCESS_TOKEN:
    try:
        line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
        print("✅ LINE Bot API 初始化成功")
    except Exception as e:
        print(f"⚠️ LINE Bot API 初始化失敗: {e}")
else:
    print("⚠️ 未設定 LINE_CHANNEL_ACCESS_TOKEN")

@app.route('/')
def index():
    """首頁：顯示當天入住客人"""
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    checkins = logger.get_today_checkins()
    
    return render_template('today_checkins.html', 
                         checkins=checkins,
                         today=today,
                         count=len(checkins))

@app.route('/api/checkins/<date>')
def get_checkins_by_date(date):
    """API：查詢指定日期的入住客人"""
    checkins = logger.get_checkins_by_date(date)
    return jsonify(checkins)

@app.route('/api/order/<order_id>')
def get_order_detail(order_id):
    """API：查詢訂單詳情"""
    order = logger.get_order(order_id)
    if order:
        return jsonify(order)
    else:
        return jsonify({"error": "Order not found"}), 404

@app.route('/api/order/<order_id>/notes', methods=['POST'])
def update_notes(order_id):
    """API：更新訂單備註"""
    from flask import request
    data = request.get_json()
    notes = data.get('notes', '')
    
    success = logger.update_admin_notes(order_id, notes)
    if success:
        return jsonify({"status": "success", "message": "備註已儲存"})
    else:
        return jsonify({"status": "error", "message": "訂單不存在"}), 404


# ========================================
# Rich Menu 管理功能
# ========================================

@app.route('/rich-menu')
def rich_menu_manager():
    """Rich Menu 管理頁面"""
    return render_template('rich_menu_manager.html')

@app.route('/api/rich-menu/current')
def get_current_rich_menu():
    """API：取得當前的 Rich Menu 資訊"""
    if not line_bot_api:
        return jsonify({"error": "LINE Bot API 未初始化"}), 500
    
    try:
        # 讀取配置檔案
        if os.path.exists(RICH_MENU_CONFIG_PATH):
            with open(RICH_MENU_CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return jsonify(config)
        else:
            return jsonify({"status": "no_config", "message": "尚未建立 Rich Menu"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/rich-menu/upload', methods=['POST'])
def upload_rich_menu_image():
    """API：上傳 Rich Menu 背景圖片"""
    if not line_bot_api:
        return jsonify({"error": "LINE Bot API 未初始化"}), 500
    
    if 'image' not in request.files:
        return jsonify({"error": "未提供圖片檔案"}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "未選擇檔案"}), 400
    
    # 儲存檔案到暫存目錄
    upload_path = os.path.join('uploads', 'rich_menu_image.png')
    os.makedirs('uploads', exist_ok=True)
    file.save(upload_path)
    
    return jsonify({
        "status": "success",
        "message": "圖片上傳成功",
        "path": upload_path
    })

@app.route('/api/rich-menu/import-from-canva', methods=['POST'])
def import_from_canva():
    """API：從 Canva 分享連結匯入圖片"""
    if not line_bot_api:
        return jsonify({"error": "LINE Bot API 未初始化"}), 500
    
    try:
        data = request.get_json()
        canva_url = data.get('canva_url')
        
        if not canva_url:
            return jsonify({"error": "未提供 Canva 連結"}), 400
        
        # 提示：使用 Canva 商業版的建議流程
        return jsonify({
            "status": "info",
            "message": "💡 使用 Canva 商業版最佳流程：\n\n1️⃣ 在 Canva 設計完成後，點擊右上角「下載」\n2️⃣ 選擇 PNG 格式，2500x1686 尺寸\n3️⃣ 下載到電腦\n4️⃣ 回到本頁面，選擇「上傳下載的圖片檔案」\n5️⃣ 上傳剛下載的圖片即可\n\n✨ 提示：使用團隊模板可以確保尺寸正確且保持品牌一致性！",
            "suggestion": "請使用「上傳檔案」功能"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/rich-menu/create', methods=['POST'])
def create_rich_menu():
    """API：創建 Rich Menu"""
    if not line_bot_api:
        return jsonify({"error": "LINE Bot API 未初始化"}), 500
    
    try:
        data = request.get_json()
        areas_config = data.get('areas', [])
        image_path = data.get('image_path')
        
        # 建立 Rich Menu 區域
        areas = []
        for area_config in areas_config:
            action_type = area_config['action_type']
            if action_type == 'message':
                action = MessageAction(text=area_config['action_value'])
            elif action_type == 'uri':
                action = URIAction(uri=area_config['action_value'])
            else:
                continue
            
            areas.append(RichMenuArea(
                bounds=RichMenuBounds(
                    x=area_config['x'],
                    y=area_config['y'],
                    width=area_config['width'],
                    height=area_config['height']
                ),
                action=action
            ))
        
        # 建立 Rich Menu
        rich_menu = RichMenu(
            size=RichMenuSize(width=2500, height=1686),
            selected=True,
            name="龜地灣旅棧主選單",
            chat_bar_text="選單",
            areas=areas
        )
        
        # 創建 Rich Menu
        rich_menu_id = line_bot_api.create_rich_menu(rich_menu)
        
        # 上傳圖片（如果有提供）
        if image_path and os.path.exists(image_path):
            with open(image_path, 'rb') as f:
                line_bot_api.set_rich_menu_image(rich_menu_id, 'image/png', f)
        
        # 設定為預設 Rich Menu
        line_bot_api.set_default_rich_menu(rich_menu_id)
        
        # 儲存配置
        config = {
            "rich_menu_id": rich_menu_id,
            "created_at": datetime.datetime.now().isoformat(),
            "areas": areas_config
        }
        with open(RICH_MENU_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            "status": "success",
            "message": "Rich Menu 建立成功",
            "rich_menu_id": rich_menu_id
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/rich-menu/delete', methods=['POST'])
def delete_rich_menu():
    """API：刪除 Rich Menu"""
    if not line_bot_api:
        return jsonify({"error": "LINE Bot API 未初始化"}), 500
    
    try:
        data = request.get_json()
        rich_menu_id = data.get('rich_menu_id')
        
        if not rich_menu_id:
            return jsonify({"error": "未提供 Rich Menu ID"}), 400
        
        # 刪除 Rich Menu
        line_bot_api.delete_rich_menu(rich_menu_id)
        
        # 刪除配置檔案
        if os.path.exists(RICH_MENU_CONFIG_PATH):
            os.remove(RICH_MENU_CONFIG_PATH)
        
        return jsonify({
            "status": "success",
            "message": "Rich Menu 已刪除"
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ========================================
# 留言板 API
# ========================================

@app.route('/api/messages', methods=['GET'])
def get_messages():
    """API：取得所有留言"""
    try:
        messages = msg_manager.get_all_messages()
        pending_count = msg_manager.get_pending_count()
        return jsonify({
            'status': 'success',
            'messages': messages,
            'pending_count': pending_count
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/messages', methods=['POST'])
def add_message():
    """API：新增留言"""
    try:
        data = request.get_json()
        
        msg_type = data.get('type', 'todo')
        priority = data.get('priority', 'medium')
        title = data.get('title', '')
        content = data.get('content', '')
        created_by = data.get('created_by', '使用者')
        
        if not title:
            return jsonify({'error': '標題不能為空'}), 400
        
        new_message = msg_manager.add_message(
            msg_type, priority, title, content, created_by
        )
        
        if new_message:
            return jsonify({
                'status': 'success',
                'message': new_message
            })
        else:
            return jsonify({'error': '建立留言失敗'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/messages/<msg_id>/complete', methods=['PUT'])
def toggle_message_complete(msg_id):
    """API：切換留言完成狀態"""
    try:
        updated_message = msg_manager.toggle_complete(msg_id)
        
        if updated_message:
            return jsonify({
                'status': 'success',
                'message': updated_message
            })
        else:
            return jsonify({'error': '找不到該留言'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/messages/<msg_id>', methods=['DELETE'])
def delete_message(msg_id):
    """API：刪除留言"""
    try:
        success = msg_manager.delete_message(msg_id)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': '留言已刪除'
            })
        else:
            return jsonify({'error': '找不到該留言'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("🏨 旅館管理後台啟動中...")
    print("📍 訪問網址：http://localhost:5002")
    print("   - 入住管理：http://localhost:5002/")
    print("   - Rich Menu 管理：http://localhost:5002/rich-menu")
    print("⏹️  按 Ctrl+C 停止")
    app.run(host='0.0.0.0', port=5002, debug=True)
