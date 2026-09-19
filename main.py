import os
import random
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
from flask import Flask, abort, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# --- ค่าคอนฟิกและ Token ---
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

# 🗄️ หน่วยความจำสำรองสำหรับระบบเซ็ตผล (กรณีต้องการกำหนดเอง)
manual_results_db = {}


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


# --- 1. ฟังก์ชันดึงผลหวยจากเว็บไซต์เป้าหมาย ---
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
      return None

    soup = BeautifulSoup(response.text, "html.parser")
    page_text = soup.get_text()

    extracted_lines = []
    # ทำความสะอาดคำค้นหา
    search_keywords = lottery_name.replace("VIP", "").strip().split()

    for line in page_text.split("\n"):
      cleaned = line.strip()
      if cleaned and all(kw in cleaned for kw in search_keywords):
        extracted_lines.append(cleaned)

    if extracted_lines:
      return "\n".join(extracted_lines[:3])

    return None
  except Exception as e:
    print(f"❌ Error fetching web: {e}")
    return None


# --- 2. ฟังก์ชันสร้างข้อความแนวทางหวย ---
def generate_lottery_message(lottery_name="หวยประจำวัน"):
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
  return "Line Bot ใบดำนำโชค is running smoothly!", 200


@app.route("/callback", methods=["POST"])
def callback():
  signature = request.headers.get("X-Line-Signature")
  body = request.get_data(as_text=True)

  try:
    handler.handle(body, signature)
  except InvalidSignatureError:
    abort(400)

  return "OK"


# --- 3. ระบบจัดการข้อความใน LINE ---
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
  user_msg = event.message.text.strip()

  if event.source.type == "group":
    print(f"📌 Group ID ปัจจุบันคือ: {event.source.group_id}")

  # คำสั่งขอไอดีกลุ่ม
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

  # คำสั่งเซ็ตผลสำรอง: เซ็ตผล [ชื่อหวย] [3ตัวบน] [2ตัวล่าง]
  if user_msg.startswith("เซ็ตผล"):
    parts = user_msg.split()
    if len(parts) >= 4:
      lottery_name = " ".join(parts[1:-2])
      top_num = parts[-2]
      bottom_num = parts[-1]

      manual_results_db[lottery_name] = {
          "top": top_num,
          "bottom": bottom_num,
          "date": get_thai_date(),
      }

      line_bot_api.reply_message(
          event.reply_token,
          TextSendMessage(
              text=(
                  f"✅ บันทึกผลสำรองสำเร็จ!\nหวย: {lottery_name}\nสามตัวบน:"
                  f" {top_num}\nสองตัวล่าง: {bottom_num}"
              )
          ),
      )
    else:
      line_bot_api.reply_message(
          event.reply_token,
          TextSendMessage(
              text=(
                  "รูปแบบคำสั่งไม่ถูกต้อง\nกรุณาใช้: เซ็ตผล [ชื่อหวย] [3ตัวบน]"
                  " [2ตัวล่าง]"
              )
          ),
      )
    return

  # คำสั่งตรวจผลหวย: พิมพ์ "ผลหวย..." หรือ "ตรวจหวย..."
  if user_msg.startswith("ผลหวย") or user_msg.startswith("ตรวจหวย"):
    lottery_name = (
        user_msg.replace("ผลหวย", "").replace("ตรวจหวย", "").strip()
    )
    if not lottery_name:
      line_bot_api.reply_message(
          event.reply_token,
          TextSendMessage(
              text=(
                  "กรุณาระบุชื่อหวยด้วยครับ\nเช่น 'ผลหวยนิเคอิบ่าย VIP'"
                  " หรือ 'ผลหวยฮานอย'"
              )
          ),
      )
      return

    # ค้นหาจากเว็บไซต์หลักก่อน
    web_result = fetch_lottery_result_from_web(lottery_name)

    if web_result:
      result_text = (
          f"🟢 ผลรางวัล {lottery_name} (ใบดำนำโชค)\n"
          f"📅 ประจำวันที่: {get_thai_date()}\n"
          f"━━━━━━━━━━━━━━━\n"
          f"{web_result}\n"
          f"━━━━━━━━━━━━━━━"
      )
    elif lottery_name in manual_results_db:
      # ถ้าเว็บไม่เจอ ใช้ผลสำรองที่เซ็ตไว้
      data = manual_results_db[lottery_name]
      result_text = (
          f"🟢 ผลรางวัล {lottery_name} (ใบดำนำโชค)\n"
          f"📅 ประจำวันที่: {data['date']}\n"
          f"━━━━━━━━━━━━━━━\n"
          f"สามตัวบน: {data['top']}\n"
          f"สองตัวล่าง: {data['bottom']}\n"
          f"━━━━━━━━━━━━━━━\n"
          f"(ข้อมูลจากระบบสำรอง)"
      )
    else:
      result_text = (
          f"🟢 ผลรางวัล {lottery_name} (ใบดำนำโชค)\n"
          f"📅 ประจำวันที่: {get_thai_date()}\n"
          f"━━━━━━━━━━━━━━━\n"
          f"❌ ยังไม่พบข้อมูลผลรางวัลของ '{lottery_name}' ในขณะนี้\n"
          f"(สามารถพิมพ์ 'เซ็ตผล {lottery_name} [3ตัว] [2ตัว]' เพื่อบันทึกผลสำรองได้)"
      )

    line_bot_api.reply_message(
        event.reply_token, TextSendMessage(text=result_text)
    )
    return

  # คำสั่งขอแนวทาง
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
