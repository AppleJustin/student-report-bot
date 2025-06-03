# LINE Bot API 測試程式
import requests
import json

# ===== API憑證設定 =====
CHANNEL_ACCESS_TOKEN = "mTS8jHgrpVIOU12AC/q+FUFPrxetZjMbZxF7+Td9ldSoMIADOUh7Cj8k7qNGwiDrmYMIDDVjesBOTJLWlRaNX94KvbO/Z5EHN45sofx7s2NUxcO9Wt1QA06HcZUv4xQF2MN2oFUu06TB+WiCCePKsQdB04t89/1O/w1cDnyilFU="

# 測試用的User ID (你需要替換為真實的User ID)
TEST_USER_ID = "YOUR_USER_ID_HERE"  # 等等教你如何取得

def test_bot_info():
    """
    測試1：檢查Bot資訊
    """
    print("🔍 測試1：檢查Bot基本資訊")
    print("=" * 40)
    
    try:
        url = "https://api.line.me/v2/bot/info"
        headers = {
            'Authorization': f'Bearer {CHANNEL_ACCESS_TOKEN}'
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            bot_info = response.json()
            print("✅ Bot連線成功！")
            print(f"📱 Bot名稱: {bot_info.get('displayName', 'N/A')}")
            print(f"🆔 Bot ID: {bot_info.get('userId', 'N/A')}")
            print(f"📊 Basic ID: {bot_info.get('basicId', 'N/A')}")
            print(f"🏷️ Premium ID: {bot_info.get('premiumId', 'N/A')}")
            return True
        else:
            print(f"❌ Bot連線失敗: {response.status_code}")
            print(f"錯誤訊息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 測試錯誤: {e}")
        return False

def send_test_message(user_id):
    """
    測試2：發送測試訊息
    """
    if user_id == "YOUR_USER_ID_HERE":
        print("⚠️ 請先設置真實的User ID才能測試發送訊息")
        return False
    
    print(f"\n📱 測試2：發送測試訊息給 {user_id}")
    print("=" * 40)
    
    try:
        url = "https://api.line.me/v2/bot/message/push"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {CHANNEL_ACCESS_TOKEN}'
        }
        
        # 測試訊息
        data = {
            "to": user_id,
            "messages": [
                {
                    "type": "text",
                    "text": "🎉 恭喜！育名補習班LINE Bot測試成功！\n\n📚 成績通知系統已準備就緒\n💪 即將為家長提供自動化成績報表服務！"
                }
            ]
        }
        
        response = requests.post(url, headers=headers, data=json.dumps(data))
        
        if response.status_code == 200:
            print("✅ 測試訊息發送成功！")
            print("📱 請檢查你的LINE是否收到訊息")
            return True
        else:
            print(f"❌ 測試訊息發送失敗: {response.status_code}")
            print(f"錯誤訊息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 發送測試訊息錯誤: {e}")
        return False

def send_flex_test_message(user_id):
    """
    測試3：發送Flex Message成績報表樣式
    """
    if user_id == "YOUR_USER_ID_HERE":
        print("⚠️ 請先設置真實的User ID才能測試Flex Message")
        return False
    
    print(f"\n📊 測試3：發送Flex Message成績報表給 {user_id}")
    print("=" * 40)
    
    try:
        url = "https://api.line.me/v2/bot/message/push"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {CHANNEL_ACCESS_TOKEN}'
        }
        
        # 測試用的Flex Message
        flex_message = {
            "type": "flex",
            "altText": "陳禹彤 12月成績報表",
            "contents": {
                "type": "bubble",
                "header": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "12月成績報表",
                            "weight": "bold",
                            "size": "xl",
                            "color": "#ffffff"
                        },
                        {
                            "type": "text",
                            "text": "陳禹彤 同學",
                            "size": "md",
                            "color": "#ffffff"
                        }
                    ],
                    "backgroundColor": "#4CAF50",
                    "paddingAll": "20px"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "班級",
                                    "size": "sm",
                                    "color": "#555555"
                                },
                                {
                                    "type": "text",
                                    "text": "Whale",
                                    "size": "sm",
                                    "color": "#111111",
                                    "align": "end"
                                }
                            ]
                        },
                        {
                            "type": "separator",
                            "margin": "md"
                        },
                        {
                            "type": "text",
                            "text": "週考成績",
                            "weight": "bold",
                            "size": "md",
                            "margin": "md"
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "12/06",
                                    "size": "sm",
                                    "color": "#555555"
                                },
                                {
                                    "type": "text",
                                    "text": "95分",
                                    "size": "sm",
                                    "color": "#111111",
                                    "align": "end"
                                }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "12/13",
                                    "size": "sm",
                                    "color": "#555555"
                                },
                                {
                                    "type": "text",
                                    "text": "89分",
                                    "size": "sm",
                                    "color": "#111111",
                                    "align": "end"
                                }
                            ]
                        },
                        {
                            "type": "separator",
                            "margin": "md"
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "平均分數",
                                    "size": "md",
                                    "color": "#555555",
                                    "weight": "bold"
                                },
                                {
                                    "type": "text",
                                    "text": "92.0分",
                                    "size": "md",
                                    "color": "#FF6B35",
                                    "align": "end",
                                    "weight": "bold"
                                }
                            ],
                            "margin": "md"
                        }
                    ]
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "💪 持續保持努力！加油！",
                            "size": "sm",
                            "color": "#666666",
                            "align": "center"
                        }
                    ],
                    "margin": "md"
                }
            }
        }
        
        data = {
            "to": user_id,
            "messages": [flex_message]
        }
        
        response = requests.post(url, headers=headers, data=json.dumps(data))
        
        if response.status_code == 200:
            print("✅ Flex Message測試發送成功！")
            print("📱 請檢查你的LINE是否收到漂亮的成績報表")
            return True
        else:
            print(f"❌ Flex Message發送失敗: {response.status_code}")
            print(f"錯誤訊息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 發送Flex Message錯誤: {e}")
        return False

def get_qr_code_info():
    """
    顯示如何取得Bot QR Code和User ID
    """
    print("\n📱 如何取得Bot QR Code和User ID：")
    print("=" * 50)
    print("1. 用手機打開LINE")
    print("2. 點擊右上角的掃描QR Code")
    print("3. 掃描Bot的QR Code (在LINE Official Account Manager中)")
    print("4. 或搜尋Bot ID: @427bebpo")
    print("5. 加Bot為好友")
    print("6. 發送任何訊息給Bot")
    print("7. 查看server log取得你的User ID")
    print("\n💡 暫時可以先用你自己的LINE來測試")

def main():
    """
    主要測試流程
    """
    print("🚀 育名補習班 LINE Bot API 測試")
    print("=" * 50)
    
    # 測試1：檢查Bot資訊
    if test_bot_info():
        print("\n✅ 恭喜！LINE Bot API連線正常")
        
        # 顯示如何取得User ID
        get_qr_code_info()
        
        # 如果有User ID，可以測試發送訊息
        if TEST_USER_ID != "YOUR_USER_ID_HERE":
            send_test_message(TEST_USER_ID)
            send_flex_test_message(TEST_USER_ID)
        else:
            print("\n📝 下一步：")
            print("1. 取得你的LINE User ID")
            print("2. 更新程式中的TEST_USER_ID")
            print("3. 測試發送訊息功能")
            print("4. 整合到成績報表系統")
    else:
        print("\n❌ API設定有問題，請檢查Channel Access Token")

if __name__ == "__main__":
    main()