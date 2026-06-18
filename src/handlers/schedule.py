from flask import Blueprint, jsonify

schedule_bp = Blueprint("schedule", __name__)


@schedule_bp.route("/check-schedule", methods=["POST"])
def check_schedule():
    # TODO: 活動カレンダーを読み取り、講義有無を判定してタスクをスケジュール登録
    return jsonify({"status": "ok"}), 200


@schedule_bp.route("/notify-absence", methods=["POST"])
def notify_absence():
    # TODO: 欠席通知をSlackに投稿
    return jsonify({"status": "ok"}), 200


@schedule_bp.route("/poll-absence", methods=["POST"])
def poll_absence():
    # TODO: 欠席届シートの新着をキャッシュシートに反映
    return jsonify({"status": "ok"}), 200


@schedule_bp.route("/post-reflection", methods=["POST"])
def post_reflection():
    # TODO: 振り返り親メッセージをSlackに投稿
    return jsonify({"status": "ok"}), 200


@schedule_bp.route("/remind-reflection", methods=["POST"])
def remind_reflection():
    # TODO: 振り返り未投稿者に@メンションでリマインド
    return jsonify({"status": "ok"}), 200


@schedule_bp.route("/reset-cache", methods=["POST"])
def reset_cache():
    # TODO: キャッシュシートをクリア
    return jsonify({"status": "ok"}), 200
