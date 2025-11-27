import os
import requests
from flask import Flask, request
import telegram

TOKEN = os.environ.get("BOT_TOKEN")
bot = telegram.Bot(token=TOKEN)

app = Flask(__name__)

TERA_API = "https://api.teraembed.com/v1/extract?url="

def extract_terabox(url):
    try:
        r = requests.get(TERA_API + url, timeout=20)
        data = r.json()

        if data.get("status") != "success":
            return None, None

        return data.get("title"), data.get("download_url")

    except Exception as e:
        print("Terabox error:", e)
        return None, None


@app.route('/webhook', methods=['POST'])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)

    if update.message and update.message.text:
        text = update.message.text.strip()

        # Detect Terabox URL
        if "terabox" in text:
            chat_id = update.message.chat.id
            bot.send_message(chat_id, "🔎 Extracting Terabox video...")

            title, dl_url = extract_terabox(text)

            if dl_url:
                bot.send_message(chat_id, f"📥 Downloading: {title}")
                try:
                    video_bytes = requests.get(dl_url, timeout=60).content
                    bot.send_video(chat_id, video_bytes)
                except Exception as e:
                    bot.send_message(chat_id, f"❌ Failed sending video: {e}")
            else:
                bot.send_message(chat_id, "❌ Unable to extract video. Link invalid or private.")

    return "OK"


@app.route('/', methods=['GET'])
def home():
    return "Bot is running!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
