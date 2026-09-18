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
line_bot_api = LineBotApi('0PnXQOQjvPvhuqMyF42RTEcfGdDr1xKFKzIFJh1oCXgmJngQcRPAOd85pWwQg0G3/jc1g+UYEuIccUao7WlVQQMwob+/ScM4MtqN6K1T+8Gyk6igcFbU2k0ZRvOh+8Aediu90MrLXX0QWy4xC+anIQdB04t89/1O/w1cDnyilFU=')
# รบกวนแทนที่ด้วย Channel Secret จากหน้า LINE Developers
handler = WebhookHandler('edc04916b82d3f178f4ce7809876f214')

@app.route("/callback", methods=['POST'])
def callback():
 signature = request.headers['X-Line-Signature']
 body = request.get_data()
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
