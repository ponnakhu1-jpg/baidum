from flask import Flask, request, abort

from linebot import (
 LineBotApi, WebhookHandler
)
from linebot.exceptions import (
 InvalidSignatureError
)
from linebot.models import (MessageEvent, TextMessage, TextSendMessage,)
app=Flask(__name__)
# รบกวนแทนที่ด้วย Channel Access Token จากหน้า LINE Developers
line_bot_api = LineBotApi('YOUR_CHANNEL_ACCESS_TOKEN')
# รบกวนแทนที่ด้วย Channel Secret จากหน้า LINE Developers
handler = WebhookHandler('YOUR_CHANNEL_SECRET')

@app.route("/callback", methods=['POST'])
def callback():
 signature = request.headers['X-Line-Signature']
 body = request.get_data(as_text=True)
 app.logger.info("Request body: " + body)

 try:
     handler.handle(body, signature)
 except InvalidSignatureError:
  print("Invalid signature. Please check your channel access token/channel secret.")
 abort(400)
 return 'OK'
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
 line_bot_api.reply_message(
 event.reply_token,
 TextSendMessage(text=event.message.text)
  )
if __name__ =="__main__":
    app.run()