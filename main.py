import random 
from apscheduler.schedulers.background import BackgroundScheduler
import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = '0PnXQOQjvPvhuqMyF42RTEcfGdDr1xKFKzIFJh1oCXgmJngQcRPAOd85pWwQg0G3/jc1g+UYEuIccUao7WlVQQMwob+/ScM4MtqN6K1T+8Gyk6igcFbU2k0ZRvOh+8Aediu90MrLXX0QWy4xC+anIQdB04t89/1O/w1cDnyilFU='
LINE_CHANNEL_SECRET = 'edc04916b82d3f178f4ce7809876f214'
scheduler=BackgroundScheduler
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/", methods=['GET'])
def home():
    return "OK", 200

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    print(event.source.group_id)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"คุณส่งข้อความว่า: {event.message.text}")
    )
def send lottery guidance():
    root/_numbers=random.sample(range(0,10),2)
    spot_numbers=random.sample(range(0,100),10)
    sets=[random.sample(range(0,1000),6) for _ in range(6)]
    message_text=f"เลขรูด:{root_numbers}nเลขเจาะ:{spot_number}nชุดหวย:{sets}"
    random/_number=random.randint(10,99)
    line_bot_api.push_message('Ccd80f46ea82114a21319bc2fa4b3b264'TextSendMessage(text=message_text)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
