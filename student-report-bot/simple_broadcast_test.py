# 簡單廣播測試程式 - 發送給所有好友
import requests
import json

# API憑證
CHANNEL_ACCESS_TOKEN = "mTS8jHgrpVIOU12AC/q+FUFPrxetZjMbZxF7+Td9ldSoMIADOUh7Cj8k7qNGwiDrmYMIDDVjesBOTJLWlRaNX94KvbO/Z5EHN45sofx7s2NUxcO9Wt1QA06HcZUv4xQF2MN2oFUu06TB+WiCCePKsQdB04t89/1O/w1cDnyilFU="

def send_broadcast_test():
    """
    發送廣播訊息給所有好友（包括你）
    """
    print("📱 LINE廣播測試")
    print("=" * 30)
    print("這個測試會發送訊息給所有加Bot為好友的人")
    print("請確認你已經加@427bebpo為好友")
    
    confirm = input("\n是否繼續測試？(y/n): ").lower()
    if confirm != 'y':
        print("測試取消")
        return
    
    try:
        url = "https://api.line.me/v2/bot/message/broadcast"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {CHANNEL_ACCESS_TOKEN}'
        }
        
        # 測試訊息
        data = {
            "messages": [
                {
                    "type": "text",
                    "text": "🎉 育名補習班LINE Bot廣播測試！\n\n📚 這是成績通知系統的測試訊息\n💪 如果你收到這則訊息，表示系統運作正常！\n\n🚀 即將開始提供自動化成績報表服務"
                }
            ]
        }
        
        print("\n發送廣播訊息中...")
        response = requests.post(url, headers=headers, data=json.dumps(data))
        
        if response.status_code == 200:
            print("✅ 廣播訊息發送成功！")
            print("📱 請檢查你的LINE是否收到訊息")
            print("💡 如果收到訊息，表示API完全正常！")
            
            # 發送成績報表樣式測試
            send_grade_report_test()
            
        else:
            print(f"❌ 發送失敗: {response.status_code}")
            print(f"錯誤: {response.text}")
            
            if response.status_code == 403:
                print("\n💡 可能原因：")
                print("1. 沒有好友加Bot")
                print("2. Channel Access Token有問題")
            
    except Exception as e:
        print(f"❌ 錯誤: {e}")

def send_grade_report_test():
    """
    發送成績報表樣式測試
    """
    print("\n📊 發送成績報表樣式測試...")
    
    try:
        url = "https://api.line.me/v2/bot/message/broadcast"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {CHANNEL_ACCESS_TOKEN}'
        }
        
        # 成績報表Flex Message
        flex_message = {
            "type": "flex",
            "altText": "📊 育名補習班成績報表測試",
            "contents": {
                "type": "bubble",
                "header": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "📊 12月成績報表",
                            "weight": "bold",
                            "size": "xl",
                            "color": "#ffffff"
                        },
                        {
                            "type": "text",
                            "text": "測試學生",
                            "size": "md",
                            "color": "#ffffff",
                            "margin": "sm"
                        }
                    ],
                    "backgroundColor": "#27AE60",
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
                                    "text": "🏫 班級",
                                    "size": "sm",
                                    "color": "#555555",
                                    "flex": 0
                                },
                                {
                                    "type": "text",
                                    "text": "育名補習班",
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
                            "text": "📝 週考成績",
                            "weight": "bold",
                            "size": "md",
                            "margin": "md",
                            "color": "#2C3E50"
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "2024-12-06週考",
                                    "size": "sm",
                                    "color": "#555555"
                                },
                                {
                                    "type": "text",
                                    "text": "95分",
                                    "size": "sm",
                                    "color": "#27AE60",
                                    "align": "end",
                                    "weight": "bold"
                                }
                            ],
                            "margin": "sm"
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "2024-12-13週考",
                                    "size": "sm",
                                    "color": "#555555"
                                },
                                {
                                    "type": "text",
                                    "text": "89分",
                                    "size": "sm",
                                    "color": "#27AE60",
                                    "align": "end",
                                    "weight": "bold"
                                }
                            ],
                            "margin": "sm"
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "2024-12-20週考",
                                    "size": "sm",
                                    "color": "#555555"
                                },
                                {
                                    "type": "text",
                                    "text": "92分",
                                    "size": "sm",
                                    "color": "#27AE60",
                                    "align": "end",
                                    "weight": "bold"
                                }
                            ],
                            "margin": "sm"
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
                                    "text": "📊 平均分數",
                                    "size": "md",
                                    "color": "#2C3E50",
                                    "weight": "bold"
                                },
                                {
                                    "type": "text",
                                    "text": "92.0分",
                                    "size": "lg",
                                    "color": "#E74C3C",
                                    "align": "end",
                                    "weight": "bold"
                                }
                            ],
                            "margin": "md"
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "🎯 月評量",
                                    "size": "md",
                                    "color": "#2C3E50",
                                    "weight": "bold"
                                },
                                {
                                    "type": "text",
                                    "text": "優秀",
                                    "size": "md",
                                    "color": "#E74C3C",
                                    "align": "end",
                                    "weight": "bold"
                                }
                            ],
                            "margin": "sm"
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
                            "color": "#95A5A6",
                            "align": "center"
                        },
                        {
                            "type": "text",
                            "text": "📞 如有問題請聯絡補習班",
                            "size": "xs",
                            "color": "#BDC3C7",
                            "align": "center",
                            "margin": "sm"
                        }
                    ],
                    "margin": "md"
                }
            }
        }
        
        data = {
            "messages": [flex_message]
        }
        
        response = requests.post(url, headers=headers, data=json.dumps(data))
        
        if response.status_code == 200:
            print("✅ 成績報表樣式發送成功！")
            print("📱 請檢查LINE是否收到漂亮的成績報表")
        else:
            print(f"❌ 成績報表發送失敗: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 成績報表錯誤: {e}")

def main():
    print("🚀 育名補習班 LINE Bot 功能測試")
    print("=" * 40)
    print("📋 測試項目：")
    print("1. 廣播文字訊息")
    print("2. 成績報表樣式訊息")
    print("\n⚠️ 注意：這會發送給所有Bot好友")
    
    send_broadcast_test()

if __name__ == "__main__":
    main()