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

LINE_CHANNEL_ACCESS_TOKEN = os.environ.get(
    "LINE_CHANNEL_ACCESS_TOKEN",
    "QW21xCzezYiuNSO+xrm2q+frEeWsecnQt64yjbsjXZOBOffIbuMK8JtovDewX8ccJ+kEmsVd8XyBi2j7JO5cvNmswWabXZtggtIepp+EePspovDsPPaai8U/Lc18qvxEFHIUHsFg6pZwfz+wVmjOFwdB04t89/1O/w1cDnyilFU=",
)
LINE_CHANNEL_SECRET = os.environ.get(
    "LINE_CHANNEL_SECRET", "5903d4e92852c68911adbf23df10f01d"
)

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

bkk_tz = timezone(timedelta(hours=7))


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
  return f"{now.day} {thai_months[now.month]} {now.year + 543}"


# --- ฟังก์ชันดึงผลหวยจากเว็บไซต์ jaywaijing.co/home ---
def fetch_jaywaijing_result(lottery_name):
  try:
    target_url = "https://jaywaijing.co/home"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    response = requests.get(target_url, headers=headers, timeout=15)
    if response.status_code != 200:
      return None

    soup = BeautifulSoup(response.text, "html.parser")
    results_found = []

    # ทำความสะอาดคำค้นหา
    search_keywords = lottery_name.replace("VIP", "").strip().split()

    # กวาดข้อมูลจากตารางหรือบล็อกข้อความบนหน้าเว็บ
    for element in soup.find_all(["tr", "div", "li", "p", "span"]):
      element_text = element.get_text(separator=" ", strip=True)
      if element_text and all(kw in element_text for kw in search_keywords):
        if len(element_text) < 150:
          results_found.append(element_text)

    # หากไม่เจอ ให้ค้นหาจากข้อความทั้งหมดในหน้า
    if not results_found:
      page_text = soup.get_text()
      for line in page_text.split("\n"):
        cleaned = line.strip()
        if cleaned and all(kw in cleaned for kw in search_keywords):
          results_found.append(cleaned)

    # กรองข้อความซ้ำ
    unique_results = []
    for r in results_found:
      if r not in unique_results:
        unique_results.append(r)

    if unique_results:
      return "\n".join(unique_results[:3])

    return None
  except Exception as e:
    print(f"❌ Error fetching jaywaijing: {e}")
    return None


@app.route("/", methods=["GET"])
def home():
  return "Line Bot Jaywaijing Parser is running!", 200


@app.route("/callback", methods=["POST"])
def callback():
  signature = request.headers.get("X-Line-Signature")
  body = request.get_data(as_text=True)
  try:
    handler.handle(body, signature)
  except InvalidSignatureError:
    abort(400)
  return "OK"


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
  user_msg = event.message.text.strip()

  # ตรวจผลหวย
  if user_msg.startswith("ผลหวย") or user_msg.startswith("ตรวจหวย"):
    lottery_name = (
        user_msg.replace("ผลหวย", "").replace("ตรวจหวย", "").strip()
    )
    if not lottery_name:
      line_bot_api.reply_message(
          event.reply_token,
          TextSendMessage(text="กรุณาระบุชื่อหวย เช่น 'ผลหวยนิเคอิบ่าย VIP'"),
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

  # ขอแนวทาง
  if user_msg.startswith("ขอแนวทาง") or user_msg in ["แนวทาง", "แนวทางหวย"]:
    l_name = user_msg.replace("ขอแนวทาง", "").strip() or "หวยประจำวัน"
    root_numbers = random.sample(range(0, 10), 2)
    spot_numbers = random.sample(range(0, 100), 10)
    sets = random.sample(range(0, 1000), 6)
    msg = (
        f"📌 แนวทาง {l_name} (ใบดำนำโชค)\n"
        f"📅 ประจำวันที่: {get_thai_date()}\n"
        f"เลขรูด:{','.join(map(str, root_numbers))}\n"
        f"เลขเจาะ:{','.join(f'{int(x):02d}' for x in spot_numbers)}\n"
        f"6กลับ:{','.join(f'{int(x):03d}' for x in sets)}"
    )
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
    return


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
