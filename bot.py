import os
import requests
from flask import Flask, request

BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
FILE_API = f"https://api.telegram.org/file/bot{BOT_TOKEN}"

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json()

    if "message" in update:
        msg = update["message"]

        # Video message
        if "video" in msg:
            file_id = msg["video"]["file_id"]
            chat_id = msg["chat"]["id"]

            # STEP 1: get file path
            r = requests.get(f"{TELEGRAM_API}/getFile?file_id={file_id}")
            result = r.json()

            file_path = result["result"]["file_path"]

            # STEP 2: download actual file
            file_url = f"{FILE_API}/{file_path}"
            video_data = requests.get(file_url).content

            # STEP 3: save file
            filename = file_path.split("/")[-1]
            save_path = os.path.join("downloads", filename)
            os.makedirs("downloads", exist_ok=True)

            with open(save_path, "wb") as f:
                f.write(video_data)

            # STEP 4: confirm message
            requests.post(f"{TELEGRAM_API}/sendMessage", json={
                "chat_id": chat_id,
                "text": f"Video saved as {filename}"
            })

    return "ok", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
