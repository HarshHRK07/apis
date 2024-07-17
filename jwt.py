from flask import Flask, request, jsonify
import jwt

app = Flask(__name__)

@app.route('/decoder', methods=['GET'])
def decode_token():
    token = request.args.get('token')
    if not token:
        return jsonify({"error": "Token is required"}), 400

    try:
        # Decode the JWT token without verification
        decoded_header = jwt.get_unverified_header(token)
        decoded_payload = jwt.decode(token, options={"verify_signature": False})

        # Return the decoded header and payload
        return jsonify({"header": decoded_header, "payload": decoded_payload}), 200
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token has expired"}), 400
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
    
