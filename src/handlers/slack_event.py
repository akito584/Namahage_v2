import json

from flask import Blueprint, request, jsonify

from utils.slack_verify import verify_slack_signature
from handlers.absence import open_absence_modal, handle_absence_submission

slack_event_bp = Blueprint("slack_event", __name__)


@slack_event_bp.route("/slack/interactivity", methods=["POST"])
def interactivity():
    if not verify_slack_signature(request):
        return jsonify({"error": "invalid signature"}), 403

    payload = json.loads(request.form.get("payload", "{}"))
    payload_type = payload.get("type")

    if payload_type == "block_actions":
        action_id = payload["actions"][0]["action_id"]
        if action_id == "open_absence_modal":
            open_absence_modal(payload["trigger_id"])
            return "", 200

    if payload_type == "view_submission":
        callback_id = payload["view"]["callback_id"]
        if callback_id == "absence_modal":
            handle_absence_submission(payload)
            return "", 200

    return "", 200
