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
line_bot_api = LineBotApi(8l6t6NJgXUUjwrt/YavacA7PGqoeS1wfIoUdekiKou4sfXupjJEBL9ikB9vlG862/jc1g+UYEuIccUao7WlVQQMwob+/ScM4MtqN6K1T+8FIqYlYG8voCE+/M1Kg3mpYnCtr6Rj955vtJLMDWTj4SgdB04t89/1O/w1cDnyilFU=)
# รบกวนแทนที่ด้วย Channel Secret จากหน้า LINE Developers
handler = WebhookHandler(fc2446b9341250dd4225d76fb497f28e)

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
