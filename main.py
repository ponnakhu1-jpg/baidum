// ใส่ Channel Access Token จาก LINE Developers Console
const CHANNEL_ACCESS_TOKEN = "0PnXQOQjvPvhuqMyF42RTEcfGdDr1xKFKzIFJh1oCXgmJngQcRPAOd85pWwQg0G3/jc1g+UYEuIccUao7WlVQQMwob+/ScM4MtqN6K1T+8Gyk6igcFbU2k0ZRvOh+8Aediu90MrLXX0QWy4xC+anIQdB04t89/1O/w1cDnyilFU=";
const USER_ID = "ใส่_LINE_USER_ID_หรือ_GROUP_ID_เป้าหมายที่นี่"; // ดู User ID ได้ที่หน้า LINE Developers หรือรับจาก Webhook

// ฟังก์ชันสำหรับส่งข้อความ Push Message
function pushMessage(text) {
  const url = "https://api.line.me/v2/bot/message/push";
  
  const payload = {
    to: USER_ID,
    messages: [
      {
        type: "text",
        text: text
      }
    ]
  };

  const options = {
    method: "post",
    headers: {
      "Content-Type": "application/json",
      "Authorization": "Bearer " + CHANNEL_ACCESS_TOKEN
    },
    payload: JSON.stringify(payload)
  };

  UrlFetchApp.fetch(url, options);
}

// ฟังก์ชันที่จะถูกเรียกทำงานตามเวลาที่ตั้งไว้
function sendScheduledMessage() {
  const message = "สวัสดีครับ! นี่คือข้อความแจ้งเตือนอัตโนมัติประจำวัน ⏰";
  pushMessage(message);
}
