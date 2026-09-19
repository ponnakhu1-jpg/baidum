import os
import random
import requests
from bs4 import BeautifulSoup
from flask import Flask, abort, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# --- ดึงค่า คีย์และ ID จาก Environment Variables ---
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get(
    "LINE_CHANNEL_ACCESS_TOKEN",
    "QW21xCzezYiuNSO+xrm2q+frEeWsecnQt64yjbsjXZOBOffIbuMK8JtovDewX8ccJ+kEmsVd8XyBi2j7JO5cvNmswWabXZtggtIepp+EePspovDsPPaai8U/Lc18qvxEFHIUHsFg6pZwfz+wVmjOFwdB04t89/1O/w1cDnyilFU="
)
LINE_CHANNEL_SECRET = os.environ.get(
    "LINE_CHANNEL_SECRET", 
    "5903d4e92852c68911adbf23df10f01d"
)
TARGET_GROUP_ID = os.environ.get(
    "TARGET_GROUP_ID", 
    "Cd9bd5f0a1640666114ff9dd35912ea75"
).strip()

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)


# --- 1. ฟังก์ชันสร้างข้อความแนวทางหวย ---
def generate_lottery_message(lottery_name="แนวทางหวย"):
    root_numbers = random.sample(range(0, 10), 2)
    spot_numbers = random.sample(range(0, 100), 10)
    sets = random.sample(range(0, 1000), 6)

    message_text = (
        f"📌 แนวทาง {lottery_name}\n"
        f"เลขรูด:{','.join(map(str, root_numbers))}\n"
        f"เลขเจาะ:{','.join(f'{int(x):02d}' for x in spot_numbers)}\n"
        f"6กลับ:{','.join(f'{int(x):03d}' for x in sets)}"
    )
    return message_text


# --- 2. ฟังก์ชันส่งแนวทางหวยอัตโนมัติตามชื่อหวย ---
def send_lottery_guidance(lottery_name="แนวทางหวย"):
    message_text = generate_lottery_message(lottery_name)
    try:
        target_id = os.environ.get("TARGET_GROUP_ID", TARGET_GROUP_ID).strip()
        if not target_id or not target_id.startswith("C"):
            print(f"❌ Error: TARGET_GROUP_ID [{target_id}] ไม่ถูกต้อง (ต้องขึ้นต้นด้วย C)")
            return

        line_bot_api.push_message(
            target_id, messages=TextSendMessage(text=message_text)
        )
        print(f"✅ ส่งแนวทาง [{lottery_name}] เรียบร้อยแล้ว!")
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการส่ง [{lottery_name}]: {e}")


# --- 3. ฟังก์ชันดึงผลหวยแบบเรียลไทม์จากเว็บเป้าหมาย ---
def fetch_realtime_lottery(lottery_name):
    try:
        url = "https://xn--t3cmiit.com/stock-lottery#vip"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'

        if response.status_code != 200:
            return "❌ ไม่สามารถเชื่อมต่อกับเว็บไซต์ผลหวยได้ในขณะนี้"

        soup = BeautifulSoup(response.text, 'html.parser')

        # ค้นหาข้อมูลจากหน้าเว็บ (ดึงข้อมูลภาพรวมเบื้องต้นหรือชื่อหวยที่ตรงกัน)
        # หมายเหตุ: โค้ดส่วนนี้จะทำการดึงลิงก์หรือข้อความจากเว็บเป้าหมายมาแสดงผล
        found_data = []
        for item in soup.find_all(['div', 'tr', 'li']):
            text = item.get_text()
            if lottery_name in text:
                # ตัดข้อความให้กระชับเพื่อนำมาแสดงในไลน์
                clean_text = " ".join(text.split())
                if len(clean_text) < 150: # กรองเฉพาะบรรทัดที่เกี่ยวข้อง
                    found_data.append(clean_text)

        if found_data:
            # เลือกผลลัพธ์ที่ตรงที่สุดมาแสดง
            result_str = "\n".join(found_data[:2])
            return f"🟢 ทรัพย์เศรษฐี ผล {lottery_name} (เรียลไทม์):\n{result_str}"
        else:
            # ถ้ายังหาคีย์เวิร์ดไม่พบในทันที ให้แสดงลิงก์แหล่งอ้างอิงสำรองให้ลูกค้ากดตรวจสอบเองได้
            return (f"🟢 ทรัพย์เศรษฐี อัปเดตผล {lottery_name}\n"
                    f"ตรวจสอบผลรางวัลฉบับเต็มได้ที่:\n{url}")

    except Exception as e:
        print(f"Error scraping: {e}")
        return f"🟢 ทรัพย์เศรษฐี อัปเดตผล {lottery_name}\nตรวจสอบผลรางวัลได้ที่: https://xn--t3cmiit.com/stock-lottery#vip"


# --- Webhook & API Routes ---
@app.route("/", methods=["GET"])
def home():
    return "Line Bot Scheduler is running!", 200

@app.route("/test-push", methods=["GET"])
def test_push():
    try:
        send_lottery_guidance("ทดสอบระบบส่งอัตโนมัติ")
        return "ส่งข้อความทดสอบเรียบร้อยแล้ว!", 200
    except Exception as e:
        return f"เกิดข้อผิดพลาด: {e}", 500

@app.route("/trigger-lottery/<lottery_name>", methods=["GET"])
def trigger_lottery(lottery_name):
    try:
        send_lottery_guidance(lottery_name)
        return f"ส่งแนวทาง {lottery_name} สำเร็จ!", 200
    except Exception as e:
        return f"Error: {e}", 500

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


# --- 4. ระบบตอบกลับข้อความในไลน์ ---
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_msg = event.message.text.strip()

    if event.source.type == "group":
        print(f"📌 Group ID ปัจจุบันคือ: {event.source.group_id}")

    # 1. ขอไอดีกลุ่ม
    if user_msg == "ขอไอดีกลุ่ม":
        if event.source.type == "group":
            group_id = event.source.group_id
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"Group ID ของกลุ่มนี้คือ:\n{group_id}"),
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="คำสั่งนี้ใช้ได้เฉพาะในกลุ่มไลน์ครับ"),
            )
        return

    # 2. ตรวจผลหวยเรียลไทม์
    if user_msg.startswith("ผลหวย") or user_msg.startswith("ตรวจหวย"):
        lottery_name = user_msg.replace("ผลหวย", "").replace("ตรวจหวย", "").strip()
        
        if not lottery_name:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="กรุณาระบุชื่อหวยที่ต้องการตรวจด้วยครับ\nเช่น 'ผลหวยฮานอย' หรือ 'ผลนิเคอิ'")
            )
            return
            
        result_text = fetch_realtime_lottery(lottery_name)
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=result_text)
        )
        return

    # 3. ขอแนวทางระบุชื่อ
    if user_msg.startswith("ขอแนวทาง"):
        lottery_name = user_msg.replace("ขอแนวทาง", "").strip()
        if not lottery_name:
            lottery_name = "หวยประจำวัน"

        message_text = generate_lottery_message(lottery_name)
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=message_text)
        )
        return

    # 4. ขอแนวทางทั่วไป
    if user_msg in ["แนวทาง", "แนวทางหวย"]:
        message_text = generate_lottery_message("หวยประจำวัน")
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=message_text)
        )
        return


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
