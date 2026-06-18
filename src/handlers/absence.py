from flask import Blueprint, jsonify

absence_bp = Blueprint("absence", __name__)


def open_absence_modal(trigger_id: str):
    # TODO: views.open で欠席届モーダルを表示
    pass


def handle_absence_submission(payload: dict):
    # TODO: モーダル送信内容を欠席届シートに書き込み、キャッシュシートA列に追記
    pass
