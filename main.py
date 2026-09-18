from flask import Flask, abort, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
app = Flask(name)
line_bot_api = LineBotApi(os.environ.get("CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.environ.get("CHANNEL_SECRET"))
@app.route("/callback", methods=["POST"])
def callback():
 signature = request.headers["X-Line-Signature"]
 body = request.get_data(as_text=True)
 try:
 handler.handle(body, signature)
 except InvalidSignatureError:
 abort(400)
 return "OK"
 @handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
 line_bot_api.reply_message(
 event.reply_token, TextSendMessage(text=event.message.text)
)
if name == "main":
app.run()
