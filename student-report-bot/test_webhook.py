from flask import Flask, request

app = Flask(__name__)

@app.route("/line_callback", methods=["GET", "POST"])
def line_callback():
    if request.method == "GET":
        print("收到 LINE GET 測試")
        return "OK", 200
    if request.method == "POST":
        print("收到 LINE POST 測試")
        print(request.headers)
        print(request.data)
        return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
