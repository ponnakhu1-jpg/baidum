import os
import random
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, abort, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# --- คีย์และ ID สำหรับเชื่อมต่อ LINE API ---
LINE_CHANNEL_ACCESS_TOKEN = "l7iMS9gakB9hsgqoDqlUyzqWYhnVJbHQj19VYUO47gr0qcFier1UsX19Ft9SxUk8hGlQinbpaQrXjNbIS0H6g54I5Js/yW8gpi3k5u/rNdCKsIvIQg6noqrUx+J66bnteLI7K8EW5Ax8YrqZawZ/HAdB04t89/1O/w1cDnyilFU=="
LINE_CHANNEL_SECRET = "266817472f62731ff868dc16a955f40f"
TARGET_GROUP_ID = "C57ce5ea1a45cb1c2ea9db9868ebd54f8"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

bkk_tz = pytz.timezone("Asia/Bangkok")


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
        line_bot_api.push_message(
            TARGET_GROUP_ID, messages=TextSendMessage(text=message_text)
        )
        print(f"ส่งแนวทาง [{lottery_name}] เรียบร้อยแล้ว!")
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการส่ง [{lottery_name}]: {e}")


# --- 3. ระบบ Scheduler ตั้งเวลาส่งอัตโนมัติ ---
scheduler = BackgroundScheduler(timezone=bkk_tz)


def add_lottery_schedule(name, hour, minute):
    scheduler.add_job(
        send_lottery_guidance,
        "cron",
        hour=hour,
        minute=minute,
        args=[name],
        timezone=bkk_tz,
        id=name,
        replace_existing=True,
    )


# =========================================================
# 🎯 ตารางตั้งชื่อหวยและเวลาส่งอัตโนมัติ
# =========================================================
add_lottery_schedule("ลาวExtar", 8, 0)
add_lottery_schedule("นิเคอิเช้า+VIP", 8, 30)
add_lottery_schedule("ฮานอยอาเซียน", 8, 30)
add_lottery_schedule("จีนเช้า+VIP", 9, 30)
add_lottery_schedule("ลาวTV", 10, 0)
add_lottery_schedule("ฮั่งเช้า+VIP", 10, 0)
add_lottery_schedule("ฮานอยHD", 10, 30)
add_lottery_schedule("ใต้หวัน+VIP", 11, 0)
add_lottery_schedule("ฮานอยStar", 11, 30)
add_lottery_schedule("เกาหลี+VIP", 12, 0)
add_lottery_schedule("นิเคอิบ่าย+VIP", 12, 30)
add_lottery_schedule("ลาวHD", 13, 0)
add_lottery_schedule("จีนบ่าย+VIP", 13, 10)
add_lottery_schedule("ฮานอยTV", 13, 30)
add_lottery_schedule("ฮั่งเส็งบ่าย+VIP", 14, 30)
add_lottery_schedule("ลาวสตาร์", 15, 0)
add_lottery_schedule("สิงคโปร์+VIP", 15, 20)
add_lottery_schedule("ฮานอยกาชาด", 15, 30)
add_lottery_schedule("ไทยเย็น", 16, 0)
add_lottery_schedule("ฮานอยพิเศษ", 16, 30)
add_lottery_schedule("ฮานอยสามัคคี", 16, 30)
add_lottery_schedule("ฮานอยปกติ", 17, 30)
add_lottery_schedule("ฮานอยVIP", 18, 30)
add_lottery_schedule("ฮานอยพัฒนา", 18, 30)
add_lottery_schedule("ลาวสามัคคี", 19, 30)
add_lottery_schedule("ลาวอาเซียน", 20, 0)
add_lottery_schedule("ลาวVIP", 20, 30)
add_lottery_schedule("ลาวสามัคคีVIP", 20, 30)
add_lottery_schedule("3รัฐ+VIP", 21, 10)
add_lottery_schedule("ลาวสตาร์VIP", 21, 10)
add_lottery_schedule("ฮานอยExtar", 21, 30)
add_lottery_schedule("ลาวกาชาด", 22, 10)
add_lottery_schedule("ดาวโจนส์+VIP", 23, 30)
add_lottery_schedule("ประชาชนลาว", 2, 32)

# 🟢 เริ่มทำงาน Scheduler ทันที
if not scheduler.running:
    scheduler.start()
    print("📌 Scheduler เริ่มทำงานเรียบร้อยแล้ว!")


# --- Webhook Routes ---
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

    if user_msg.startswith("ขอแนวทาง"):
        lottery_name = user_msg.replace("ขอแนวทาง", "").strip()
        if not lottery_name:
            lottery_name = "หวยประจำวัน"

        message_text = generate_lottery_message(lottery_name)
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=message_text)
        )

    elif user_msg in ["แนวทาง", "แนวทางหวย"]:
        message_text = generate_lottery_message("หวยประจำวัน")
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=message_text)
        )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
