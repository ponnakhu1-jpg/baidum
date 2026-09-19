import atexit
import fcntl
import os
import random
import pytz
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from bs4 import BeautifulSoup
from flask import Flask, abort, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# --- ดึงค่า คีย์และ ID จาก Environment Variables ---
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get(
    "LINE_CHANNEL_ACCESS_TOKEN",
    "QW21xCzezYiuNSO+xrm2q+frEeWsecnQt64yjbsjXZOBOffIbuMK8JtovDewX8ccJ+kEmsVd8XyBi2j7JO5cvNmswWabXZtggtIepp+EePspovDsPPaai8U/Lc18qvxEFHIUHsFg6pZwfz+wVmjOFwdB04t89/1O/w1cDnyilFU=",
)
LINE_CHANNEL_SECRET = os.environ.get(
    "LINE_CHANNEL_SECRET", "5903d4e92852c68911adbf23df10f01d"
)
TARGET_GROUP_ID = os.environ.get(
    "TARGET_GROUP_ID", "Cd9bd5f0a1640666114ff9dd35912ea75"
).strip()

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

bkk_tz = pytz.timezone("Asia/Bangkok")


def get_thai_date():
  thai_months = [
      "",
      "มกราคม",
      "กุมภาพันธ์",
      "มีนาคม",
      "เมษายน",
      "พฤษภาคม",
      "มิถุนายน",
      "กรกฎาคม",
      "สิงหาคม",
      "กันยายน",
      "ตุลาคม",
      "พฤศจิกายน",
      "ธันวาคม",
  ]
  now = datetime.now(bkk_tz) if "datetime" in globals() else None
  # ใช้ datetime แบบปลอดภัย
  from datetime import datetime

  now = datetime.now(bkk_tz)
  return f"{now.day} {thai_months[now.month]} {now.year + 543}"


# --- 1. ฟังก์ชันดึงผลหวยจากเว็บไซต์ jaywaijing.co ---
def fetch_jaywaijing_result(lottery_name):
  try:
    target_url = "https://jaywaijing.co/home"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(target_url, headers=headers, timeout=10)
    if response.status_code != 200:
      return None

    soup = BeautifulSoup(response.text, "html.parser")
    clean_name = (
        lottery_name.replace("VIP", "")
        .replace("(", " ")
        .replace(")", " ")
        .strip()
    )
    keywords = [kw for kw in clean_name.split() if kw]

    if not keywords:
      keywords = [lottery_name]

    candidates = []
    for tag in soup.find_all(["div", "tr", "li", "p", "span", "td"]):
      text = tag.get_text(" ", strip=True)
      if all(kw in text for kw in keywords):
        if any(char.isdigit() for char in text):
          if len(text) < 180:
            candidates.append(text)

    unique_candidates = []
    for c in candidates:
      if c not in unique_candidates:
        unique_candidates.append(c)

    if unique_candidates:
      return "\n".join(unique_candidates[:2])

    return None
  except Exception as e:
    print(f"❌ Error fetching: {e}")
    return None


# --- 2. ฟังก์ชันสร้างข้อความแนวทางหวย ---
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


# --- 3. ฟังก์ชันส่งแนวทางหวยอัตโนมัติตามชื่อหวย ---
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


# --- 4. ระบบ Scheduler ตั้งเวลาส่งอัตโนมัติ (พร้อมตารางเวลาครบถ้วนของคุณ) ---
scheduler = BackgroundScheduler(timezone=bkk_tz)


def start_scheduler():
  lock_file_path = "/tmp/lottery_scheduler.lock"
  try:
    fp = open(lock_file_path, "wb")
    fcntl.flock(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
  except (IOError, OSError):
    print(
        "⚠️ Worker อื่นกำลังรัน Scheduler อยู่แล้ว ปิดใช้งานใน Worker"
        " นี้เพื่อป้องกันข้อความเบิ้ล"
    )
    return

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

  # ตารางเวลาของคุณครบทุกรายการตามเดิมเป๊ะๆ
  add_lottery_schedule("ลาวExtar", 8, 0)
  add_lottery_schedule("นิเคอิเช้า+VIP", 8, 30)
  add_lottery_schedule("ฮานอยอาเซียน", 8, 30)
  add_lottery_schedule("จีนเช้า+VIP", 9, 30)
  add_lottery_schedule("ลาวTV", 10, 0)
  add_lottery_schedule("ฮั่งเช้า+VIP", 10, 0)
  add_lottery_schedule("ฮานอยHD", 10, 30)
  add_lottery_schedule("ใต้หวัน+VIP", 11, 0)
  add_lottery_schedule("ฮานอยStar", 11, 30)
  add_lottery_schedule("เกาหลี+VIP", 11, 47)
  add_lottery_schedule("นิเคอิบ่าย+VIP", 12, 43)
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
  add_lottery_schedule("ฮานอยปกติ", 17, 5)
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
  add_lottery_schedule("ประชาชนลาว", 3, 30)
  add_lottery_schedule("ลาวสันติภาพ", 3, 31)

  if not scheduler.running:
    scheduler.start()
    print("📌 Scheduler เริ่มทำงานพร้อมตารางเวลาครบถ้วนแล้ว!")

  atexit.register(lambda: scheduler.shutdown(wait=False))


start_scheduler()


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


# --- 5. ระบบตอบกลับข้อความในไลน์ ---
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

  # 2. ตรวจผลหวยจากเว็บไซต์ jaywaijing.co (เพิ่มกลับมาให้สมบูรณ์)
  if user_msg.startswith("ผลหวย") or user_msg.startswith("ตรวจหวย"):
    lottery_name = user_msg.replace("ผลหวย", "").replace("ตรวจหวย", "").strip()

    if not lottery_name:
      line_bot_api.reply_message(
          event.reply_token,
          TextSendMessage(
              text="กรุณาระบุชื่อหวยที่ต้องการตรวจด้วยครับ\nเช่น 'ผลหวยนิเคอิ เช้า'"
          ),
      )
      return

    web_result = fetch_jaywaijing_result(lottery_name)

    if web_result:
      result_text = (
          f"🟢 ผลรางวัล {lottery_name} (ใบดำนำโชค)\n"
          f"📅 ประจำวันที่: {get_thai_date()}\n"
          f"━━━━━━━━━━━━━━━\n"
          f"{web_result}\n"
          f"━━━━━━━━━━━━━━━"
      )
    else:
      result_text = (
          f"🟢 ผลรางวัล {lottery_name} (ใบดำนำโชค)\n"
          f"📅 ประจำวันที่: {get_thai_date()}\n"
          f"━━━━━━━━━━━━━━━\n"
          f"❌ ยังไม่พบผลรางวัลของ '{lottery_name}' จากเว็บไซต์ในขณะนี้"
      )

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
