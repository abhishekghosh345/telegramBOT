import telebot
import requests
import re
import os
import json

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# ---- Extract real video URL from new Terabox links ----
def get_direct_link(share_url):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": share_url
    }

    # First request: get share page HTML
    html = requests.get(share_url, headers=headers).text

    # Find JSON containing file information
    match = re.search(r'window\.preload\s*=\s*(\{.*?\});', html, re.S)
    if not match:
        return None

    data = json.loads(match.group(1))

    # Extract dlink
    try:
        dlink = data["file_list"][0]["dlink"]
        return dlink
    except:
        return None


# ---- Downloading function ----
def download_video(url, filename):
    r = requests.get(url, stream=True)
    with open(filename, "wb") as f:
        for chunk in r.iter_content(1024 * 1024):
            if chunk:
                f.write(chunk)


# ---- Telegram bot handlers ----

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🎥 Send a TeraBox video link, I will download it!")


@bot.message_handler(func=lambda m: True)
def handle(message):
    link = message.text.strip()

    if "terabox" not in link:
        bot.reply_to(message, "❌ Invalid link. Send a real TeraBox URL.")
        return

    bot.reply_to(message, "⏳ Extracting video link...")

    direct = get_direct_link(link)
    if not direct:
        bot.reply_to(message, "❌ Could not extract video URL. TeraBox changed format.")
        return

    bot.reply_to(message, "⬇️ Downloading video...")

    filename = "video.mp4"
    download_video(direct, filename)

    with open(filename, "rb") as v:
        bot.send_video(message.chat.id, v)

    os.remove(filename)


print("Bot running...")
bot.polling(none_stop=True)
