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


# --- 1. ฟังก์ชันสร้างข้อความแนวทางหวย (ระบุชื่อหวยได้) ---
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
        line_bot_api.push_message(
            TARGET_GROUP_ID, messages=TextSendMessage(text=message_text)
        )
        print(f"ส่งแนวทาง [{lottery_name}] เรียบร้อยแล้ว!")
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการส่ง [{lottery_name}]: {e}")


# --- 3. ระบบ Scheduler ตั้งเวลาส่งอัตโนมัติ ---
scheduler = BackgroundScheduler(timezone="Asia/Bangkok")


# ฟังก์ชันช่วยเพิ่มชื่อหวยและเวลาส่งลงในระบบ Scheduler
def add_lottery_schedule(name, hour, minute):
    """ฟังก์ชันสำหรับเพิ่มชื่อหวยและกำหนดเวลาส่ง"""
    scheduler.add_job(
        send_lottery_guidance, "cron", hour=hour, minute=minute, args=[name]
    )


# =========================================================
# 🎯 ส่วนตั้งชื่อหวยและเวลาส่งอัตโนมัติ (แก้ไข/เพิ่มตรงนี้ได้เลย)
# รูปแบบ: add_lottery_schedule("ชื่อหวย", ชั่วโมง, นาที)
# =========================================================
add_lottery_schedule("ลาวExtar", 8, 00)  
add_lottery_schedule("นิเคอิเช้า+VIP", 8, 30) 
add_lottery_schedule("ฮานอยอาเซียน", 8, 30)  # ส่ง 18:15 น.
add_lottery_schedule("จีนเช้า+VIP", 09, 30)  # ส่ง 20:00 น.
add_lottery_schedule("ลาวTV", 10, 00)
add_lottery_schedule("ฮั่งเช้า+VIP", 10, 00)
add_lottery_schedule("ฮานอยHD", 10, 30)
add_lottery_schedule("ใต้หวัน+VIP", 11, 00)
add_lottery_schedule("ฮานอยStar", 11, 30)
add_lottery_schedule("เกาหลี+VIP", 12, 00)
add_lottery_schedule("นิเคอิบ่าย+VIP", 12, 30)
add_lottery_schedule("ลาวHD", 13, 00)
add_lottery_schedule("จีนบ่าย+VIP", 13, 10)
add_lottery_schedule("ฮานอยTV", 13, 30)
add_lottery_schedule("ฮั่งเส็งบ่าย+VIP", 14, 30)
add_lottery_schedule("ลาวสตาร์", 15, 00)
add_lottery_schedule("สิงคโปร์+VIP", 15, 20)
add_lottery_schedule("ไทยเย็น", 16, 00)
add_lottery_schedule("ฮานอยกาชาด", 15, 30)
add_lottery_schedule("ฮานอยพิเศษ", 16, 30)
add_lottery_schedule("ฮานอยสามัคคี", 16, 30)
add_lottery_schedule("ฮานอยปกติ", 17, 30)
add_lottery_schedule("ฮานอยVIP", 18, 30)
add_lottery_schedule("ฮานอยพัฒนา", 18, 30)
add_lottery_schedule("ลาวสามัคคี", 19, 30)
add_lottery_schedule("ลาวอาเซียน", 20, 00)
add_lottery_schedule("ลาวVIP", 20, 30)
add_lottery_schedule("ลาวสามัคคีVIP", 20, 30)
add_lottery_schedule("3รัฐ+VIP", 21, 10)
add_lottery_schedule("ลาวสตาร์VIP", 21, 10)
add_lottery_schedule("ฮานอยExtar", 21, 30)
add_lottery_schedule("ลาวกาชาด", 22, 00)
add_lottery_schedule("ดาวโจนส์+VIP", 23, 30)
scheduler.start()


# --- Webhook Routes ---
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


# --- 4. ระบบตอบกลับข้อความในไลน์ (ดึงชื่อหวยจากข้อความที่พิมพ์มาได้) ---
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_msg = event.message.text.strip()

    # กรณีพิมพ์คำว่า "ขอแนวทาง [ชื่อหวย]" เช่น "ขอแนวทาง ฮานอย"
    if user_msg.startswith("ขอแนวทาง"):
        # ดึงชื่อหวยจากคำที่พิมพ์ต่อท้าย
        lottery_name = user_msg.replace("ขอแนวทาง", "").strip()
        if not lottery_name:
            lottery_name = "หวยประจำวัน"

        message_text = generate_lottery_message(lottery_name)
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=message_text)
        )

    # กรณีพิมพ์คำว่า "แนวทาง" หรือ "แนวทางหวย" สั้นๆ
    elif user_msg in ["แนวทาง", "แนวทางหวย"]:
        message_text = generate_lottery_message("หวยประจำวัน")
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=message_text)
        )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
