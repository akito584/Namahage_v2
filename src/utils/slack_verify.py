import hashlib
import hmac
import os
import time

from flask import Request


def verify_slack_signature(request: Request) -> bool:
    signing_secret = os.environ.get("SLACK_SIGNING_SECRET", "")
    timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
    signature = request.headers.get("X-Slack-Signature", "")

    if abs(time.time() - int(timestamp)) > 300:
        return False

    sig_basestring = f"v0:{timestamp}:{request.get_data(as_text=True)}"
    mac = hmac.new(signing_secret.encode(), sig_basestring.encode(), hashlib.sha256)
    expected = "v0=" + mac.hexdigest()

    return hmac.compare_digest(expected, signature)
