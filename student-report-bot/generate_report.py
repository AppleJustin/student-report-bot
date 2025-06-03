# complete_automation_system.py - 按正確順序合併你的6組程式+ngrok整合
import pandas as pd
import matplotlib
matplotlib.rcParams['font.family'] = 'AppleGothic'  # 圖表中文字支援
import matplotlib.pyplot as plt
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import os
import shutil
import re
import gspread
from google.oauth2.service_account import Credentials
import requests
import json
import time
import threading
from flask import Flask, send_file, abort
from werkzeug.serving import make_server
import urllib.parse
from datetime import datetime
from flask import Flask, request
import requests
import json

CHANNEL_ACCESS_TOKEN = "mTS8jHgrpVIOU12AC/q+FUFPrxetZjMbZxF7+Td9ldSoMIADOUh7Cj8k7qNGwiDrmYMIDDVjesBOTJLWlRaNX94KvbO/Z5EHN45sofx7s2NUxcO9Wt1QA06HcZUv4xQF2MN2oFUu06TB+WiCCePKsQdB04t89/1O/w1cDnyilFU="  # 如果前面有宣告就不用重複
webhook_app = Flask("line_userid_webhook")


# ==================== 第一組：generate_report.py 完整程式碼 ====================

# Google Sheets 設定
SPREADSHEET_ID = ""
CREDENTIALS_PATH = "invoice-automation-460003-e0efa1fbbe27.json"
OUTPUT_DIR = "output"

GRADE_CONFIGS = [

    {
        "grade_name": "先修",
        "score_sheet_id": "1ahROLPacRMtDTtn0AufOo8cfbVwlc4s5LiePdD8z_38",
        "parents_sheet_id": "1GVr9UTBAf71-iGe4keLxSj4zTYa4uiFjUdH2ntBxxjU"
    }
]


# PDF 類別（中文支援）
class GradeReportPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.add_font("HanSans", "", "fonts/SourceHanSansHC-Regular.otf")
        self.set_font("HanSans", "", 14)

    def header(self):
        self.set_font("HanSans", "", 16)
        self.cell(0, 10, self.title, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        self.ln(5)

    def student_info(self, name, class_name):
        self.set_font("HanSans", "", 12)
        self.cell(0, 10, f"學生姓名: {name}   班級: {class_name}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def score_list(self, title, items: list):
        self.set_font("HanSans", "", 12)
        self.cell(0, 10, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font("HanSans", "", 11)
        for label, value in items:
            text = f"{label}：{'缺席' if (pd.isna(value) or value == '') else value}"
            self.cell(0, 8, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(3)

    def summary(self, weekly_avg, monthly_score):
        self.set_font("HanSans", "", 11)
        text = (
            f"本月週考平均：{weekly_avg:.1f} 分；"
            f"月評量成績：{monthly_score} 分\n學習狀況良好，請持續努力！"
        )
        self.multi_cell(0, 8, text)
        self.ln(5)

    def add_score_chart(self, image_path):
        self.image(image_path, x=25, w=160)
        self.ln(10)

# 解析欄位中的月份，不處理「評量卷」等字串
def extract_month_from_label(label: str):
    label = str(label).strip()
    if "評量卷" in label:
        return None
    # MMDD 無分隔符號
    m = re.match(r"^(\d{2})(\d{2})", label)
    if m:
        month = int(m.group(1))
        if 1 <= month <= 12:
            return f"{month:02d}"
    # YYYY-MM-DD
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})", label)
    if m:
        return f"{int(m.group(2)):02d}"
    # MM/DD 或 MM-DD
    m = re.match(r"^(\d{1,2})[/-](\d{1,2})", label)
    if m and 1 <= int(m.group(1)) <= 12:
        return f"{int(m.group(1)):02d}"
    # MM月DD
    m = re.match(r"^(\d{1,2})月(\d{1,2})", label)
    if m and 1 <= int(m.group(1)) <= 12:
        return f"{int(m.group(1)):02d}"
    return None

# 判斷是否為週考欄位
def is_weekly_column(label):
    return (
        "週考" in str(label)
        and "小考" not in str(label)
        and extract_month_from_label(label) is not None
    )

# 判斷是否為月評量欄位
def is_monthly_column(label):
    return "月評量" in str(label)

# 檢查能不能轉成浮點數
def is_number(v):
    try:
        float(v)
        return True
    except:
        return False

# 主程式：從 Google Sheets 擷取資料並生成 PDF
from datetime import datetime

def parse_date_from_col(col):
    # 專抓 YYYY-MM-DD
    m = re.search(r"(\d{4}-\d{2}-\d{2})", str(col))
    if m:
        try:
            return datetime.strptime(m.group(1), "%Y-%m-%d").date()
        except:
            return None
    return None

def get_nearest_monthly_and_last4_weekly(df, today=None):
    if today is None:
        today = datetime.now().date()
    # 檢查所有欄位
    monthly_cols = []
    weekly_cols = []
    for c in df.columns:
        if "月評量" in c and parse_date_from_col(c):
            monthly_cols.append((c, parse_date_from_col(c)))
        elif "週考" in c and parse_date_from_col(c):
            weekly_cols.append((c, parse_date_from_col(c)))
    # 只留下日期<=today
    monthly_cols = [(c, d) for c, d in monthly_cols if d and d <= today]
    weekly_cols = [(c, d) for c, d in weekly_cols if d and d <= today]
    if not monthly_cols:
        return None, []
    # 找到最近的月評量（日期最大且<=today）
    nearest_mc, nearest_date = max(monthly_cols, key=lambda x: x[1])
    # 找出所有在這個月評量日期之前的週考
    prev_weeklies = [(c, d) for c, d in weekly_cols if d < nearest_date]
    # 取日期最近的4次週考
    prev_weeklies_sorted = sorted(prev_weeklies, key=lambda x: x[1], reverse=True)[:4]
    # 再按時間排序
    prev_weeklies_sorted = sorted(prev_weeklies_sorted, key=lambda x: x[1])
    return nearest_mc, prev_weeklies_sorted

def generate_reports():
    # 🚀 先自動清空舊的 output/ 資料夾
    if os.path.isdir(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    creds = Credentials.from_service_account_file(
        CREDENTIALS_PATH,
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    reports = []
    today = datetime.now().date()

    for ws in spreadsheet.worksheets():
        class_name = ws.title.strip()
        records = ws.get_all_records(empty2zero=False, default_blank="")
        df = pd.DataFrame(records)

        # 同時接受「中文姓名」或「Name」
        if "中文姓名" not in df.columns and "Name" not in df.columns:
            print(f"跳過工作表【{class_name}】，因為沒有「中文姓名」或「Name」欄位")
            continue

        print(f"處理班級：{class_name}，共 {len(df)} 位學生")

        for _, row in df.iterrows():
            raw_name = (
                str(row.get("中文姓名","")).strip()
                or str(row.get("Name","")).strip()
            )
            if not raw_name:
                continue
            name = raw_name.replace("/", "_").replace("\\", "_")

            # ===== 取得最近月評量與前4次週考 =====
            nearest_mc, last4_weeklies = get_nearest_monthly_and_last4_weekly(df, today)
            if not nearest_mc or len(last4_weeklies) < 1:
                print(f"❌ 找不到{raw_name} 最近的月評量或前4次週考，略過")
                continue

            # print最近月評量與週考的欄位和日期
            print(f"{raw_name} 最近月評量欄位：{nearest_mc}，日期：{parse_date_from_col(nearest_mc)}")
            print(f"前4次週考：{[(c, parse_date_from_col(c)) for c, _ in last4_weeklies]}")

            # 取這幾個欄位的分數
            month_score = row.get(nearest_mc, "")
            weekly_scores = [(c, row.get(c, "")) for c, _ in last4_weeklies]

            # 濾掉週考成績非數字
            weekly_scores_clean = [(c, float(v)) for c, v in weekly_scores if (v != "" and pd.notna(v) and str(v).replace('.','',1).isdigit())]
            if not weekly_scores_clean:
                print(f"❌ {raw_name} 沒有有效的週考分數，略過")
                continue
            avg4 = sum(v for _, v in weekly_scores_clean) / len(weekly_scores_clean)

            # 準備圖表資料
            dates2 = [str(parse_date_from_col(c)) for c, _ in weekly_scores_clean] + [str(parse_date_from_col(nearest_mc))]
            vals2 = [v for _, v in weekly_scores_clean]
            try:
                mv2 = float(month_score)
                vals2.append(mv2)
            except:
                vals2.append(0)

            # 繪製趨勢圖
            folder = os.path.join(OUTPUT_DIR, class_name, name)
            os.makedirs(folder, exist_ok=True)
            img_file = os.path.join(folder, f"{parse_date_from_col(nearest_mc)}_chart.png")
            plt.figure(figsize=(6,3))
            plt.plot(dates2, vals2, marker='o')
            plt.title(f"{parse_date_from_col(nearest_mc)}月評量＋前4次週考")
            plt.ylabel("分數")
            plt.ylim(0, 120)
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(img_file)
            plt.close()

            # PDF
            pdf = GradeReportPDF()
            pdf.title = f"{parse_date_from_col(nearest_mc)}月評量報表"
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()
            pdf.student_info(name, class_name)
            pdf.add_score_chart(img_file)
            pdf.score_list(
                "週考成績（最近4次）",
                [(c, row.get(c, "")) for c, _ in last4_weeklies]
            )
            pdf.score_list(
                "月評量成績",
                [(nearest_mc, month_score if month_score not in ("", None, "") else "缺席")]
            )
            pdf.summary(avg4, month_score)

            out_pdf = os.path.join(folder, f"{parse_date_from_col(nearest_mc)}月評量報表.pdf")
            pdf.output(out_pdf)
            os.remove(img_file)
            print(f"✅ 生成 {class_name}/{name} 在 {nearest_mc} 的最近月評量報表")

            reports.append({
                'student_name': raw_name,
                'class_name': class_name,
                'eval_month': str(parse_date_from_col(nearest_mc)),
                'last4_weekly': [(str(parse_date_from_col(c)), row.get(c, "")) for c, _ in last4_weeklies],
                'avg_score': avg4,
                'monthly_score': month_score
            })

    print(f"📝 共生成 {len(reports)} 筆報表資料")
    return reports




# ==================== 第二組：line_api_test.py 完整程式碼 ====================

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

def main_line_api_test():
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


# ==================== 第三組：line_utils.py 完整程式碼 ====================

def test_bot_info_utils():
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


# ==================== 第四組：simple_broadcast_test.py 完整程式碼 ====================

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

def main_broadcast_test():
    print("🚀 育名補習班 LINE Bot 功能測試")
    print("=" * 40)
    print("📋 測試項目：")
    print("1. 廣播文字訊息")
    print("2. 成績報表樣式訊息")
    print("\n⚠️ 注意：這會發送給所有Bot好友")
    
    send_broadcast_test()


# ==================== 第五組：test_send_text.py 完整程式碼 ====================

def test_send_text_function():
    """第五組程式功能"""
    # 測試用 User ID
    test_user_id = "jc0108955"
    # 測試訊息
    message = "🔍 這是測試訊息，確認 LINE Bot 傳送功能正常。"
    # 呼叫 send_text()
    success = send_text(test_user_id, message)
    # 顯示結果
    if success:
        print(f"✅ 成功傳送訊息給 {test_user_id}")
    else:
        print(f"❌ 傳送訊息給 {test_user_id} 失敗")


# ==================== 第六組：parents.csv 資料處理 ====================

def load_parents_data_from_gsheet(parents_sheet_id):
    creds = Credentials.from_service_account_file(
        CREDENTIALS_PATH,
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(parents_sheet_id)
    ws = spreadsheet.worksheets()[0]  # 通常只有一個工作表
    records = ws.get_all_records(empty2zero=False, default_blank="")
    df = pd.DataFrame(records)
    print(f"📋 載入 {len(df)} 位家長資料")
    return df



def send_flex_message_to_parent(report):
    student_name = report['student_name']
    class_name = report['class_name']
    parent_line_id = report['parent_line_id']
    eval_month = report['eval_month']
    last4_weekly = report['last4_weekly']
    avg_score = report['avg_score']
    monthly_score = report['monthly_score']

    flex_message = {
        "type": "flex",
        "altText": f"{student_name} {eval_month}月成績報表",
        "contents": {
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": f"📊 {eval_month}月成績報表", "weight": "bold", "size": "xl", "color": "#ffffff"},
                    {"type": "text", "text": f"{student_name} 同學", "size": "md", "color": "#ffffff", "margin": "sm"}
                ],
                "backgroundColor": "#27AE60",
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "box", "layout": "horizontal", "contents": [
                        {"type": "text", "text": "🏫 班級", "size": "sm", "color": "#555555", "flex": 0},
                        {"type": "text", "text": class_name, "size": "sm", "color": "#111111", "align": "end"}
                    ]},
                    {"type": "separator", "margin": "md"},
                    {"type": "text", "text": "📝 週考成績", "weight": "bold", "size": "md", "margin": "md", "color": "#2C3E50"},
                    *[
                        {"type": "box", "layout": "horizontal", "contents": [
                            {"type": "text", "text": f"{d}", "size": "sm", "color": "#555555"},
                            {"type": "text", "text": f"{v}分", "size": "sm", "color": "#27AE60", "align": "end", "weight": "bold"}
                        ], "margin": "sm"} for d, v in last4_weekly
                    ],
                    {"type": "separator", "margin": "md"},
                    {"type": "box", "layout": "horizontal", "contents": [
                        {"type": "text", "text": "📊 平均分數", "size": "md", "color": "#2C3E50", "weight": "bold"},
                        {"type": "text", "text": f"{avg_score:.1f}分", "size": "lg", "color": "#E74C3C", "align": "end", "weight": "bold"}
                    ], "margin": "md"},
                    {"type": "box", "layout": "horizontal", "contents": [
                        {"type": "text", "text": "🎯 月評量", "size": "md", "color": "#2C3E50", "weight": "bold"},
                        {"type": "text", "text": f"{monthly_score}分", "size": "md", "color": "#E74C3C", "align": "end", "weight": "bold"}
                    ], "margin": "sm"}
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "💪 持續保持努力！加油！", "size": "sm", "color": "#95A5A6", "align": "center"},
                    {"type": "text", "text": "📞 如有問題請聯絡補習班", "size": "xs", "color": "#BDC3C7", "align": "center", "margin": "sm"}
                ],
                "margin": "md"
            }
        }
    }
    return send_flex(parent_line_id, f"{student_name} {eval_month}月成績報表", flex_message['contents'])



# ==================== 主要自動化流程 ====================
def generate_reports_and_collect_data():
    return generate_reports()

def run_complete_automation():
    print("🚀 成績報表自動化系統開始")

    try:
        if not test_bot_info_utils():
            raise Exception("LINE API連線失敗")

        # ========= 1. 問老師選年級 =========
        print("\n請選擇今天要發送哪個年級的成績單？")
        for idx, config in enumerate(GRADE_CONFIGS):
            print(f"  {idx+1}: {config['grade_name']}")
        grade_choice = input("👉 請輸入數字選擇（1/2/3）：")
        if grade_choice not in [str(i+1) for i in range(len(GRADE_CONFIGS))]:
            print("❌ 無效選項，已取消")
            return
        grade_idx = int(grade_choice) - 1
        config = GRADE_CONFIGS[grade_idx]

        # ========= 2. 問老師選班級 =========
        class_name_input = input("請輸入今天要發送的班級名稱（如 Whale、A3、Dolphin 等）：").strip()
        if not class_name_input:
            print("❌ 沒有輸入班級，已取消")
            return

        # ========= 3. 後續流程僅針對此年級+班級 =========
        global SPREADSHEET_ID
        SPREADSHEET_ID = config['score_sheet_id']
        reports = generate_reports_and_collect_data()
        if not reports:
            print(f"❌ {config['grade_name']} 沒有成績資料，略過")
            return

        parents_df = load_parents_data_from_gsheet(config['parents_sheet_id'])
        if parents_df is None or parents_df.empty:
            print(f"❌ 讀取{config['grade_name']}家長名單失敗")
            return

        # ========== 容錯抓欄位名 ==========
        def find_column_case_insensitive(df, candidates):
            candidates = [c.strip().lower() for c in candidates]
            for col in df.columns:
                if col is None:
                    continue
                c_lower = str(col).strip().lower()
                if c_lower in candidates:
                    return col
                for cand in candidates:
                    if c_lower.replace(" ", "") == cand.replace(" ", ""):
                        return col
            return None

        class_col = find_column_case_insensitive(parents_df, [
            '班級', 'class', 'class name', '班級名稱'
        ])
        name_col = find_column_case_insensitive(parents_df, [
            '學生姓名', '中文姓名', '學生名字', 'name'
        ])
        lineid_col = find_column_case_insensitive(parents_df, [
            "家長LineID", "家長LINEID", "家長lineid", "LINE USER ID", "line user id", "家長 LINEID"
        ])

        # ========== 只處理選定班級的學生 ==========
        reports = [r for r in reports if r.get('class_name', '').strip() == class_name_input]

        if not reports:
            print(f"❌ 在年級【{config['grade_name']}】找不到班級【{class_name_input}】的成績資料")
            return

        # ======= 檢查點用: 整理成大表 DataFrame =======
        preview_list = []
        print("\n====== 預覽：即將發送給家長的成績報表清單 ======")
        for report in reports:
            student_name = report.get('student_name', '')
            class_name = report.get('class_name', '')
            eval_month = report.get('eval_month', '未知')
            last4_weekly = report.get('last4_weekly', [])
            avg_score = report.get('avg_score', 0)
            monthly_score = report.get('monthly_score', 0)

            parent_line_id = "(查無)"
            if class_col and name_col and lineid_col:
                row = parents_df[
                    (parents_df[class_col] == class_name) &
                    (parents_df[name_col] == student_name)
                ]
                if not row.empty:
                    parent_line_id = str(row.iloc[0][lineid_col]).strip()

            # 將 4 次週考日期與分數組合成字串
            week_data = []
            for (d, v) in last4_weekly:
                score = v if v != "" else "缺席"
                week_data.append(score)
            preview_list.append({
                '學生姓名': student_name,
                '班級': class_name,
                '月評量分數': monthly_score,
                '週考平均': round(avg_score, 1),
                '週考1': week_data[0] if len(week_data) > 0 else "",
                '週考2': week_data[1] if len(week_data) > 1 else "",
                '週考3': week_data[2] if len(week_data) > 2 else "",
                '週考4': week_data[3] if len(week_data) > 3 else "",
                '家長LineID': parent_line_id
            })
            print(f"\n學生：{student_name} | 班級：{class_name} | 家長LineID：{parent_line_id}")
            print(f"  月評量：{monthly_score} | 週考平均：{avg_score:.1f}")
            for i, (d, v) in enumerate(last4_weekly):
                print(f"    週考{i+1}：{d} -> {v if v != '' else '缺席'}")

        # ======= 產生檢查用PDF表格 =======
        if preview_list:
            preview_df = pd.DataFrame(preview_list)
            from fpdf import FPDF

            class CheckPreviewPDF(FPDF):
                def __init__(self):
                    super().__init__()
                    self.add_font("HanSans", "", "fonts/SourceHanSansHC-Regular.otf", uni=True)
                    self.set_font("HanSans", "", 10)

                def header(self):
                    self.set_font("HanSans", "", 13)
                    self.cell(0, 10, "即將發送的成績預覽清單", 0, 1, "C")
                    self.ln(3)

                def table(self, df):
                    self.set_font("HanSans", "", 10)
                    col_widths = [28, 20, 22, 22, 18, 18, 18, 18, 50]
                    columns = list(df.columns)
                    for i, col in enumerate(columns):
                        self.cell(col_widths[i], 8, str(col), 1, 0, "C")
                    self.ln()
                    for _, row in df.iterrows():
                        for i, col in enumerate(columns):
                            text = str(row[col])
                            if len(text) > 22:
                                text = text[:20] + "..."
                            self.cell(col_widths[i], 8, text, 1, 0, "C")
                        self.ln()

            pdf = CheckPreviewPDF()
            pdf.add_page()
            pdf.table(preview_df)
            os.makedirs("output", exist_ok=True)
            pdf_path = os.path.join("output", "check_preview.pdf")
            pdf.output(pdf_path)
            print(f"\n✅ 已產生檢查用PDF，請開啟檢查：{pdf_path}")
        else:
            print("\n⚠️ 無資料可預覽")

        print("\n※請人工檢查PDF及下方列表有無錯誤，確定沒問題請輸入 1 後發送，其他任何鍵取消。")
        confirm = input("👉 確認送出請輸入 1：")
        if confirm != "1":
            print("❌ 已取消發送，請檢查資料後重試！")
            return

        # ========== 真正發送 ==========
        success_count = 0
        failed_count = 0
        for report in reports:
            student_name = report.get('student_name', '')
            class_name = report.get('class_name', '')
            eval_month = report.get('eval_month', '未知')
            last4_weekly = report.get('last4_weekly', [])
            avg_score = report.get('avg_score', 0)
            monthly_score = report.get('monthly_score', 0)
            if class_col is None or name_col is None or lineid_col is None:
                print(f"❌ 缺少必要欄位，請檢查家長名單表頭拼寫")
                failed_count += 1
                continue
            row = parents_df[
                (parents_df[class_col] == class_name) &
                (parents_df[name_col] == student_name)
            ]
            if row.empty:
                print(f"❌ 找不到 {student_name} 的家長資料")
                failed_count += 1
                continue
            parent_line_id = str(row.iloc[0][lineid_col]).strip()
            report_data = {
                'student_name': student_name,
                'class_name': class_name,
                'parent_line_id': parent_line_id,
                'eval_month': eval_month,
                'last4_weekly': last4_weekly,
                'avg_score': avg_score,
                'monthly_score': monthly_score
            }
            if send_flex_message_to_parent(report_data):
                success_count += 1
                print(f"✅ 成功發送給 {student_name} 的家長")
            else:
                failed_count += 1
                print(f"❌ 發送給 {student_name} 的家長失敗")
            time.sleep(2)

        print(f"\n{config['grade_name']} 成功發送：{success_count}")
        print(f"{config['grade_name']} 發送失敗：{failed_count}")

        print("\n🎉 自動化流程完成")
        print(f"📊 總報表數：{len(reports)}")
        print(f"✅ 總成功發送：{success_count}")
        print(f"❌ 總發送失敗：{failed_count}")

    except Exception as e:
        print(f"❌ 執行失敗: {e}")
# ---- 新增 webhook server，讓家長傳訊息給 bot 自動回 userId ----

from flask import Flask, request
import threading
import requests
import json

CHANNEL_ACCESS_TOKEN = "mTS8jHgrpVIOU12AC/q+FUFPrxetZjMbZxF7+Td9ldSoMIADOUh7Cj8k7qNGwiDrmYMIDDVjesBOTJLWlRaNX94KvbO/Z5EHN45sofx7s2NUxcO9Wt1QA06HcZUv4xQF2MN2oFUu06TB+WiCCePKsQdB04t89/1O/w1cDnyilFU="

webhook_app = Flask("line_userid_webhook")

@webhook_app.route("/line_callback", methods=["POST", "GET"])
def line_callback():
    if request.method == "GET":
        return "LINE Webhook OK", 200
    try:
        data = request.get_json(silent=True) or {}
        events = data.get("events", [])
        print("收到 LINE events:", events)
        for event in events:
            # 新增：處理 follow event（新好友）
            if event.get("type") == "follow" and "userId" in event.get("source", {}):
                user_id = event["source"]["userId"]
                reply_token = event.get("replyToken")
                send_text_reply(reply_token, f"🎉 您已加入好友！\n您的 LINE ID 是：\n{user_id}\n請複製並提供給老師！")
            # 原本：收到訊息也回傳ID
            elif event.get("type") == "message" and "userId" in event.get("source", {}):
                user_id = event["source"]["userId"]
                reply_token = event.get("replyToken")
                send_text_reply(reply_token, f"您的 LINE ID 是：\n{user_id}\n請複製並提供給老師！")
        return "OK", 200
    except Exception as e:
        print(f"webhook 錯誤: {e}, 原始資料: {request.data}")
        return "OK", 200


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
        print("[send_text_reply] 準備送出資料", data)
        r = requests.post(url, headers=headers, data=json.dumps(data))
        print("[send_text_reply] LINE回覆狀態碼", r.status_code, r.text)
    except Exception as e:
        print(f"[send_text_reply] LINE回覆API錯誤: {e}")



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
        print("[send_text_reply] 準備送出內容：", data)  # 新增
        r = requests.post(url, headers=headers, data=json.dumps(data))
        print("[send_text_reply] LINE回覆狀態碼", r.status_code, r.text)  # 新增
    except Exception as e:
        print(f"[send_text_reply] LINE回覆API錯誤: {e}")


if __name__ == "__main__":
    # 啟動 webhook server 於背景 thread
    threading.Thread(target=lambda: webhook_app.run(host="0.0.0.0", port=5000), daemon=True).start()

    # 等待 2 秒，確保 webhook server 啟動
    import time
    time.sleep(2)

    # 執行你的主流程
    run_complete_automation()

