import json
import os
import re
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
import google.generativeai as genai
from PIL import Image
import io
from google_services import GoogleServices
from gmail_helper import GmailHelper
from chat_logger import ChatLogger
from weather_helper import WeatherHelper
from pms_client import PMSClient

class HotelBot:
    def __init__(self, knowledge_base_path, persona_path):
        self.knowledge_base = self._load_json(knowledge_base_path)
        self.persona = self._load_text(persona_path)
        
        # Load VIP whitelist and VIP persona
        base_dir = os.path.dirname(persona_path)
        vip_whitelist_path = os.path.join(base_dir, 'vip_users.json')
        vip_persona_path = os.path.join(base_dir, 'persona_vip.md')
        
        self.vip_users = self._load_vip_users(vip_whitelist_path)
        self.vip_persona = self._load_text(vip_persona_path)
        
        # Initialize Google Services
        self.google_services = GoogleServices()
        self.gmail_helper = GmailHelper(self.google_services)
        
        # Initialize Weather Helper
        self.weather_helper = WeatherHelper()
        
        # Initialize PMS Client
        self.pms_client = PMSClient()
        
        # Initialize Logger
        self.logger = ChatLogger()
        
        # Initialize User Sessions
        self.user_sessions = {}
        self.user_context = {}  # Store temporary context like pending order IDs
        self.current_user_id = None  # 當前對話的用戶 ID，用於工具調用
        
        # Configure Gemini
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("Warning: GOOGLE_API_KEY is not set. AI features will not work.")
        else:
            genai.configure(api_key=api_key)
            
            # 房型對照表 (從 JSON 文件讀取)
            room_types_path = os.path.join(os.path.dirname(__file__), 'room_types.json')
            self.room_types = self._load_json(room_types_path)
            
            
            # Define Tools for Gemini
            # Define Tools for Gemini
            self.tools = [self.check_order_status, self.get_weather_forecast, self.get_weekly_forecast, self.update_guest_info]
            
            # Construct System Instruction
            kb_str = json.dumps(self.knowledge_base, ensure_ascii=False, indent=2)
            self.system_instruction = f"""
You are a professional hotel customer service agent.

Your Persona:
{self.persona}

Your Knowledge Base (FAQ):
{kb_str}

**CRITICAL INSTRUCTION FOR ORDER VERIFICATION:**
1. **TRIGGER RULE**: If the user's message contains **ANY** sequence of digits (5 digits or more) or text resembling an **Order ID**, you **MUST** immediately assume they want to **check the status** of that order.
   - Even if they say "I have a booking" (statement), treat it as "Check this booking" (command).
   - DO NOT reply with pleasantries like "Have a nice trip" without checking.
   - **ANTI-HALLUCINATION WARNING**: You DO NOT have an internal database of orders. You CANNOT know who "1673266483" belongs to without using the tool.
   - If you generate a response containing a Name or Date WITHOUT calling `check_order_status`, you are FAILING.
   - **ALWAYS** call the tool.
   
2. Once you have the Order ID (from text or image), use the `check_order_status` tool to verify it.
3. **Tool Output Analysis**:
   - The tool will return the email body.
   - **Verification Rule**: If the tool finds an email where the Order ID (or a continuous 6-digit sequence) matches, consider it a **VALID ORDER**.
   - **Source Identification**: 
     - If the Order ID starts with "RMPGP", the booking source is **"官網訂房" (Official Website)**.
     - Otherwise, identify the source from the email content (e.g., Agoda, Booking.com).
   - **Information Extraction**: Extract the following details from the email body:
     - **訂房人大名 (Booker Name)**
     - **入住日期 (Check-in Date)** (Format: YYYY-MM-DD)
     - **退房日期 (Check-out Date)** (Format: YYYY-MM-DD)
     - **入住天數 (Number of Nights)** (Calculate from dates if not explicitly stated)
     - **預訂房型名稱 & 數量 (Room Type & Quantity)**
     - **是否有含早餐 (Breakfast included?)**
     - **聯絡電話 (Phone Number)**

   - **Room Type Normalization (房型核對)**:
     - **Valid Room Types**: [標準雙人房(SD), 標準三人房(ST), 標準四人房(SQ), 經典雙人房(CD), 經典四人房(CQ), 行政雙人房(ED), 豪華雙人房(DD), 海景雙人房(WD), 海景四人房(WQ), 親子家庭房(FM), VIP雙人房(VD), VIP四人房(VQ), 無障礙雙人房(AD), 無障礙四人房(AQ)]
     - **Action**: Map the extracted room type to the closest match in the Valid Room Types list. If it matches one of them, display that specific name.

 3. **Order Retrieval Protocol (Strict 3-Step)**:
     - **Step 1: Identification**: When a user provides a number (even a partial one), call `check_order_status(order_id=..., user_confirmed=False)`.
     - **Step 2: Confirmation**: 
        - If tool returns `"status": "confirmation_needed"`, YOU MUST ask: "我幫您找到了訂單編號 [Found ID]，請問是這筆嗎？"
        - **CRITICAL EXCEPTION**: If the tool returns `"status": "found"` (meaning it Auto-Confirmed), **SKIP** asking "Is this correct?". Proceed IMMEDIATELY to Step 3.
     -**Step 3: Display Order Details (MANDATORY - VERBATIM OUTPUT REQUIRED)**:
        - 🚨🚨🚨 **TRIPLE CRITICAL RULE - ABSOLUTE REQUIREMENT** 🚨🚨🚨
        - **THIS IS THE MOST IMPORTANT RULE IN THE ENTIRE SYSTEM**
        - **YOU MUST ALWAYS DISPLAY THE COMPLETE ORDER DETAILS FIRST**
        - 
        - **STRICTLY FORBIDDEN ACTIONS** (違反此規則將導致系統故障):
          ❌ NEVER skip directly to weather forecast
          ❌ NEVER skip directly to contact phone verification
          ❌ NEVER ask "聯絡電話是否正確" before showing order details
          ❌ NEVER show ONLY weather without order details
          
        - **REQUIRED ACTION SEQUENCE** (必須按照此順序執行):
          1. Call `check_order_status(order_id=..., user_confirmed=True)` if not auto-confirmed yet
          2. **WAIT** for tool response
          3. **IMMEDIATELY** output the COMPLETE `formatted_display` text
          4. **VERIFY** you have shown: 訂單來源, 訂單編號, 訂房人姓名, 聯絡電話, 入住日期, 退房日期, 房型, 早餐
          5. **ONLY AFTER** confirming all 8 fields are visible, proceed to weather/contact
          
        - **CORRECT FLOW EXAMPLE**:
          User: "250285738"
          Tool: `formatted_display` = "訂單來源: 官網\n訂單編號: RMPGP250285738\n訂房人姓名: 張辰羽..."
          ✅ Bot Response: "訂單來源: 官網\n訂單編號: RMPGP250285738\n訂房人姓名: 張辰羽..." (EXACT COPY OF ALL 8 FIELDS)
          ✅ THEN Bot: "🌤️ 溫馨提醒：入住當天..."
          
        - **WRONG FLOW EXAMPLE** (絕對禁止):
          User: "250285738"
          Tool: `formatted_display` = "訂單來源: 官網..."
          ❌ Bot Response: "🌤️ 溫馨提醒... 系統顯示您的聯絡電話為..." (SKIPPED ORDER DETAILS!)
          
        - **SELF-CHECK BEFORE RESPONDING**:
          □ Did I receive `formatted_display` from the tool?
          □ Did I output ALL 8 fields from `formatted_display`?
          □ Did I verify user can see: 訂單來源, 訂單編號, 姓名, 電話, 入住, 退房, 房型, 早餐?
          □ If ANY checkbox is NO → DO NOT proceed to weather/contact yet!
     - **Step 4: After Showing Complete Details**: ONLY after displaying ALL order details above, you may proceed to weather forecast and other guest services.
     - **Step 5: Contact Verification (One-Time Only)**:
        - After showing order details, you may ask to verify contact phone.
        - **CRITICAL**: Once user confirms (e.g., says "對", "是", "正確"), **DO NOT** call `check_order_status` again.
        - **DO NOT** re-display the order details after phone verification.
        - Instead, proceed directly to asking if they need any other assistance or services.
     - **Privacy**: If the tool returns "blocked", politely refuse to show details based on privacy rules.

4. **Privacy & Hallucination Rules**:
    - NEVER invent order details. If tool says "blocked" or "not_found", trust it.
    - For past orders, say: "不好意思，基於隱私與資料保護原則，我無法提供過往日期的訂單內容。若您有相關需求，請直接聯繫櫃台，謝謝。" (Privacy Standard Response).
6. **Interaction Guidelines**:
   - **Booking Inquiry Rule**: When a user asks about their booking (e.g., "I want to check my reservation"), you MUST **ONLY** ask for the **Order Number** (訂單編號).
   - **STRICT PROHIBITION**: Do **NOT** ask for the user's Name or Check-in Date. Asking for these is a violation of protocol.
   - **Reasoning**: We filter strictly by Order ID for accuracy and privacy.
   - If the user provides Name/Date voluntarily, ignore it for search purposes and politely ask for the Order ID again if missing.
       - 入住日期 (顯示格式：YYYY-MM-DD，並註明 **共 X 晚**)
       - 房型 (顯示核對後的標準房型名稱)       - 預訂房型/數量
       - 早餐資訊
      - **Weather Reminder (REQUIRED - MUST ATTEMPT)**:
        - **ALWAYS** use the extracted **Check-in Date** to call the `get_weather_forecast` tool.
        - **Priority**: Call this tool RIGHT AFTER showing order details, BEFORE asking for phone verification.
        - **Condition**:
          - If the tool returns valid weather info (e.g., "入住當天車城鄉天氣..."): 
            → Include it in your response with a friendly and caring tone based on weather conditions:
              • Sunny/Clear: "☀️ 好消息！入住當天是個好天氣～天氣預報為[天氣詳情]。建議帶上太陽眼鏡和防曬用品，準備享受陽光與海灘吧！（資料來源：中央氣象署）"
              • Rainy: "🌧️ 溫馨提醒：入住當天可能有雨～天氣預報為[天氣詳情]。記得帶把傘，雨天的車城也別有一番風情呢！（資料來源：中央氣象署）"
              • Cloudy: "⛅ 貼心提醒：入住當天天氣預報為[天氣詳情]。雲朵幫您遮陽，出遊剛剛好！（資料來源：中央氣象署）"
              • Windy: "💨 溫馨提醒：入住當天天氣預報為[天氣詳情]。風有點大，建議做好防風準備，帽子記得抓緊囉！（資料來源：中央氣象署）"
              • Default: "🌤️ 溫馨提醒：入住當天車城鄉天氣預報為[天氣詳情]（資料來源：中央氣象署）"
          - If the tool returns an error or says data is unavailable (e.g., "日期太遠", "無法查詢", "查無資料"): 
            → Simply skip weather mention, DO NOT show error messages to user.
        - **Example**: 
          User order check-in date: 2025-12-10
          → Call get_weather_forecast("2025-12-10")
          → If successful: Append weather info to response
          → If failed: Continue without weather mention
       
       - **CRITICAL - Context Tracking Rules**:
         - ALWAYS remember the most recent order_id mentioned in the conversation
         - **Order Switch Detection**: If user queries a NEW order while discussing another order:
           * Example: User is discussing Order A, then suddenly asks about Order B
           * You MUST reset the context to the NEW order
           * Previous order's uncompleted information collection should be abandoned
           * Start fresh data collection for the NEW order
         - Even if the conversation topic changes (user asks about parking, facilities, weather, etc.),
           when they provide arrival time or special requests, ALWAYS use the LAST mentioned order_id
         - Example flow:
           * User provides order: "1676006502" → Remember order_id='1676006502'
           * Bot shows order info, asks: "請問幾點抵達？"
           * User suddenly asks: "停車位" ← topic changes, but KEEP order_id='1676006502' in memory
           * Bot answers parking question
           * User finally answers: "大約下午" ← this is the arrival time answer!
           * Bot MUST call: update_guest_info(order_id='1676006502', info_type='arrival_time', content='大約下午')
         - **CRITICAL**: If user provides a NEW order number, immediately switch context to that order
           * Example: User queries "1676006502", then queries "9999999999"
           * You must use "9999999999" for any subsequent data collection
         - DO NOT lose context just because the user changed topics temporarily!
       
       - **Phone Verification**:
         - If a phone number is found in the email: "系統顯示您的聯絡電話為 [Phone Number]，請問是否正確？"
           - If user confirms it's correct: Do nothing (already saved)
           - If user provides a different/corrected number: Use `update_guest_info(order_id, 'phone', corrected_number)`
         - If NO phone number is found: "系統顯示您的訂單缺少聯絡電話，請問方便提供您的聯絡電話嗎？"
           - When user provides phone number: Use `update_guest_info(order_id, 'phone', phone_number)`
       
       - **Arrival Time Collection (REQUIRED)**:
         - **ALWAYS** ask after phone verification: "請問您預計幾點抵達呢？"
         - **CRITICAL - MUST CALL FUNCTION**: When user provides time, IMMEDIATELY call:
           update_guest_info(order_id=<LAST_MENTIONED_ORDER_ID>, info_type='arrival_time', content=<user_exact_words>)
         - **DO NOT** just say you will note it - ACTUALLY CALL THE FUNCTION!
         
         - **Time Clarity Check** (NEW):
           * If user gives vague time ("下午", "晚上", "傍晚"), ASK for specific time:
             "好的，了解您大約下午會抵達。為了更準確安排，請問大約是下午幾點呢？（例如：下午2點、下午3點等）"
           * If user gives specific time ("下午3點", "15:00", "3pm"), accept it directly
           * ALWAYS call update_guest_info regardless - save what they said first, then ask for clarity if needed
       
       - **Special Requests Collection (CRITICAL - MUST SAVE ALL)**:
         - After collecting arrival time, ask: "請問有什麼其他需求或特殊要求嗎？（例如：嬰兒床、消毒鍋、嬰兒澡盆、禁菸房等）"
         - **CRITICAL**: ANY user request mentioned during the conversation MUST be saved!
         - Examples of requests that MUST be saved:
           * 停車位需求 → call update_guest_info(order_id, 'special_need', '需要停車位')
           * 床型要求 ("我要兩張床") → save it!
           * 樓層要求 ("高樓層") → save it!
           * 設施需求 ("需要嬰兒床") → save it!
           * 提前入住 ("提前入住可以嗎", "能提早入住嗎") → call update_guest_info(order_id, 'special_need', '提前入住需求')
           * 延遲退房 ("可以延遲退房嗎") → save it!
           * 任何特殊要求 → save it!
         - If user says "沒有" or "好" (just acknowledgment): Do not save
         - **Note**: Special requests are stored in an array, so multiple requests can be accumulated.
         - After saving, always thank them: "好的，已為您記錄！"
         
         - **Bed Type Inquiries (IMPORTANT - Database Rules)**:
           When user asks about bed configuration, you MUST:
            1. **Follow Database Rules** - Only these combinations are possible:
               • 標準雙人房(SD): 兩小床
               • 標準三人房(ST): 三小床 OR 一大床+一小床  
               • 標準四人房(SQ): 兩大床 OR 兩小床+一大床 OR 四小床
               • 經典雙人房(CD): 兩小床 OR 一大床
               • 經典四人房(CQ): 兩大床 OR 四小床
               • 豪華雙人房(DD): 一大床
               • 行政雙人房(ED): 一大床
               • 海景雙人房(WD): 一大床 OR 兩小床
               • 海景四人房(WQ): 兩大床 OR 四小床
               • VIP雙人房(VD): 一大床
               • VIP四人房(VQ): 兩大床
               • 親子家庭房(FM): 兩大床 OR 一大床+兩小床
               • 無障礙雙人房(AD): 一大床
               • 無障礙四人房(AQ): 兩大床
           2. **Ask to clarify their preference** if they mention bed type
           3. **Record their request** using update_guest_info(order_id, 'special_need', '床型需求：XXX')
           4. **Use CAREFUL wording** - NEVER guarantee arrangement:
              ✅ CORRECT: "好的，已為您記錄床型需求：XXX。館方會盡力為您安排，但仍需以實際房況為準。"
              ❌ WRONG: "好的，我們會為您安排 XXX" (too absolute)
              ❌ WRONG: "已經為您確認 XXX" (cannot guarantee)
           5. **If request is IMPOSSIBLE** (e.g., user wants 3 small beds in 雙人房):
              Politely inform: "標準雙人房只能提供兩小床的配置。若您需要三小床，建議預訂標準三人房。我可以為您記錄此需求嗎？"
       
       - **MANDATORY Important Notices (ALWAYS show after completing guest info collection)**:
        After collecting all guest information (phone, arrival time, special requests), you MUST inform the guest of the following two important points:
        
        📌 **環保政策提醒**:
        "配合減塑／環保政策，我們旅館目前不提供任何一次性備品（如小包裝牙刷、牙膏、刮鬍刀、拖鞋等）。
        
        房內仍提供可重複使用的洗沐用品（大瓶裝或壁掛式洗髮乳、沐浴乳）與毛巾等基本用品。
        
        若您習慣使用自己的盥洗用品，建議旅途前記得自備。
        
        謝謝您的理解與配合，一起為環保盡一份心力 🌱"
        
        🅿️ **停車流程提醒**:
        "為了讓您的入住流程更順暢，請於抵達當日先至櫃檯辦理入住登記，之後我們的櫃檯人員將會協助引導您前往停車位置 🅿️
        
        感謝您的配合，我們期待為您提供舒適的入住體驗。"
        
        **CRITICAL**: These notices are MANDATORY and must be shown every time after order confirmation is complete. Do not skip them.
    - **If Order NOT Found**:
     - Apologize and ask them to double-check the ID.

**General Instructions:**
1. **STRICTLY** answer the user's question based **ONLY** on the provided Knowledge Base.
2. **DO NOT** use any outside knowledge, assumptions, or general information about hotels.
3. **FORMATTING RULE**: Do NOT use Markdown syntax (**, *, _, etc.) in your responses. Use plain text only. LINE does not support Markdown formatting.
4. If the answer is NOT explicitly found in the Knowledge Base, you **MUST** reply with the following apology template (in Traditional Chinese):
   "不好意思，關於這個問題我目前沒有相關資訊。請問方便留下您的訂單編號或入住房號，以便我們後續與您聯繫嗎？"
4. Reply in Traditional Chinese (繁體中文).

**Weather Query Instructions:**
1. If the user asks for **current weather** or weather for a **specific date** (e.g., "今天天氣", "明天天氣", "12/25天氣"), use `get_weather_forecast(date_str)`.
2. If the user asks for **weekly weather**, **future weather**, or **general forecast** (e.g., "一週天氣", "未來天氣", "天氣預報"), use `get_weekly_forecast()`.
3. **ALWAYS** ensure the response includes the data source attribution: "(資料來源：中央氣象署)".
"""
            
            
            # Configure safety settings to avoid over-blocking normal hotel conversations
            from google.generativeai.types import HarmCategory, HarmBlockThreshold
            
            # Save as instance variables for reuse in get_user_session
            self.safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE
            }
            
            # Generation config for more deterministic function calling
            self.generation_config = {
                'temperature': 0.2,  # Lower temperature for more consistent function calling
                'top_p': 0.8,
                'top_k': 20,
            }
            
            # Main model for conversation and function calling
            self.model = genai.GenerativeModel(
                model_name='gemini-2.5-flash',
                tools=self.tools,
                system_instruction=self.system_instruction,
                safety_settings=self.safety_settings,
                generation_config=self.generation_config
            )
            print("✅ HotelBot initialized.")
            
            # Vision model for OCR tasks (keep 2.0, already excellent)
            self.vision_model = genai.GenerativeModel(
                'gemini-2.0-flash',
                safety_settings=self.safety_settings
            )
            
            # Privacy validator - upgraded to 2.5 for better date parsing
            self.validator_model = genai.GenerativeModel(
                'gemini-2.5-flash',
                safety_settings=self.safety_settings
            )
            
        print("系統啟動：旅館專業客服機器人 (AI Vision + Function Calling + Multi-User + Logging + Weather版) 已就緒。")

    def _load_json(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading knowledge base: {e}")
            return {"faq": []}

    def _load_text(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error loading persona: {e}")
            return ""

    def _load_vip_users(self, path):
        """載入VIP用戶白名單"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                vip_list = data.get('vip_users', [])
                print(f"✅ Loaded {len(vip_list)} VIP user(s)")
                return set(vip_list)  # 使用set加速查詢
        except FileNotFoundError:
            print("⚠️  vip_users.json not found, VIP mode disabled")
            return set()
        except Exception as e:
            print(f"❌ Error loading VIP users: {e}")
            return set()

    # --- Tools for Gemini ---
    def check_order_status(self, order_id: str, user_confirmed: bool = False):
            """
            Checks the status of an order.
            
            Args:
                order_id: The order ID provided by the user (or the confirmed full ID).
                user_confirmed: Set to True ONLY after the user explicitly says "Yes" to the found order ID. Default is False.
            
            Returns:
                Dict with status:
                - If confirmed=False: returns 'confirmation_needed' and the Found ID.
                - If confirmed=True: returns full details dict containing:
                  * status: "found"
                  * order_id: the booking ID
                  * subject: email subject or booking source
                  * body: the cleaned body text
                  * **formatted_display**: 🚨 CRITICAL - Pre-formatted order details text 🚨
                    
                    ⚠️ MANDATORY ACTION REQUIRED ⚠️
                    When you receive this field, you MUST:
                    1. Output the EXACT content of `formatted_display` VERBATIM
                    2. Do NOT skip, summarize, or modify ANY part of it
                    3. Do NOT proceed to weather/contact BEFORE showing all 8 fields:
                       訂單來源, 訂單編號, 訂房人姓名, 聯絡電話, 入住日期, 退房日期, 房型, 早餐
                    4. ONLY after displaying formatted_display, then show weather/contact
                    
                    ❌ FORBIDDEN: Skipping `formatted_display` and going directly to:
                       "🌤️ 溫馨提醒..." or "系統顯示您的聯絡電話..."
                    ✅ REQUIRED: Display `formatted_display` FIRST, then weather/contact
            """
            print(f"🔧 Tool Called: check_order_status(order_id={order_id}, confirmed={user_confirmed})")
            
            # Clean input
            order_id = order_id.strip()

            # 1. Try PMS API First (Primary Data Source)
            order_info = None
            data_source = None
            
            try:
                print("🔷 Attempting PMS API query...")
                pms_response = self.pms_client.get_booking_details(order_id)
                
                if pms_response and pms_response.get('success'):
                    order_info = pms_response
                    data_source = 'pms'
                    print(f"✅ PMS API Success: {pms_response['data']['booking_id']}")
                else:
                    print("📭 PMS API: Booking not found")
            except Exception as e:
                print(f"⚠️ PMS API failed: {e}")
            
            # 2. Fallback to Gmail if PMS fails
            if not order_info or data_source != 'pms':
                print("📧 Falling back to Gmail search...")
                gmail_info = self.gmail_helper.search_order(order_id)
                if gmail_info:
                    order_info = gmail_info
                    data_source = 'gmail'
                    print("✅ Gmail search successful")
            
            # 3. Check if we found anything
            if not order_info:
                return {"status": "not_found", "order_id": order_id}

            # 4. Extract Order ID (different logic for PMS vs Gmail)
            if data_source == 'pms':
                # PMS data is already clean and structured
                pms_id = order_info['data']['booking_id']
                ota_id = order_info['data'].get('ota_booking_id', '')
                
                # 优先使用客人输入的号码来确认（如果匹配 OTA 订单号）
                if ota_id and (order_id in ota_id or ota_id in order_id):
                    found_id = ota_id  # 使用 OTA 订单号确认
                    found_subject = f"OTA Order: {ota_id}"
                    print(f"📋 Using OTA Order ID for confirmation: {found_id}")
                else:
                    found_id = pms_id  # 使用 PMS 订单号
                    found_subject = f"PMS Order: {pms_id}"
                    print(f"📋 Using PMS Order ID: {pms_id}")
            else:
                # Gmail data needs extraction (original logic)
                found_subject = order_info.get('subject', 'Unknown')
                found_id = order_info.get('order_id', 'Unknown')
                
                # Always try to extract the most complete NUMERIC order ID from subject
                import re
                # Look for long numeric sequences (10+ digits preferred, min 6 digits)
                patterns = [
                    r'訂單編號[：:]?\s*(?:[A-Z]+)?(\d{6,})',  # Optional colon
                    r'編號[：:]?\s*(?:[A-Z]+)?(\d{6,})',
                    r'Booking\s+ID[：:]?\s*(?:[A-Z]+)?(\d{6,})',
                    r'\b(?:RM[A-Z]{2})?(\d{10,})\b',  # Optional RMAG prefix
                    r'\b(\d{10,})\b'  # Pure long number
                ]
                
                extracted_id = None
                for pattern in patterns:
                    match = re.search(pattern, found_subject)
                    if match:
                        extracted = match.group(1)  # Get ONLY the digits
                        # Verify this contains the user's query
                        if order_id in extracted or extracted in order_id:
                            extracted_id = extracted
                            print(f"📋 Extracted numeric order ID: {extracted_id}")
                            break
                
                # Use extracted numeric ID if it's longer/more complete
                if extracted_id:
                    # Remove any non-digit characters from extracted_id
                    extracted_id = re.sub(r'\D', '', extracted_id)
                    if found_id == 'Unknown' or len(extracted_id) > len(re.sub(r'\D', '', found_id)):
                        found_id = extracted_id
                elif found_id == 'Unknown':
                    # Final fallback: extract digits from order_id or subject
                    numeric_only = re.sub(r'\D', '', order_id)
                    if numeric_only:
                        found_id = numeric_only
                    else:
                        found_id = order_id
            
            # 2. Confirmation Step (Safety + Correctness)
            if not user_confirmed:
                # Check for "Strong Match" to potentially skip manual confirmation
                # User Request: "If number matches exactly (ignoring prefix), accept it."
                # Logic: If order_id is long enough (>= 9 digits) and appears in found_id, auto-confirm.
                is_strong_match = len(order_id) >= 9 and (order_id in found_subject or (found_id != 'Unknown' and order_id in found_id))
                
                print(f"🔍 Match Debug: ID={order_id}, Found={found_id}, Subject={found_subject}, StrongMatch={is_strong_match}")
                
                if is_strong_match:
                     print(f"🤖 Auto-Confirming Strong Match: {order_id}")
                     user_confirmed = True # Proceed directly to Step 3
                else:
                    # We found something, but we must verify with the user first.
                    # We return only safe metadata, NO details.
                    return {
                        "status": "confirmation_needed",
                        "found_order_id": found_id,
                        "found_subject": found_subject,
                        "message": f"I found an order with ID {found_id}. Please ask the user if this is correct."
                    }

            # 3. Privacy & Detail Step (Only if Confirmed)
            from datetime import datetime, timedelta
            today_str = datetime.now().strftime("%Y-%m-%d")
            
            if data_source == 'pms':
                # PMS data: Simple privacy check based on check-in date
                try:
                    check_in_date = order_info['data']['check_in_date']
                    check_in = datetime.strptime(check_in_date, '%Y-%m-%d')
                    today = datetime.strptime(today_str, '%Y-%m-%d')
                    days_ago = (today - check_in).days
                    
                    if days_ago > 5:
                        print(f"🚫 Blocking Old PMS Order (Over 5 days): {found_id}")
                        return {
                            "status": "blocked",
                            "reason": "privacy_protection",
                            "message": "System Alert: This order is historical (Check-in > 5 days ago). Access Denied."
                        }
                    
                    print(f"✅ Privacy Check Passed for PMS Order: {found_id}")
                    
                    # Build response from PMS structured data
                    order_data = order_info['data']
                    
                    # 构建房号信息
                    room_numbers = order_data.get('room_numbers', [])
                    room_no_text = ', '.join(room_numbers) if room_numbers else '尚未安排'
                    
                    # 构建房型信息（不含人数）
                    rooms_info = []
                    for room in order_data.get('rooms', []):
                        room_name = room.get('room_type_name') or room.get('room_type_code', '').strip()
                        room_count = room.get('room_count', 1)
                        room_text = f"{room_name} x{room_count}"
                        rooms_info.append(room_text)
                    rooms_text = '\n                    '.join(rooms_info) if rooms_info else '無'
                    
                    # 订金信息（只显示已付订金）
                    deposit_paid = order_data.get('deposit_paid', 0)
                    deposit_text = ""
                    if deposit_paid and deposit_paid > 0:
                        deposit_text = f"\n                    已付訂金: NT${deposit_paid:,.0f}"
                    
                    # OTA 订单号（优先显示，如果没有则显示 PMS 订单号）
                    ota_id = order_data.get('ota_booking_id', '')
                    display_order_id = ota_id if ota_id else order_data['booking_id']
                    
                    # 订房来源（優先從備註判斷，其次才用 OTA ID）
                    booking_source = "未知"
                    remarks = order_data.get('remarks', '')
                    # 優先檢查 remarks 中的關鍵字
                    if '官網' in remarks or '網路訂房' in order_data.get('guest_name', ''):
                        booking_source = "官網"
                    elif 'agoda' in remarks.lower():
                        booking_source = "Agoda"
                    elif 'booking.com' in remarks.lower():
                        booking_source = "Booking.com"
                    # 如果 remarks 沒有，才用 OTA ID 判斷
                    elif ota_id:
                        if ota_id.startswith('RMAG'):
                            booking_source = "Agoda"
                        elif ota_id.startswith('RMPGP'):
                            booking_source = "Booking.com"
                    
                    # 組合姓名：優先使用 Last Name + First Name
                    last_name = order_data.get('guest_last_name', '').strip()
                    first_name = order_data.get('guest_first_name', '').strip()
                    if last_name and first_name:
                        full_name = f"{last_name}{first_name}"
                    else:
                        full_name = order_data.get('guest_name', '')
                    
                    # 訂單狀態檢查
                    status_name = order_data.get('status_name', '未知')
                    status_code = order_data.get('status_code', '')
                    
                    # 如果訂單已取消，只顯示取消訊息
                    if status_code.strip() == 'D' or '取消' in status_name:
                        clean_body = f"""
                    ⚠️ 訂單狀態：已取消
                    
                    此訂單已經取消，無法辦理入住。
                    如有疑問，請聯繫櫃檯：(03) 832-5700
                    """
                    else:
                        # 正常訂單：顯示核對資訊
                        
                        # 构建房型信息（只显示中文名称）
                        rooms_info = []
                        for room in order_data.get('rooms', []):
                            # PMS API 返回大寫鍵名，需要處理大小寫
                            room_code = room.get('ROOM_TYPE_CODE') or room.get('room_type_code', '')
                            room_code = room_code.strip() if room_code else ''
                            
                            # 優先使用房型代碼查詢中文名稱
                            if room_code in self.room_types:
                                room_name = self.room_types[room_code]['zh']
                            else:
                                room_name = room.get('ROOM_TYPE_NAME') or room.get('room_type_name') or room_code
                            
                            room_count = room.get('ROOM_COUNT') or room.get('room_count', 1)
                            room_text = f"{room_name} x{room_count}"
                            rooms_info.append(room_text)
                        rooms_text = '\n                    '.join(rooms_info) if rooms_info else '無'
                        
                        # 订金信息（只显示已付订金，如有）
                        deposit_paid = order_data.get('deposit_paid', 0)
                        deposit_text = ""
                        if deposit_paid and deposit_paid > 0:
                            deposit_text = f"\n                    已付訂金: NT${deposit_paid:,.0f}"
                        
                        
                        # 早餐資訊（從房價代號或備註判斷）
                        breakfast = "有"  # 預設有早餐
                        
                        # 檢查備註中的產品名稱
                        if '不含早' in remarks:
                            breakfast = "無"
                        
                        
                        # 也檢查房型名稱
                        for room in order_data.get('rooms', []):
                            room_type_name = room.get('room_type_name')
                            if room_type_name and '不含早' in room_type_name:
                                breakfast = "無"
                                break
                        
                        
                        
                        clean_body = f"""
                    訂單來源: {booking_source}
                    訂單編號: {ota_id if ota_id else order_data['booking_id']}
                    訂房人姓名: {full_name}
                    聯絡電話: {order_data.get('contact_phone', '未提供')}
                    入住日期: {order_data['check_in_date']}
                    退房日期: {order_data['check_out_date']} (共 {order_data['nights']} 晚)
                    房型: {rooms_text}{deposit_text}
                    早餐: {breakfast}
                    """
                    
                except Exception as e:
                    print(f"❌ PMS Privacy check error: {e}")
                    return {
                        "status": "blocked",
                        "reason": "system_error",
                        "message": "Privacy verification system encountered an error."
                    }
                    
            else:
                # Gmail data: Original LLM-based privacy check
                body = order_info.get('body', '')

                # Remove sensitive blocks first (CSS/Script)
                clean_body = re.sub(r'<style.*?>.*?</style>', '', body, flags=re.DOTALL | re.IGNORECASE)
                clean_body = re.sub(r'<script.*?>.*?</script>', '', clean_body, flags=re.DOTALL | re.IGNORECASE)
                # Remove remaining tags
                clean_body = re.sub(r'<[^>]+>', ' ', clean_body)
                # Collapse whitespace
                clean_body = re.sub(r'\s+', ' ', clean_body).strip()
                
                print(f"📧 Cleaned Email Body Preview (First 500 chars):\n{clean_body[:500]}") # Debug Log

                validation_prompt = f"""
                Task: Check-in Date Privacy Verification.
                
                Current Date: {today_str}
                Email Text Content:
                {clean_body[:3000]}
                
                Instructions:
                1. Search for "Check-in" or "入住日期" in the content.
                2. Extract the date text (e.g., "Dec 14, 2025" or "2025-12-14").
                3. Parse it to YYYY-MM-D.
                4. Calculate DAYS_AGO = Current Date - Check-in Date.
                5. Logic:
                   - If Check-in Date is in the FUTURE (DAYS_AGO < 0): ALLOW (Result: YES)
                   - If DAYS_AGO >= 0 and DAYS_AGO <= 5: ALLOW (Result: YES)
                   - If DAYS_AGO > 5: BLOCK (Result: NO)
                   - If Date Not Found: BLOCK (Result: NO)
                
                Examples:
                - Today: 2025-12-11, Check-in: 2025-12-14 → DAYS_AGO = -3 → ALLOW (Future booking)
                - Today: 2025-12-11, Check-in: 2025-12-10 → DAYS_AGO = 1 → ALLOW (Recent)
                - Today: 2025-12-11, Check-in: 2025-12-05 → DAYS_AGO = 6 → BLOCK (Too old)
                
                Output Required Format:
                REASON: [Found Date: X, Days Ago: Y, Decision: Valid/Invalid because...]
                RESULT: [YES/NO]
                """
                
                try:
                    # Use the Validator Model
                    validator_response = self.validator_model.generate_content(validation_prompt)
                    full_response = validator_response.text.strip()
                    print(f"🤔 Validator Thought Process:\n{full_response}")
                    
                    # Parse Result (handle both "RESULT: YES" and "RESULT: [YES]")
                    match = re.search(r'RESULT:\s*\[?(YES|NO)\]?', full_response, re.IGNORECASE)
                    result = match.group(1).upper() if match else 'NO'
                    
                    print(f"🔒 Privacy Validator Final Decision: {result} (Today: {today_str})")
                    
                    if result != 'YES':
                         # Block it
                         print(f"🚫 Blocking Old Order (Over 5 days): {found_id}")
                         return {
                            "status": "blocked",
                            "reason": "privacy_protection",
                            "message": "System Alert: This order is historical (Check-in > 5 days ago). Access Denied."
                        }
                    
                except Exception as e:
                    # FAIL SAFE: If validation fails, BLOCK access rather than allowing.
                    return {
                        "status": "blocked",
                        "reason": "system_error",
                        "message": "System Alert: Privacy verification system encountered an error. Access temporarily denied to prevent data leak."
                    }

            # PASSED! User is allowed to see the order details.
            print(f"✅ Privacy Check Passed for Order: {found_id}")
            
            # 儲存訂單資料到 JSON（新功能）
            order_data = {
                'order_id': found_id,
                'line_user_id': self.current_user_id,  # 添加用戶 ID
                'subject': found_subject,
                'body': clean_body,
                'check_in': None,  # 稍後由 LLM 提取
                'check_out': None,
                'room_type': None,
                'guest_name': None,
                'booking_source': None
            }
            
            # 嘗試從 body 提取基本資訊（簡易版）
            import re as regex_lib
            from datetime import datetime as dt
            
            # 提取入住日期（支援多種格式）
            # Format 1: "6-Dec-2025" or "06-Dec-2025"
            checkin_match = regex_lib.search(r'Check-in.*?(\d{1,2}-[A-Za-z]{3}-\d{4})', clean_body)
            if checkin_match:
                try:
                    # 轉換為標準格式 YYYY-MM-DD
                    date_obj = dt.strptime(checkin_match.group(1), '%d-%b-%Y')
                    order_data['check_in'] = date_obj.strftime('%Y-%m-%d')
                except:
                    pass
            
            # Format 2: "2025-12-06" (備用)
            if not order_data['check_in']:
                checkin_match2 = regex_lib.search(r'Check-in.*?(\d{4}-\d{2}-\d{2})', clean_body)
                if checkin_match2:
                    order_data['check_in'] = checkin_match2.group(1)
            
            # 提取退房日期（支援多種格式）
            checkout_match = regex_lib.search(r'Check-out.*?(\d{1,2}-[A-Za-z]{3}-\d{4})', clean_body)
            if checkout_match:
                try:
                    date_obj = dt.strptime(checkout_match.group(1), '%d-%b-%Y')
                    order_data['check_out'] = date_obj.strftime('%Y-%m-%d')
                except:
                    pass
            
            if not order_data['check_out']:
                checkout_match2 = regex_lib.search(r'Check-out.*?(\d{4}-\d{2}-\d{2})', clean_body)
                if checkout_match2:
                    order_data['check_out'] = checkout_match2.group(1)
            
            # 提取客人姓名
            # 只提取 First Name，避免包含 "Customer Last Name" 等文字
            name_match = regex_lib.search(r'Customer First Name.*?[：:]\s*([A-Za-z\s]+?)(?:\s+Customer|$)', clean_body)
            if name_match:
                order_data['guest_name'] = name_match.group(1).strip()
            else:
                # 備用：嘗試從「姓名:」提取
                name_match2 = regex_lib.search(r'姓名[：:]\s*([^\n,]+?)(?:\s*,|\s*電話|$)', clean_body)
                if name_match2:
                    order_data['guest_name'] = name_match2.group(1).strip()
                else:
                    order_data['guest_name'] = None

            
            # 提取電話號碼（支援多種格式）
            # Format 1: "電話: 0912345678" 或 "電話：0912345678"
            phone_match = regex_lib.search(r'電話[：:]\s*(09\d{8})', clean_body)
            if not phone_match:
                # Format 2: 單獨出現的手機號碼
                phone_match = regex_lib.search(r'\b(09\d{8})\b', clean_body)
            if phone_match:
                order_data['phone'] = phone_match.group(1)
            else:
                order_data['phone'] = None
            
            # 提取房型（支援多種格式）
            # 直接查找 "Standard/Deluxe/etc + Room" 模式
            room_match = regex_lib.search(r'\b((?:Standard|Deluxe|Superior|Executive|Family|VIP|Premium|Classic|Ocean View|Sea View|Economy|Accessible|Disability Access)\s+(?:Single|Double|Twin|Triple|Quadruple|Family|Suite|Queen Room)?\s*(?:Room|Suite)?[^,\n]*?(?:Non-Smoking|Smoking|with.*?View|with.*?Balcony)?)', clean_body, regex_lib.IGNORECASE)
            
            if not room_match:
                # 備用：查找特定房型關鍵字
                room_match = regex_lib.search(r'\b(Quadruple Room - Disability Access|Double Room - Disability Access|Double Room with Balcony and Sea View|Quadruple Room with Sea View|Superior Queen Room with Two Queen Beds)', clean_body, regex_lib.IGNORECASE)
            
            if room_match:
                raw_room_type = room_match.group(1).strip()
                # 清理尾部數字和多餘文字
                raw_room_type = regex_lib.sub(r'\s+\d+\s*$', '', raw_room_type)
                raw_room_type = regex_lib.sub(r'\s+No\..*$', '', raw_room_type)
                raw_room_type = regex_lib.sub(r'\s+', ' ', raw_room_type).strip()
                
                # 載入房型對應表
                try:
                    import json as json_lib
                    base_dir = os.path.dirname(os.path.abspath(__file__))
                    mapping_file = os.path.join(base_dir, 'room_type_mapping.json')
                    with open(mapping_file, 'r', encoding='utf-8') as f:
                        room_mapping = json_lib.load(f)['room_type_mapping']
                    
                    # 查找對應的內部代號
                    if raw_room_type in room_mapping:
                        order_data['room_type'] = room_mapping[raw_room_type]
                    else:
                        # 如果找不到精確匹配，保留原始名稱
                        order_data['room_type'] = raw_room_type
                except Exception as e:
                    print(f"⚠️ 無法載入房型對應表: {e}")
                    order_data['room_type'] = raw_room_type
            else:
                order_data['room_type'] = None
            
            # 提取訂房來源
            if 'agoda' in clean_body.lower():
                order_data['booking_source'] = 'Agoda'
            elif 'booking.com' in clean_body.lower():
                order_data['booking_source'] = 'Booking.com'
            
            # 儲存訂單
            try:
                self.logger.save_order(order_data)
                print(f"💾 Order {found_id} saved to database")
                
                # 建立訂單與 LINE 用戶的關聯
                if self.current_user_id:
                    self.logger.link_order_to_user(found_id, self.current_user_id)
                    print(f"🔗 Order {found_id} linked to LINE User {self.current_user_id}")
            except Exception as e:
                print(f"⚠️ Failed to save order: {e}")
            
            # Return FULL details with pre-formatted display text + MANDATORY INSTRUCTION
            return {
                "status": "found",
                "order_id": found_id,
                "subject": found_subject,
                "body": clean_body,
                "formatted_display": clean_body,  # 預格式化的完整訂單文本，LLM 應直接原樣輸出
                "NEXT_RESPONSE_INSTRUCTION": f"""
🚨🚨🚨 IMMEDIATE ACTION REQUIRED 🚨🚨🚨

YOU MUST FOLLOW THIS EXACT OUTPUT SEQUENCE:

STEP 1: Output the following EXACT TEXT (訂單詳情):
{clean_body}

STEP 2: ONLY AFTER showing all above details, then add weather and contact.

❌ DO NOT skip Step 1
❌ DO NOT go directly to "🌤️ 溫馨提醒"
❌ DO NOT go directly to "系統顯示您的聯絡電話"

✅ You MUST output Step 1 FIRST, then Step 2
"""
            }


    def update_guest_info(self, order_id: str, info_type: str, content: str):
        """
        Updates guest information for an existing order.
        
        Args:
            order_id: The order ID
            info_type: Type of information ('phone', 'arrival_time', 'special_need')
            content: The content to update
        
        Returns:
            Dict with success status
        """
        print(f"🔧 Tool Called: update_guest_info(order_id={order_id}, type={info_type}, content={content})")
        
        # 驗證訂單是否存在
        if order_id not in self.logger.orders:
            return {
                "status": "error",
                "message": f"Order {order_id} not found in database. Please check the order first."
            }
        
        # 更新資料
        success = self.logger.update_guest_request(order_id, info_type, content)
        
        if success:
            print(f"✅ Successfully updated {info_type} for order {order_id}")
            return {
                "status": "success",
                "message": f"Successfully saved {info_type}"
            }
        else:
            print(f"❌ Failed to update {info_type} for order {order_id}")
            return {
                "status": "error",
                "message": "Failed to save information. Please try again."
            }


    def get_weather_forecast(self, date_str: str):
        """
        Gets the weather forecast for Checheng Township on a specific date.
        :param date_str: Date in 'YYYY-MM-DD' format.
        """
        print(f"🔧 Tool Called: get_weather_forecast(date_str={date_str})")
        return self.weather_helper.get_weather_forecast(date_str)

    def get_weekly_forecast(self):
        """
        Gets the weekly weather forecast for Checheng Township.
        Returns a formatted string with 7-day forecast.
        """
        print(f"🔧 Tool Called: get_weekly_forecast()")
        return self.weather_helper.get_weekly_forecast()

    def handle_image(self, user_id, image_data, display_name=None):
        """Handles image input using Gemini Vision."""
        if display_name:
            self.logger.save_profile(user_id, display_name)

        if not hasattr(self, 'model'):
            return "【系統錯誤】尚未設定 GOOGLE_API_KEY，無法辨識圖片。"

        try:
            image = Image.open(io.BytesIO(image_data))
            
            prompt = """
        請仔細分析這張圖片，判斷是以下哪一種類型：
        
        1. 如果是「住宿券」或「優惠券」(Voucher)：
           - 特徵：通常會有「使用說明」、「有效期限」、券號（可能以 NO. 或 No. 開頭）
           - 辨識券號（提取完整的券號，包含 NO. 前綴和所有數字）
           - 確認是否為龜地灣旅棧的住宿券
           - 回覆格式：VOUCHER|券號
           
        2. 如果是「訂單編號」、「預訂確認書」或「訂房資訊」：
           - 特徵：包含 Order ID、Booking ID、訂單編號等字樣
           - 提取訂單編號（通常是純數字，5位數以上）
           - 回覆格式：ORDER|訂單編號
           
        3. 如果都不是以上類型：
           - 簡短描述你看到的內容
           - 回覆格式：OTHER|描述
        
        請嚴格按照上述格式回覆，使用 | 符號分隔類型和內容。
        """
            
            # For vision, we use the separate vision model to avoid tool calling interference
            response = self.vision_model.generate_content([prompt, image])
            text = response.text.strip()
            print(f"Gemini Vision Result: {text}")
            
            # Log the image interaction
            self.logger.log(user_id, "User", "[傳送了一張圖片]")
            self.logger.log(user_id, "Bot (Vision)", text)
            
            # Parse the structured response
            if "|" in text:
                parts = text.split("|", 1)
                response_type = parts[0].strip().upper()
                content = parts[1].strip() if len(parts) > 1 else ""
                
                if response_type == "VOUCHER":
                    return self._handle_voucher_image(content, user_id)
                elif response_type == "ORDER":
                    return self._handle_order_image(content, user_id)
                else:
                    return f"我看到了圖片內容：{content}\n\n不過我目前主要能辨識「住宿券」和「訂單編號」。如果您有其他問題，歡迎直接詢問我！😊"
            else:
                # Fallback: try to find any number as before
                match = re.search(r'(\d{5,})', text)
                if match:
                    found_id = match.group(1)
                    return self._handle_order_image(found_id, user_id)
                else:
                    return text

        except ValueError as ve:
            # Gemini API returned finish_reason != STOP (usually due to token limit or safety filter)
            error_msg = str(ve)
            print(f"❌ Gemini ValueError: {error_msg}")
            
            # Check if it's a finish_reason=1 error (token limit exceeded)
            if "finish_reason" in error_msg or "The candidate's" in error_msg:
                print(f"⚠️ Token limit likely exceeded for user {user_id}. Auto-resetting conversation...")
                
                # Automatically reset the user's conversation
                self.reset_conversation(user_id)
                
                # Return a friendly message explaining what happened
                reply = """對話歷史已自動清除，以確保系統正常運作。

請再次提供您的訂單編號，我將為您重新查詢。謝謝！😊"""
                self.logger.log(user_id, "Bot", reply)
                return reply
            
            # Other ValueError
            reply = f"【受邀回覆】不好意思，剛才連線有點問題，請您再說一次好嗎？😊"
            self.logger.log(user_id, "Bot", reply)
            return reply

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Vision Error: {e}")
            return "【客服回覆】\n圖片處理發生錯誤，請稍後再試。"

    def _handle_voucher_image(self, voucher_number, user_id):
        """處理住宿券圖片辨識結果"""
        # Store voucher number in context for potential future use
        if user_id not in self.user_context:
            self.user_context[user_id] = {}
        self.user_context[user_id]['voucher_number'] = voucher_number
        
        return f"""✅ 我看到您的住宿券了！券號：{voucher_number}

📅 使用住宿券預訂流程：
1. 請至官網預訂：https://ktwhotel.com/2cTrT
2. 付款方式選擇「銀行轉帳」
3. 在訂房需求欄位填入住宿券編號：{voucher_number}
4. 預訂完成後，請告知我訂房編號
5. 我會為您確認並回傳訂房確認書

⚠️ 重要提醒：
• 適用房型：四人房（不含早餐）
• 適用日期：週日到週五（春節及連續假期不適用）
• 入住時請務必攜帶住宿券正本
• 核對券號，認券不認人
• 如需加購早餐，請在收到確認書後告知我

有任何問題都可以隨時詢問我！😊"""

    def _handle_order_image(self, found_id, user_id):
        """處理訂單編號圖片辨識結果"""
        # Store this ID in context for the next turn
        if user_id not in self.user_context:
            self.user_context[user_id] = {}
        self.user_context[user_id]["pending_order_id"] = found_id
        return f"我從圖片中看到了訂單編號 {found_id}。請問您是要查詢這筆訂單嗎？"


    def _get_recent_conversation_summary(self, user_id, max_turns=20):
        """
        讀取用戶最近的對話記錄並生成摘要
        
        Args:
            user_id: 用戶 ID
            max_turns: 讀取最近幾輪對話（預設 20 輪）
        
        Returns:
            str: 對話摘要，None 表示無歷史記錄
        """
        try:
            # 讀取日誌
            logs = self.logger.get_logs(user_id)
            
            if logs == "尚無對話紀錄 (No logs found).":
                return None
            
            # 解析日誌格式: [時間] 【發送者】\n訊息\n-----
            import re
            pattern = r'\[([^\]]+)\] 【([^】]+)】\n(.*?)(?=\n-{5,}|\Z)'
            matches = re.findall(pattern, logs, re.DOTALL)
            
            if not matches:
                return None
            
            # 只取最近的對話（max_turns 輪 = max_turns*2 則訊息，因為每輪包含用戶+Bot）
            recent_messages = matches[-(max_turns * 2):]
            
            # 提取關鍵資訊
            conversation_lines = []
            found_order_ids = []  # 改為列表，記錄所有訂單號（客人可能訂過多次）
            
            for timestamp, sender, message in recent_messages:
                # 清理訊息內容
                clean_message = message.strip()
                
                # 限制每則訊息長度（避免 token 過多）
                if len(clean_message) > 200:
                    clean_message = clean_message[:200] + "..."
                
                # 提取訂單號（可能有多筆）
                order_matches = re.findall(r'\b(16\d{8}|25\d{8})\b', clean_message)
                for order_id in order_matches:
                    if order_id not in found_order_ids:  # 避免重複
                        found_order_ids.append(order_id)
                
                # 記錄對話
                conversation_lines.append(f"[{sender}]: {clean_message}")
            
            # 生成摘要
            summary = "Recent conversation history (last {} turns):\n".format(len(conversation_lines) // 2)
            summary += "\n".join(conversation_lines[-40:])  # 最多顯示最近 40 則訊息
            
            # 如果找到訂單號，特別標註（可能有多筆）
            if found_order_ids:
                if len(found_order_ids) == 1:
                    summary += f"\n\n**Important Context**: User's current order ID is {found_order_ids[0]}"
                else:
                    summary += f"\n\n**Important Context**: User has multiple orders: {', '.join(found_order_ids)} (most recent: {found_order_ids[-1]})"
            
            print(f"📖 Loaded {len(recent_messages)} messages from chat history for user {user_id}")
            if found_order_ids:
                print(f"📌 Found {len(found_order_ids)} order ID(s) in history: {', '.join(found_order_ids)}")
            
            return summary
            
        except Exception as e:
            print(f"⚠️ Error reading conversation history: {e}")
            return None

    def get_user_session(self, user_id):
        """Retrieves or creates a chat session for the given user."""
        if user_id not in self.user_sessions:
            print(f"Creating new chat session for user: {user_id}")
            
            # Check if VIP user and construct appropriate system instruction
            is_vip = user_id in self.vip_users
            if is_vip:
                print(f"👑 VIP Mode activated for user: {user_id}")
                # VIP用戶：使用VIP persona，無需knowledge base限制
                kb_str = json.dumps(self.knowledge_base, ensure_ascii=False, indent=2)
                vip_system_instruction = f"""
You are a friendly and helpful AI assistant.

Your Persona:
{self.vip_persona}

Hotel Knowledge Base (for reference when answering hotel-related questions):
{kb_str}

You still have access to hotel management tools (check_order_status, get_weather_forecast, etc.).
Use these tools when appropriate to provide accurate information.
"""
                active_system_instruction = vip_system_instruction
            else:
                # 一般用戶：使用標準系統指令
                active_system_instruction = self.system_instruction
            
            # Create model with appropriate system instruction
            model_with_persona = genai.GenerativeModel(
                model_name='gemini-2.5-flash',
                tools=self.tools,
                system_instruction=active_system_instruction,
                safety_settings=self.safety_settings,
                generation_config=self.generation_config
            )
            
            self.user_sessions[user_id] = model_with_persona.start_chat(enable_automatic_function_calling=True)
        return self.user_sessions[user_id]

    def reset_conversation(self, user_id):
        """重置用戶對話：清除 chat session 和對話歷史"""
        # 刪除 chat session（下次會重新創建）
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
            print(f"✅ Reset chat session for user: {user_id}")
        
        # 清除用戶上下文
        if user_id in self.user_context:
            del self.user_context[user_id]
            print(f"✅ Cleared context for user: {user_id}")
        
        # 清除對話日誌（保留歷史記錄但標記為新對話）
        self.logger.log(user_id, "System", "=== 對話已重新開始 ===")
        print(f"🔄 User {user_id} conversation resetted")


    def generate_response(self, user_question, user_id="default_user", display_name=None):
        # 設定當前用戶 ID，供工具函數使用
        self.current_user_id = user_id
        
        # Save profile if provided
        if display_name:
            self.logger.save_profile(user_id, display_name)

        # Log User Input
        self.logger.log(user_id, "User", user_question)

        # Check for pending context (e.g. Order ID from previous image)
        context = self.user_context.get(user_id, {})
        pending_id = context.get("pending_order_id")
        
        # Inject Current Date to help Gemini understand "Today", "Tomorrow"
        today_str = datetime.now().strftime("%Y-%m-%d")
        weekday_map = {0: '一', 1: '二', 2: '三', 3: '四', 4: '五', 5: '六', 6: '日'}
        weekday_str = weekday_map[datetime.now().weekday()]
        system_time_context = f"\n(System Info: Current Date is {today_str} 星期{weekday_str})"
        
        # Append context to user question (invisible to user in chat, but visible to LLM)
        user_question_with_context = user_question + system_time_context
        
        if pending_id:
            # Inject context into the prompt so the AI knows what "Yes" refers to
            print(f"Injecting pending Order ID: {pending_id}")
            user_question_with_context += f"\n(System Note: The user previously uploaded an image containing Order ID {pending_id}. If the user is confirming or saying 'yes', please use this ID to call check_order_status.)"
            # Clear only the pending_id to avoid stuck state, but keep current_order_id
            if user_id in self.user_context and 'pending_order_id' in self.user_context[user_id]:
                del self.user_context[user_id]['pending_order_id']
        
        # Inject current order_id if exists (for context tracking across topic changes)
        current_order_id = context.get("current_order_id")
        if current_order_id:
            print(f"📌 Current active Order ID: {current_order_id}")
            user_question_with_context += f"\n(System Note: The current active Order ID is {current_order_id}. If the user provides arrival time, special requests, or any guest information, use this Order ID when calling update_guest_info.)"

        if not hasattr(self, 'model'):
            return "【系統錯誤】尚未設定 GOOGLE_API_KEY，無法使用 AI 回覆。"

        try:
            # Get user-specific session
            chat_session = self.get_user_session(user_id)
            
            # **NEW**: 讀取歷史對話記錄（即使重啟也能恢復記憶）
            # VIP用戶跳過歷史載入，避免舊的拒絕回答模式影響新對話
            is_vip = user_id in self.vip_users
            if not is_vip:
                conversation_summary = self._get_recent_conversation_summary(user_id)
                if conversation_summary:
                    user_question_with_context += f"\n\n(System Context - {conversation_summary})"
            else:
                print(f"👑 VIP用戶跳過歷史對話載入")
            
            # Send message to Gemini
            print(f"🤖 Sending to Gemini (Tools Enabled: True)...") # Assuming tools are always enabled for chat sessions
            response = chat_session.send_message(user_question_with_context)
            print("🤖 Gemini Response Received.")

            # Check if order was queried - if yes, save it as current_order_id
            if hasattr(response, 'parts'):
                for part in response.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        if part.function_call.name == 'check_order_status':
                            # Extract order_id from function call
                            order_id_arg = part.function_call.args.get('order_id', '')
                            if order_id_arg:
                                # Check if this is a NEW order (different from current)
                                old_order_id = self.user_context.get(user_id, {}).get('current_order_id')
                                if old_order_id and old_order_id != order_id_arg:
                                    print(f"🔄 Order Switch Detected: {old_order_id} → {order_id_arg}")
                                    # Clear any pending collection state for the old order
                                    # This prevents mixing data between different orders
                                
                                print(f"🔖 Saving current_order_id: {order_id_arg}")
                                if user_id not in self.user_context:
                                    self.user_context[user_id] = {}
                                self.user_context[user_id]['current_order_id'] = order_id_arg
                                # Mark when this order was queried (for staleness detection)
                                self.user_context[user_id]['order_query_time'] = datetime.now()
            
            reply_text = response.text
            
            # Log Bot Response
            self.logger.log(user_id, "Bot", reply_text)
            
            return reply_text
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Gemini API Error: {e}")
            # If session fails (e.g. history too long or other error), reset it for this user
            print(f"Resetting session for user: {user_id}")
            self.user_sessions[user_id] = self.model.start_chat(enable_automatic_function_calling=True)
            return "【客服回覆】\n不好意思，剛才連線有點問題，請您再說一次好嗎？"

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    kb_path = os.path.join(base_dir, "knowledge_base.json")
    persona_path = os.path.join(base_dir, "persona.md")

    bot = HotelBot(kb_path, persona_path)

    print("\n--- 模擬 LINE@ 對話視窗 (輸入 'exit' 離開) ---")
    print("Agent: 您好！我是您的專屬客服，請問有什麼我可以幫您的嗎？")
    
    # Simulate a user ID for local testing
    user_id = "local_test_user"

    while True:
        user_input = input("\nUser: ")
        if user_input.lower() in ['exit', 'quit', '離開']:
            print("Agent: 謝謝您的來訊，期待再次為您服務！")
            break
        
        response = bot.generate_response(user_input, user_id)
        print(f"Agent: {response}")

if __name__ == "__main__":
    main()
