import os
import requests
import json
import tempfile
from flask import Flask, request, jsonify

# --- Config ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # https://your-app.onrender.com/webhook
PORT = int(os.environ.get("PORT", 10000))
TEA_API = "https://api.teraembed.com/v1/extract?url="  # public extractor endpoint

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN env var is required")

if not WEBHOOK_URL:
    print("WARNING: WEBHOOK_URL not set. You can set it in Render env or via setWebhook call manually.")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
TELEGRAM_FILE_API = f"https://api.telegram.org/file/bot{BOT_TOKEN}"

app = Flask(__name__)

# --- Helpers ---
def send_message(chat_id, text):
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, json=payload, timeout=15)
    except Exception as e:
        print("send_message error:", e)

def extract_terabox(url):
    """Use teraembed public extractor. Returns (title, download_url) or (None, None)."""
    try:
        r = requests.get(TEA_API + url, timeout=20)
        if r.status_code != 200:
            print("teraembed status", r.status_code, r.text)
            return None, None
        data = r.json()
        if data.get("status") != "success":
            print("teraembed not success:", data)
            return None, None
        return data.get("title") or "video.mp4", data.get("download_url")
    except Exception as e:
        print("extract_terabox error:", e)
        return None, None

def download_bytes(url, timeout=60):
    """Return bytes of content or None."""
    try:
        r = requests.get(url, stream=True, timeout=timeout)
        r.raise_for_status()
        return r.content
    except Exception as e:
        print("download_bytes error:", e)
        return None

def send_video_bytes(chat_id, video_bytes, filename="video.mp4"):
    """
    Send video bytes to Telegram by multipart upload.
    Use requests.post to /sendVideo with files param.
    """
    url = f"{TELEGRAM_API}/sendVideo"
    files = {"video": (filename, video_bytes)}
    data = {"chat_id": chat_id}
    try:
        r = requests.post(url, data=data, files=files, timeout=120)
        if r.status_code != 200:
            print("sendVideo failed:", r.status_code, r.text)
            return False
        return True
    except Exception as e:
        print("send_video_bytes error:", e)
        return False

# --- Webhook routes ---
@app.route("/", methods=["GET"])
def index():
    return "Terabox bot is running", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json(force=True)
    if not update:
        return jsonify({"ok": False}), 400

    # Basic message handling
    message = update.get("message") or update.get("edited_message")
    if not message:
        return jsonify({"ok": True}), 200

    chat_id = message["chat"]["id"]

    # If message contains text and terabox link
    text = message.get("text", "") or message.get("caption", "")
    if not text:
        send_message(chat_id, "Send a Terabox share link (https://...terabox.com/...).")
        return jsonify({"ok": True}), 200

    # Detect terabox link
    if "terabox" not in text.lower():
        send_message(chat_id, "I only support TeraBox links. Send a TeraBox share URL.")
        return jsonify({"ok": True}), 200

    # Process terabox link
    send_message(chat_id, "🔎 Extracting Terabox video link...")
    title, dl_url = extract_terabox(text.strip())

    if not dl_url:
        send_message(chat_id, "❌ Could not extract direct video link. Link private or extractor failed.")
        return jsonify({"ok": True}), 200

    send_message(chat_id, f"📥 Downloading `{title}` (this may take a while) ...")

    video_bytes = download_bytes(dl_url, timeout=120)
    if not video_bytes:
        send_message(chat_id, "❌ Failed to download the video from Terabox.")
        return jsonify({"ok": True}), 200

    send_message(chat_id, f"⬆️ Sending `{title}` back to you ...")
    ok = send_video_bytes(chat_id, video_bytes, filename=title if title.endswith(".mp4") else "video.mp4")

    if ok:
        send_message(chat_id, "✅ Done — video sent.")
    else:
        send_message(chat_id, "❌ Failed to send video to Telegram (maybe file too large).")

    return jsonify({"ok": True}), 200

# --- Set webhook on startup (attempt) ---
def set_telegram_webhook():
    if not WEBHOOK_URL:
        return
    set_url = f"{TELEGRAM_API}/setWebhook"
    try:
        r = requests.post(set_url, json={"url": WEBHOOK_URL}, timeout=15)
        print("setWebhook response:", r.status_code, r.text)
    except Exception as e:
        print("setWebhook error:", e)

if __name__ == "__main__":
    # attempt to set webhook automatically on start
    print("Starting bot; attempting to set webhook to", WEBHOOK_URL)
    set_telegram_webhook()

    # Use the PORT env that Render sets
    app.run(host="0.0.0.0", port=PORT)
