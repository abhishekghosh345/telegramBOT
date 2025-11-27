import telebot
import requests
import re
import os

BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
bot = telebot.TeleBot(BOT_TOKEN)

# -------- Extract shareid + uk from Terabox link ----------
def extract_ids(url):
    match = re.search(r'share\/(\w+)\?uk=(\d+)', url)
    if match:
        return match.group(1), match.group(2)
    return None, None

# -------- Get direct download URL ----------
def get_direct_link(terabox_url):
    shareid, uk = extract_ids(terabox_url)

    if not shareid or not uk:
        return None

    api_url = f"https://www.1024terabox.com/share/list?shareid={shareid}&uk={uk}"
    r = requests.get(api_url, headers={'User-Agent': 'Mozilla/5.0'})

    try:
        file_url = r.json()['list'][0]['dlink']
        return file_url
    except:
        return None

# -------- Download file locally ----------
def download_video(url, filename):
    r = requests.get(url, stream=True)
    with open(filename, "wb") as f:
        for chunk in r.iter_content(1024*1024):
            f.write(chunk)

@bot.message_handler(commands=['start'])
def start(msg):
    bot.reply_to(msg,
        "🎬 Send me a **TeraBox video link** and I will download it for you!")

@bot.message_handler(func=lambda m: True)
def handle_link(message):
    url = message.text.strip()

    if "terabox" not in url:
        bot.reply_to(message, "❌ Please send a valid **TeraBox link**.")
        return

    bot.reply_to(message, "⏳ Fetching real video link...")

    direct = get_direct_link(url)
    if not direct:
        bot.reply_to(message, "❌ Unable to extract direct video URL.")
        return

    bot.reply_to(message, "⬇️ Downloading video... Please wait...")

    filename = "video.mp4"
    download_video(direct, filename)

    bot.send_video(message.chat.id, open(filename, "rb"))

    os.remove(filename)

bot.polling()
