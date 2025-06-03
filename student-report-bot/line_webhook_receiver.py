# line_webhook_receiver.py - 簡化版 Webhook 接收器
from flask import Flask, request
import json
import csv
from datetime import datetime

app = Flask(__name__)

# 你現有的LINE Bot Token
CHANNEL_ACCESS_TOKEN = "mTS8jHgrpVIOU12AC/q+FUFPrxetZjMbZxF7+Td9ldSoMIADOUh7Cj8k7qNGwiDrmYMIDDVjesBOTJLWlRaNX94KvbO/Z5EHN45sofx7s2NUxcO9Wt1QA06HcZUv4xQF2MN2oFUu06TB+WiCCePKsQdB04t89/1O/w1cDnyilFU="

@app.route("/webhook", methods=['POST'])
def webhook():
    """接收LINE訊息的Webhook"""
    print("🔔 收到 Webhook 請求！")
    
    try:
        # 取得請求內容
        body = request.get_data(as_text=True)
        print(f"📨 接收到的資料: {body}")
        
        # 解析JSON
        events = json.loads(body)['events']
        
        for event in events:
            print(f"📋 事件類型: {event['type']}")
            
            # 如果是訊息事件
            if event['type'] == 'message':
                user_id = event['source']['userId']
                message_text = event['message']['text']
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                print(f"✅ 收到訊息！")
                print(f"🆔 User ID: {user_id}")
                print(f"💬 訊息內容: {message_text}")
                print(f"⏰ 時間: {timestamp}")
                
                # 儲存到CSV檔案
                save_user_id(user_id, message_text, timestamp)
                
                # 回覆確認訊息
                reply_to_user(event['replyToken'], user_id)
        
        return 'OK', 200
        
    except Exception as e:
        print(f"❌ 處理Webhook時發生錯誤: {e}")
        return 'OK', 200  # 即使錯誤也回傳200，避免LINE重複發送

def save_user_id(user_id, message, timestamp):
    """儲存User ID到CSV檔案"""
    try:
        user_id_file = "collected_user_ids.csv"
        
        # 檢查檔案是否存在，不存在則建立標題行
        try:
            with open(user_id_file, 'r', encoding='utf-8'):
                pass
        except FileNotFoundError:
            with open(user_id_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['時間', 'User ID', '訊息內容', '備註'])
        
        # 附加新的User ID記錄
        with open(user_id_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, user_id, message, '家長發送'])
        
        print(f"✅ User ID已儲存到 {user_id_file}")
        
    except Exception as e:
        print(f"❌ 儲存User ID時發生錯誤: {e}")

def reply_to_user(reply_token, user_id):
    """回覆訊息給用戶"""
    import requests
    
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {CHANNEL_ACCESS_TOKEN}'
    }
    
    data = {
        "replyToken": reply_token,
        "messages": [
            {
                "type": "text",
                "text": f"✅ 收到您的訊息！\n\n🆔 您的User ID已記錄：\n{user_id}\n\n📋 補習班會使用此ID發送成績報表。"
            }
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            print("✅ 回覆訊息發送成功")
        else:
            print(f"❌ 回覆訊息失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 回覆訊息時發生錯誤: {e}")

@app.route("/users", methods=['GET'])
def show_users():
    """顯示所有收集到的User ID"""
    try:
        users_html = "<h1>📋 收集到的家長User ID</h1>"
        users_html += "<table border='1' style='border-collapse: collapse; width: 100%;'>"
        users_html += "<tr style='background-color: #f2f2f2;'><th>時間</th><th>User ID</th><th>訊息內容</th><th>備註</th></tr>"
        
        with open("collected_user_ids.csv", 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # 跳過標題行
            for row in reader:
                users_html += f"<tr><td>{row[0]}</td><td style='font-family: monospace;'>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td></tr>"
        
        users_html += "</table>"
        users_html += "<br><p>📝 請複製上面的User ID到 parents.csv 檔案中</p>"
        return users_html
        
    except FileNotFoundError:
        return "<h1>📂 還沒有收集到任何User ID</h1><p>🔄 請請家長發送訊息給LINE Bot</p>"
    except Exception as e:
        return f"<h1>❌ 錯誤</h1><p>{e}</p>"

@app.route("/health")
def health():
    """健康檢查"""
    return {"status": "ok", "message": "LINE Webhook Server is running", "port": 5001}

if __name__ == "__main__":
    print("🚀 啟動LINE Webhook接收器")
    print("=" * 60)
    print("📍 伺服器運行在: http://localhost:5000")
    print("🌐 ngrok URL: https://dcf3-111-184-192-110.ngrok-free.app/")
    print("📨 Webhook端點: /webhook")
    print("👁️ 查看收集的User ID: /users")
    print("=" * 60)
    
    # 啟動Flask伺服器 (使用 port 5000，配合ngrok)
    app.run(host='0.0.0.0', port=5002, debug=False)