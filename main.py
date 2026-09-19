import os
import random
import time
from datetime import datetime, timedelta, timezone
from flask import Flask, abort, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# ไลบรารีสำหรับดึงข้อมูลจากเว็บแบบอัตโนมัติ (Selenium)
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

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

# กำหนดโซนเวลาประเทศไทย (UTC+7)
bkk_tz = timezone(timedelta(hours=7))


# --- ฟังก์ชันแปลงวันที่เป็นภาษาไทย ---
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
  now = datetime.now(bkk_tz)
  day = now.day
  month = thai_months[now.month]
  year = now.year + 543
  return f"{day} {month} {year}"


# --- 1. ฟังก์ชันดึงผลหวยจากเว็บไซต์เป้าหมายอัตโนมัติ ---
def fetch_lottery_result_from_web(lottery_name):
  """ฟังก์ชันใช้ Selenium จำลองเปิดเว็บเพื่อกวาดตัวเลขผลหวยอัตโนมัติ"""
  try:
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # รันแบบซ่อนหน้าจอ
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")

    # ติดตั้งและเปิดเบราว์เซอร์จำลอง
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # 🔗 ใส่ URL เว็บไซต์ที่คุณต้องการให้บอทวิ่งเข้าไปดึงข้อมูลตรงนี้
    # (เปลี่ยนเป็นลิงก์เว็บจริงที่คุณใช้งานอยู่)
    target_url = "https://example.com/lottery-results"
    driver.get(target_url)

    # รอให้หน้าเว็บโหลด JavaScript แสดงผลตัวเลขสักครู่ (ปรับเวลาได้ตามความเหมาะสม)
    time.sleep(3)

    # ตัวอย่าง: ค้นหาข้อความหรือดึงข้อมูลจากตารางหน้าเว็บ
    # (คุณสามารถปรับ Selector ของ BeautifulSoup หรือ Selenium ตามโครงสร้างเว็บจริงได้ที่นี่)
    page_text = driver.find_element(By.TAG_NAME, "body").text
    driver.quit()

    # สมมติฐาน: ถ้าดึงข้อความจากเว็บมาได้ เราจะนำมาคัดกรองหรือส่งกลับไป
    # หากเว็บมีรูปแบบเฉพาะ สามารถเขียนโค้ดตัดคำ (Parsing) เพิ่มตรงนี้ได้ครับ
    return {
        "top": "กำลังดึงข้อมูล...",
        "bottom": "กำลังดึงข้อมูล...",
        "raw": page_text,
    }

  except Exception as e:
    print(f"❌ Error fetching web: {e}")
    return None


# --- 2. ฟังก์ชันสร้างข้อความแนวทางหวย ---
def generate_lottery_message(lottery_name="แนวทางหวย"):
  root_numbers = random.sample(range(0, 10), 2)
  spot_numbers = random.sample(range(0, 100), 10)
  sets = random.sample(range(0, 1000), 6)

  message_text = (
      f"📌 แนวทาง {lottery_name} (ใบดำนำโชค)\n"
      f"📅 ประจำวันที่: {get_thai_date()}\n"
      f"เลขรูด:{','.join(map(str, root_numbers))}\n"
      f"เลขเจาะ:{','.join(f'{int(x):02d}' for x in spot_numbers)}\n"
      f"6กลับ:{','.join(f'{int(x):03d}' for x in sets)}"
  )
  return message_text


# --- Webhook & API Routes ---
@app.route("/", methods=["GET"])
def home():
  return "Line Bot ใบดำนำโชค (Auto Scraping) is running!", 200


@app.route("/callback", methods=["POST"])
def callback():
  signature = request.headers.get("X-Line-Signature")
  body = request.get_data(as_text=True)

  try:
    handler.handle(body, signature)
  except InvalidSignatureError:
    abort(400)

  return "OK"


# --- 3. ระบบตอบกลับข้อความในไลน์ ---
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

  # 2. ตรวจผลหวย: พิมพ์ "ผลหวยฮานอย" หรือ "ตรวจหวยนิเคอิ" -> ให้บอทวิ่งไปดึงจากเว็บอัตโนมัติ
  if user_msg.startswith("ผลหวย") or user_msg.startswith("ตรวจหวย"):
    lottery_name = (
        user_msg.replace("ผลหวย", "").replace("ตรวจหวย", "").strip()
    )
    if not lottery_name:
      line_bot_api.reply_message(
          event.reply_token,
          TextSendMessage(
              text=(
                  "กรุณาระบุชื่อหวยด้วยครับ\nเช่น 'ผลหวยฮานอย' หรือ 'ผลหวยนิเคอิ'"
              )
          ),
      )
      return

    # แจ้งเตือนสถานะกำลังดึงข้อมูล
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=(
                f"⏳ กำลังดึงผลรางวัล '{lottery_name}'"
                " จากเว็บไซต์อัตโนมัติ..."
            )
        ),
    )

    # เรียกใช้ฟังก์ชันดึงข้อมูลจากเว็บ
    web_data = fetch_lottery_result_from_web(lottery_name)

    if web_data:
      result_text = (
          f"🟢 ผลรางวัล {lottery_name} (ใบดำนำโชค)\n"
          f"📅 ประจำวันที่: {get_thai_date()}\n"
          f"━━━━━━━━━━━━━━━\n"
          f"สามตัวบน: {web_data['top']}\n"
          f"สองตัวล่าง: {web_data['bottom']}\n"
          f"━━━━━━━━━━━━━━━\n"
          f"(ดึงข้อมูลจากเว็บไซต์อัตโนมัติสำเร็จ)"
      )
    else:
      result_text = (
          f"❌ ไม่สามารถดึงข้อมูลผลรางวัล '{lottery_name}' จากเว็บไซต์ได้ในขณะนี้"
      )

    # ส่งผลลัพธ์กลับเข้าแชท
    target_id = (
        event.source.group_id
        if event.source.type == "group"
        else event.source.user_id
    )
    line_bot_api.push_message(
        target_id, messages=TextSendMessage(text=result_text)
    )
    return

  # 3. ขอแนวทาง
  if user_msg.startswith("ขอแนวทาง") or user_msg in ["แนวทาง", "แนวทางหวย"]:
    lottery_name = user_msg.replace("ขอแนวทาง", "").strip()
    if not lottery_name or lottery_name in ["แนวทาง", "แนวทางหวย"]:
      lottery_name = "หวยประจำวัน"

    message_text = generate_lottery_message(lottery_name)
    line_bot_api.reply_message(
        event.reply_token, TextSendMessage(text=message_text)
    )
    return


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
