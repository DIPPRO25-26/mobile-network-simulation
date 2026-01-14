import hmac
import hashlib
import json
import os
from datetime import datetime

HMAC_SECRET = os.getenv("HMAC_SECRET_KEY", "your_shared_secret_key_here")

def create_hmac_headers(data: dict) -> dict:
    timestamp = datetime.now().isoformat()
    body = json.dumps(data, separators=(',', ':'), sort_keys=True)

    message = f"{timestamp}.{body}"
    signature = hmac.new(
        HMAC_SECRET.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()

    return {
        "X-HMAC-Signature": signature,
        "X-Timestamp": timestamp,
        "Content-Type": "application/json"
    }