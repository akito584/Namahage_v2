from flask import Flask
from dotenv import load_dotenv

load_dotenv()

import os
if os.environ.get("GCP_PROJECT_ID"):
    from utils.secrets import load_secrets
    load_secrets()

app = Flask(__name__)

from handlers.schedule import schedule_bp
from handlers.slack_event import slack_event_bp
from handlers.absence import absence_bp

app.register_blueprint(schedule_bp)
app.register_blueprint(slack_event_bp)
app.register_blueprint(absence_bp)


@app.route("/health")
def health():
    return "ok", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
