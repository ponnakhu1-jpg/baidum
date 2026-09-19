import os
import random
import requests  # ใช้ดึงข้อมูลเว็บแบบเบาสบาย
from bs4 import BeautifulSoup  # ใช้แกะข้อความใน HTML
from datetime import datetime, timedelta, timezone
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


# --- 1. ฟังก์ชันดึงผลหวยด้วย Requests + BeautifulSoup (เร็วและไม่ใช้ Chrome) ---
def fetch_lottery_result_from_web(lottery_name):
  try:
    target_url = "https://xn--t3cmiit.com/stock-lottery#vip"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    response = requests.get(target_url, headers=headers, timeout=10)
    if response.status_code != 200:
      return (
          f"🟢 ผลรางวัล {lottery_name} (ใบดำนำโชค)\n"
          f"📅 ประจำวันที่: {get_thai_date()}\n"
          f"━━━━━━━━━━━━━━━\n"
          f"❌ ไม่สามารถเชื่อมต่อกับเว็บไซต์เป้าหมายได้"
      )

    # แกะข้อความด้วย BeautifulSoup
    soup = BeautifulSoup(response.text, "html.parser")
    page_text = soup.get_text()

    extracted_lines = []
    for line in page_text.split("\n"):
      cleaned_line = line.strip()
      if cleaned_line and lottery_name in cleaned_line:
        extracted_lines.append(cleaned_line)

    if extracted_lines:
      result_detail = "\n".join(extracted_lines[:3])
      return (
          f"🟢 ผลรางวัล {lottery_name} (ใบดำนำโชค)\n"
          f"📅 ประจำวันที่: {get_thai_date()}\n"
          f"━━━━━━━━━━━━━━━\n"
          f"{result_detail}\n"
          f"━━━━━━━━━━━━━━━"
      )

    return (
        f"🟢 ผลรางวัล {lottery_name} (ใบดำนำโชค)\n"
        f"📅 ประจำวันที่: {get_thai_date()}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"❌ ยังไม่พบข้อมูลผลรางวัลของ '{lottery_name}' จากเว็บไซต์ในขณะนี้"
    )

  except Exception as e:
    print(f"❌ Error during scraping: {e}")
    return (
        f"🟢 ผลรางวัล {lottery_name} (ใบดำนำโชค)\n"
        f"📅 ประจำวันที่: {get_thai_date()}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"❌ เกิดข้อผิดพลาดในการดึงข้อมูล: {e}"
    )


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
  return "Line Bot ใบดำนำโชค (Requests Engine) is running smoothly!", 200


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

  # 2. ตรวจผลหวยอัตโนมัติจากเว็บ
  if user_msg.startswith("ผลหวย") or user_msg.startswith("ตรวจหวย"):
    lottery_name = (
        user_msg.replace("ผลหวย", "").replace("ตรวจหวย", "").strip()
    )
    if not lottery_name:
      line_bot_api.reply_message(
          event.reply_token,
          TextSendMessage(
              text=(
                  "กรุณาระบุชื่อหวยด้วยครับ\nเช่น 'ผลหวยนิเคอิ' หรือ"
                  " 'ผลหวยฮานอย'"
              )
          ),
      )
      return

    result_text = fetch_lottery_result_from_web(lottery_name)
    line_bot_api.reply_message(
        event.reply_token, TextSendMessage(text=result_text)
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
