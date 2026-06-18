from flask import Blueprint, request, jsonify

slack_event_bp = Blueprint("slack_event", __name__)


@slack_event_bp.route("/slack/interactivity", methods=["POST"])
def interactivity():
    # TODO: ボタンクリック・モーダル送信のペイロードを振り分け
    return jsonify({"status": "ok"}), 200
