from flask import Flask, request, jsonify
import requests
import json

app = Flask(__name__)

API_KEY = "your_custom_api_key"

# Define model name mappings
MODEL_NAME_MAP = {
    "llama": "meta-llama/Llama-3-70b-chat-hf",
    "gpt-3.5": "gpt-3.5-turbo-0125",
    "mixtral": "mistralai/Mixtral-8x7B-Instruct-v0.1"
}

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

def chat_with_model(model, content):
    vqd_value = extract_vqd()
    chat_url = "https://duckduckgo.com/duckchat/v1/chat"

    payload = json.dumps({
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": content
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

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json

    api_key = data.get('api_key')
    if api_key != API_KEY:
        return jsonify({"error": "Invalid API key"}), 403

    short_model_name = data.get('model')
    content = data.get('prompt')

    if not short_model_name or not content:
        return jsonify({"error": "Model and prompt are required"}), 400

    # Map short model name to full model name
    model = MODEL_NAME_MAP.get(short_model_name)
    if not model:
        return jsonify({"error": "Invalid model name"}), 400

    try:
        lines = chat_with_model(model, content)
        complete_message = parse_response(lines)
        return jsonify({"response": complete_message})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
