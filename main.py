import os
from flask import Flask, request, abort
from dotenv import load_dotenv

from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

# โหลดค่าต่าง ๆ จากไฟล์ .env
load_dotenv()

app = Flask(__name__)

channel_secret = os.getenv('edc04916b82d3f178f4ce7809876f214')
channel_access_token = os.getenv('0PnXQOQjvPvhuqMyF42RTEcfGdDr1xKFKzIFJh1oCXgmJngQcRPAOd85pWwQg0G3/jc1g+UYEuIccUao7WlVQQMwob+/ScM4MtqN6K1T+8Gyk6igcFbU2k0ZRvOh+8Aediu90MrLXX0QWy4xC+anIQdB04t89/1O/w1cDnyilFU=')

configuration = Configuration(access_token=channel_access_token)
handler = WebhookHandler(channel_secret)

# Webhook Endpoint สำหรับรับ Event จาก LINE
@app.route("/webhook", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Check channel secret/access token.")
        abort(400)

    return 'OK'

# ฟังก์ชันจัดการข้อความประเภท Text (Echo Bot: ตอบกลับข้อความเดิม)
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        
        # ส่งข้อความกลับหาผู้ใช้
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=event.message.text)]
            )
        )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
