from datetime import datetime

from flask import Blueprint

from services.slack import open_modal
from services.sheets import append_row

absence_bp = Blueprint("absence", __name__)

ABSENCE_MODAL = {
    "type": "modal",
    "callback_id": "absence_modal",
    "title": {"type": "plain_text", "text": "欠席・遅刻届"},
    "submit": {"type": "plain_text", "text": "送信"},
    "close": {"type": "plain_text", "text": "キャンセル"},
    "blocks": [
        {
            "type": "input",
            "block_id": "date_block",
            "label": {"type": "plain_text", "text": "対象日付"},
            "element": {
                "type": "datepicker",
                "action_id": "date_input",
                "placeholder": {"type": "plain_text", "text": "日付を選択"},
            },
        },
        {
            "type": "input",
            "block_id": "type_block",
            "label": {"type": "plain_text", "text": "種別"},
            "element": {
                "type": "radio_buttons",
                "action_id": "type_input",
                "options": [
                    {"text": {"type": "plain_text", "text": "欠席"}, "value": "欠席"},
                    {"text": {"type": "plain_text", "text": "遅刻"}, "value": "遅刻"},
                ],
            },
        },
        {
            "type": "input",
            "block_id": "arrival_block",
            "label": {"type": "plain_text", "text": "到着予定時刻（遅刻の場合）"},
            "optional": True,
            "element": {
                "type": "timepicker",
                "action_id": "arrival_input",
                "placeholder": {"type": "plain_text", "text": "時刻を選択"},
            },
        },
        {
            "type": "input",
            "block_id": "reason_block",
            "label": {"type": "plain_text", "text": "理由"},
            "element": {
                "type": "plain_text_input",
                "action_id": "reason_input",
                "multiline": True,
                "placeholder": {"type": "plain_text", "text": "理由を入力してください"},
            },
        },
    ],
}


def open_absence_modal(trigger_id: str) -> None:
    open_modal(trigger_id, ABSENCE_MODAL)


def handle_absence_submission(payload: dict) -> None:
    values = payload["view"]["state"]["values"]
    slack_id = payload["user"]["id"]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    date = values["date_block"]["date_input"]["selected_date"]
    absence_type = values["type_block"]["type_input"]["selected_option"]["value"]
    arrival = values["arrival_block"]["arrival_input"].get("selected_time", "")
    reason = values["reason_block"]["reason_input"]["value"]

    append_row("欠席届!A:F", [now, slack_id, date, absence_type, arrival, reason])

    if datetime.strptime(date, "%Y-%m-%d").date() == datetime.now().date():
        append_row("キャッシュ!A:A", [slack_id])
