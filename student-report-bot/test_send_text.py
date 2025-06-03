# test_send_text.py
from line_utils import send_text

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
