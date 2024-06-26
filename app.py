import requests
import json
import secrets
import threading
from flask import Flask, request, jsonify
import telebot

# Configuration
API_KEY_FILE = 'api_keys.txt'
OWNER_CHAT_ID = '6460703454'  # Replace with your Telegram chat ID
TELEGRAM_BOT_TOKEN = '7195510626:AAEESkdWYtD8sG-qKgHW6Sod0AsdS3E4zmY'  # Replace with your Telegram bot token

# Flask app
app = Flask(__name__)

# Define model name mappings
MODEL_NAME_MAP = {
    "llama-3-70B": "meta-llama/Llama-3-70b-chat-hf",
    "gpt-3.5-turbo": "gpt-3.5-turbo-0125",
    "mixtral-8x7B": "mistralai/Mixtral-8x7B-Instruct-v0.1"
}

# Telegram bot
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

def extract_vqd():
    status_url = "https://duckduckgo.com/duckchat/v1/status"

    status_headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
        'cache-control': "no-store",
        'x-vqd-accept': "1",
        'sec-fetch-mode': "cors",
        'referer': "https://duckduckgo.com/"
    }

    status_response = requests.get(status_url, headers=status_headers)

    # Extract the 'vqd' value from the response headers
    for key, value in status_response.headers.items():
        if key.lower().startswith('x-vqd'):
            return value

    raise ValueError("vqd value not found in the response headers")

def chat_with_model(model, system_message, content):
    vqd_value = extract_vqd()
    chat_url = "https://duckduckgo.com/duckchat/v1/chat"

    # Prepend the system message to the user's message
    combined_message = f"{system_message} {content}"

    payload = json.dumps({
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": combined_message
            }
        ]
    })

    chat_headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
        'Accept': "text/event-stream",
        'Content-Type': "application/json",
        'x-vqd-4': vqd_value,
        'sec-ch-ua-mobile': "?1",
        'origin': "https://duckduckgo.com",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'referer': "https://duckduckgo.com/"
    }

    response = requests.post(chat_url, data=payload, headers=chat_headers)

    return response.iter_lines()

def parse_response(lines):
    message_parts = []
    for line in lines:
        if line:
            line_str = line.decode('utf-8')
            if line_str.startswith('data:'):
                try:
                    data = json.loads(line_str[6:])
                    if 'message' in data:
                        message_parts.append(data.get('message', ''))
                except json.JSONDecodeError:
                    continue

    return ''.join(message_parts)

def is_valid_api_key(api_key):
    with open(API_KEY_FILE, 'r') as f:
        valid_api_keys = f.read().splitlines()
    return api_key in valid_api_keys

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json

    api_key = data.get('api_key')
    if not is_valid_api_key(api_key):
        return jsonify({"error": "Invalid API key"}), 403

    short_model_name = data.get('model')
    content = data.get('prompt')
    system_message = data.get('system_message', "You are a helpful assistant.")

    if not short_model_name or not content:
        return jsonify({"error": "Model and prompt are required"}), 400

    # Map short model name to full model name
    model = MODEL_NAME_MAP.get(short_model_name)
    if not model:
        return jsonify({"error": "Invalid model name"}), 400

    try:
        lines = chat_with_model(model, system_message, content)
        complete_message = parse_response(lines)
        return jsonify({"response": complete_message})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Hi! Use /generate to create a new API key.")

@bot.message_handler(commands=['generate'])
def generate_api_key(message):
    if str(message.chat.id) != OWNER_CHAT_ID:
        bot.reply_to(message, "You are not authorized to generate API keys.")
        return

    new_api_key = f"HRK-{secrets.token_hex(4).upper()}-{secrets.token_hex(4).upper()}-{secrets.token_hex(4).upper()}"
    with open(API_KEY_FILE, 'a') as f:
        f.write(new_api_key + '\n')

    bot.reply_to(message, f'New API key generated: {new_api_key}')

def start_flask():
    app.run()

def start_telegram_bot():
    bot.polling()

if __name__ == "__main__":
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.start()

    # Start Telegram bot
    start_telegram_bot()
