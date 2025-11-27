import telebot
import os
from flask import Flask, request

TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Telegram webhook URL
WEBHOOK_URL = os.getenv('WEBHOOK_URL')  # Example: https://your-app.onrender.com/webhook

@app.route('/' , methods=['GET'])
def index():
    return "Bot running!", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_str = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return '', 200
    else:
        return "Invalid", 403

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Hello! Bot is working via webhook!")

if __name__ == "__main__":
    # Remove old webhook
    bot.remove_webhook()

    # Set new webhook
    bot.set_webhook(url=WEBHOOK_URL)

    # Start Flask app
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
