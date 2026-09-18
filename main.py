import os
import random
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, abort, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# --- คีย์และ ID สำหรับเชื่อมต่อ LINE API ---
LINE_CHANNEL_ACCESS_TOKEN = "0PnXQOQjvPvhuqMyF42RTEcfGdDr1xKFKzIFJh1oCXgmJngQcRPAOd85pWwQg0G3/jc1g+UYEuIccUao7WlVQQMwob+/ScM4MtqN6K1T+8Gyk6igcFbU2k0ZRvOh+8Aediu90MrLXX0QWy4xC+anIQdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = "edc04916b82d3f178f4ce7809876f214"
TARGET_GROUP_ID = "Ccd80f46ea82114a21319bc2fa4b3b264"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)


# --- ฟังก์ชันสร้างข้อความแนวทางหวย ---
def generate_lottery_message():
    root_numbers = random.sample(range(0, 10), 2)
    spot_numbers = random.sample(range(0, 100), 10)
    sets = random.sample(range(0, 1000), 6)

    message_text = (
        f"\nเลขรูด:{','.join(map(str, root_numbers))}"
        f"\nเลขเจาะ:{','.join(f'{int(x):02d}' for x in spot_numbers)}"
        f"\n6กลับ:{','.join(f'{int(x):03d}' for x in sets)}"
    )
    return message_text


# --- ฟังก์ชันส่งแนวทางหวยไปยังกลุ่มที่กำหนด (Push Message) ---
def send_lottery_guidance():
    message_text = generate_lottery_message()
    try:
        line_bot_api.push_message(
            TARGET_GROUP_ID, messages=TextSendMessage(text=message_text)
        )
        print("ส่งแนวทางอัตโนมัติเรียบร้อยแล้ว!")
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการส่งPush Message: {e}")


# --- ระบบตั้งเวลาส่งอัตโนมัติ (APScheduler) ---
scheduler = BackgroundScheduler(timezone="Asia/Bangkok")

# กำหนดเวลาส่งตามที่คุณต้องการ (แก้ไข/เพิ่ม-ลด เวลาได้ตามสะดวก)
scheduler.add_job(
    send_lottery_guidance, "cron", hour=9, minute=30
)  # รอบเช้า 09:30 น.
scheduler.add_job(
    send_lottery_guidance, "cron", hour=15, minute=30
)  # รอบบ่าย 15:30 น.
scheduler.add_job(
    send_lottery_guidance, "cron", hour=20, minute=0
)  # รอบค่ำ 20:00 น.

scheduler.start()


# --- Webhook สำหรับตรวจสอบสถานะ Server ---
@app.route("/", methods=["GET"])
def home():
    return "Line Bot Scheduler is running!", 200


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


# --- ระบบตอบกลับข้อความอัตโนมัติ (Reply Message) ---
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_msg = event.message.text.strip()

    # เมื่อมีคนพิมพ์คำว่า "แนวทาง", "ขอแนวทาง", หรือ "แนวทางหวย" บอทจะแจกเลขสดๆ ทันที
    if user_msg in ["แนวทาง", "ขอแนวทาง", "แนวทางหวย"]:
        message_text = generate_lottery_message()
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=message_text)
        )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
