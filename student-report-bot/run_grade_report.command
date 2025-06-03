#!/bin/bash
cd "$(dirname "$0")"       # 自動切換到腳本所在資料夾
# 推薦用 python3，避免系統 python2 問題
python3 generate_report.py
echo ""
echo "===== 執行完畢，請按任意鍵關閉視窗 ====="
read -n 1