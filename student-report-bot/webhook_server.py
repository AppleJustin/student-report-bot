from flask import Flask, request
import requests
import json

CHANNEL_ACCESS_TOKEN = "mTS8jHgrpVIOU12AC/q+FUFPrxetZjMbZxF7+Td9ldSoMIADOUh7Cj8k7qNGwiDrmYMIDDVjesBOTJLWlRaNX94KvbO/Z5EHN45sofx7s2NUxcO9Wt1QA06HcZUv4xQF2MN2oFUu06TB+WiCCePKsQdB04t89/1O/w1cDnyilFU="

app = Flask(__name__)

def send_text_reply(reply_token, text):
    url = 'https://api.line.me/v2/bot/message/reply'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {CHANNEL_ACCESS_TOKEN}'
    }
    data = {
        'replyToken': reply_token,
        'messages': [{'type': 'text', 'text': text}]
    }
    try:
        r = requests.post(url, headers=headers, data=json.dumps(data))
        print("[send_text_reply] 回應狀態", r.status_code, r.text)
    except Exception as e:
        print(f"[send_text_reply] LINE回覆API錯誤: {e}")

@app.route("/line_callback", methods=["POST", "GET"])
def line_callback():
    if request.method == "GET":
        return "LINE Webhook OK", 200
    try:
        data = request.get_json(silent=True) or {}
        events = data.get("events", [])
        print("收到 LINE events:", events)
        for event in events:
            # follow event（加好友）
            if event.get("type") == "follow" and "userId" in event.get("source", {}):
                user_id = event["source"]["userId"]
                reply_token = event.get("replyToken")
                send_text_reply(reply_token, f"🎉 您已加入好友！\n您的 LINE ID 是：\n{user_id}\n請複製並提供給老師！")
            # message event
            elif event.get("type") == "message" and "userId" in event.get("source", {}):
                user_id = event["source"]["userId"]
                reply_token = event.get("replyToken")
                send_text_reply(reply_token, f"您的 LINE ID 是：\n{user_id}\n請複製並提供給老師！")
        return "OK", 200
    except Exception as e:
        print(f"webhook 錯誤: {e}, 原始資料: {request.data}")
        return "OK", 200
