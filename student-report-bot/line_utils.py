import requests, json

CHANNEL_ACCESS_TOKEN = "mTS8jHgrpVIOU12AC/q+FUFPrxetZjMbZxF7+Td9ldSoMIADOUh7Cj8k7qNGwiDrmYMIDDVjesBOTJLWlRaNX94KvbO/Z5EHN45sofx7s2NUxcO9Wt1QA06HcZUv4xQF2MN2oFUu06TB+WiCCePKsQdB04t89/1O/w1cDnyilFU="

def test_bot_info():
    url = "https://api.line.me/v2/bot/info"
    headers = {'Authorization': f'Bearer {CHANNEL_ACCESS_TOKEN}'}
    r = requests.get(url, headers=headers)
    return r.status_code == 200

def send_text(user_id, text):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {CHANNEL_ACCESS_TOKEN}'
    }
    payload = {"to": user_id, "messages":[{"type":"text","text":text}]}
    r = requests.post(url, headers=headers, data=json.dumps(payload))
    return r.status_code == 200

def send_file(user_id, file_url, file_name):
    # 修改為發送包含下載連結的文字訊息
    return send_text(user_id, f"📎 {file_name}\n請點擊以下連結下載：\n{file_url}")

def send_flex(user_id, alt_text, contents):
    """
    user_id: 要推送的家長 Line ID
    alt_text: 無法顯示 Flex 時的替代文字
    contents: 完整的 Flex bubble JSON (dict)
    """
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {CHANNEL_ACCESS_TOKEN}'
    }
    payload = {
        "to": user_id,
        "messages": [{
            "type": "flex",
            "altText": alt_text,
            "contents": contents
        }]
    }
    r = requests.post(url, headers=headers, data=json.dumps(payload))
    return r.status_code == 200
