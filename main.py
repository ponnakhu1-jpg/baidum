import os
import random
from datetime import datetime
import pytz
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

# ตัวแปรเก็บผลหวยชั่วคราวในระบบบอท
lottery_database = {
    "ฮานอย": {"top": "824", "bottom": "16"},
    "ลาว": {"top": "182", "bottom": "82"},
}


# --- ฟังก์ชันช่วยแปลงวันที่เป็นภาษาไทย ---
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


# --- 1. ฟังก์ชันสร้างข้อความแนวทางหวย ---
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


# --- 2. ฟังก์ชันส่งแนวทางหวยอัตโนมัติตามชื่อหวย ---
def send_lottery_guidance(lottery_name="แนวทางหวย"):
  message_text = generate_lottery_message(lottery_name)
  try:
    target_id = os.environ.get("TARGET_GROUP_ID", TARGET_GROUP_ID).strip()
    if not target_id or not target_id.startswith("C"):
      print(f"❌ Error: TARGET_GROUP_ID [{target_id}] ไม่ถูกต้อง")
      return

    line_bot_api.push_message(
        target_id, messages=TextSendMessage(text=message_text)
    )
    print(f"✅ ส่งแนวทาง [{lottery_name}] เรียบร้อยแล้ว!")
  except Exception as e:
    print(f"❌ เกิดข้อผิดพลาด: {e}")


# --- Webhook & API Routes ---
@app.route("/", methods=["GET"])
def home():
  return "Line Bot ใบดำนำโชค is running!", 200


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

  # 2. คำสั่งสำหรับแอดมินตั้งค่าผลหวย: พิมพ์ "เซ็ตผล ฮานอย 824 16"
  if user_msg.startswith("เซ็ตผล") or user_msg.startswith("ตั้งค่าผล"):
    parts = user_msg.split()
    if len(parts) >= 4:
      l_name = parts[1]
      top_val = parts[2]
      bot_val = parts[3]

      lottery_database[l_name] = {"top": top_val, "bottom": bot_val}

      line_bot_api.reply_message(
          event.reply_token,
          TextSendMessage(
              text=(
                  f"✅ บันทึกผล {l_name} เรียบร้อย!\n"
                  f"สามตัวบน: {top_val} | สองตัวล่าง: {bot_val}"
              )
          ),
      )
    else:
      line_bot_api.reply_message(
          event.reply_token,
          TextSendMessage(
              text="⚠️ รูปแบบไม่ถูกต้อง\nตัวอย่าง: เซ็ตผล ฮานอย 824 16"
          ),
      )
    return

  # 3. สมาชิกหรือแอดมินพิมพ์ตรวจผล: พิมพ์ "ผลหวยฮานอย" หรือ "ตรวจหวยฮานอย"
  if user_msg.startswith("ผลหวย") or user_msg.startswith("ตรวจหวย"):
    lottery_name = (
        user_msg.replace("ผลหวย", "").replace("ตรวจหวย", "").strip()
    )
    if not lottery_name:
      line_bot_api.reply_message(
          event.reply_token,
          TextSendMessage(
              text=(
                  "กรุณาระบุชื่อหวยด้วยครับ\nเช่น 'ผลหวยฮานอย' หรือ 'ผลหวยลาว'"
              )
          ),
      )
      return

    # ค้นหาชื่อหวยในระบบที่บันทึกไว้
    found_result = None
    for key in lottery_database:
      if key in lottery_name:
        found_result = lottery_database[key]
        break

    if found_result:
      result_text = (
          f"🟢 ผลรางวัล {lottery_name} (ใบดำนำโชค)\n"
          f"📅 ประจำวันที่: {get_thai_date()}\n"
          f"━━━━━━━━━━━━━━━\n"
          f"สามตัวบน: {found_result['top']}\n"
          f"สองตัวล่าง: {found_result['bottom']}\n"
          f"━━━━━━━━━━━━━━━"
      )
    else:
      result_text = (
          f"🟢 ผลรางวัล {lottery_name} (ใบดำนำโชค)\n"
          f"📅 ประจำวันที่: {get_thai_date()}\n"
          f"━━━━━━━━━━━━━━━\n"
          f"❌ ยังไม่มีข้อมูลผลของ '{lottery_name}' ในระบบ\n"
          f"(แอดมินสามารถพิมพ์ 'เซ็ตผล {lottery_name} [3ตัว] [2ตัว]' เพื่อบันทึกได้ครับ)"
      )

    line_bot_api.reply_message(
        event.reply_token, TextSendMessage(text=result_text)
    )
    return

  # 4. ขอแนวทางระบุชื่อ
  if user_msg.startswith("ขอแนวทาง"):
    lottery_name = user_msg.replace("ขอแนวทาง", "").strip()
    if not lottery_name:
      lottery_name = "หวยประจำวัน"

    message_text = generate_lottery_message(lottery_name)
    line_bot_api.reply_message(
        event.reply_token, TextSendMessage(text=message_text)
    )
    return

  # 5. ขอแนวทางทั่วไป
  if user_msg in ["แนวทาง", "แนวทางหวย"]:
    message_text = generate_lottery_message("หวยประจำวัน")
    line_bot_api.reply_message(
        event.reply_token, TextSendMessage(text=message_text)
    )
    return


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
