import os
import uuid
import random
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

BROWSER_PROFILES = [
    {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-platform": '"Windows"',
        "sec-ch-ua-mobile": "?0"
    },
    {
        "user-agent": "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.81 Mobile Safari/537.36",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-platform": '"Android"',
        "sec-ch-ua-mobile": "?1"
    },
    {
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-platform": '"Linux"',
        "sec-ch-ua-mobile": "?0"
    }
]

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "active",
        "usage": "/api/lookup?number=919998887779"
    }), 200

@app.route('/api/lookup', methods=['GET'])
def lookup_number():
    number = request.args.get('number')
    
    if not number:
        return jsonify({"error": "Number is required. Example: ?number=919998887779"}), 400

    req_id = str(uuid.uuid4())
    session = requests.Session()
    profile = random.choice(BROWSER_PROFILES)
    
    base_headers = {
        "user-agent": profile["user-agent"],
        "sec-ch-ua": profile["sec-ch-ua"],
        "sec-ch-ua-platform": profile["sec-ch-ua-platform"],
        "sec-ch-ua-mobile": profile["sec-ch-ua-mobile"],
        "accept": "*/*",
        "sec-fetch-site": "same-origin",
        "sec-fetch-mode": "cors",
        "sec-fetch-dest": "empty",
        "referer": "https://lookupnow.top/",
        "accept-encoding": "gzip, deflate",
        "accept-language": "en-US,en;q=0.9"
    }

    try:
        # 1. Generate Token API
        token_headers = base_headers.copy()
        token_headers.update({
            "x-ln-purpose": "lookup",
            "x-ln-rid": req_id,
            "content-type": "application/json",
            "origin": "https://lookupnow.top"
        })
        
        token_payload = {
            "requestId": req_id,
            "number": number,
            "purpose": "lookup"
        }
        
        token_res = session.post(
            "https://lookupnow.top/api/generate-token",
            headers=token_headers,
            json=token_payload,
            timeout=10
        )

        # Agar JSON body mein token ho toh cookie set karein
        try:
            token_data = token_res.json()
            if isinstance(token_data, dict):
                token_val = token_data.get("token") or token_data.get("ln_ot")
                if token_val and "ln_ot" not in session.cookies:
                    session.cookies.set("ln_ot", token_val, domain="lookupnow.top")
        except Exception:
            pass

        # 2. Lookup API
        lookup_headers = base_headers.copy()
        lookup_headers.update({
            "x-ln-purpose": "lookup",
            "x-ln-rid": req_id
        })
        
        lookup_params = {
            "number": number,
            "ref": "lookupnow-web",
            "referer": "android-app://com.google.android.googlequicksearchbox/"
        }
        
        response = session.get(
            "https://lookupnow.top/api/lookup",
            headers=lookup_headers,
            params=lookup_params,
            timeout=10
        )
        
        try:
            return jsonify(response.json()), response.status_code
        except Exception:
            return jsonify({
                "status_code": response.status_code,
                "raw_response": response.text
            }), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
