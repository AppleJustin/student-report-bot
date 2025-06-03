from generate_report import generate_reports
from simple_broadcast_test import send_broadcast_test
from line_utils import send_text

def run_all():
    # 執行 generate_report.py
    print("🚀 執行報表生成與LINE推播")
    generate_reports()

    # 執行 simple_broadcast_test.py
    print("\n🚀 執行廣播測試")
    send_broadcast_test()

    # 執行 test_send_text.py（手動設置測試 User ID）
    print("\n🚀 執行推播測試訊息")
    test_user_id = "jc0108955"  # 這裡填你測試用 User ID
    test_message = "🎉 測試訊息：系統串接成功！"
    send_text(test_user_id, test_message)

if __name__ == "__main__":
    run_all()
