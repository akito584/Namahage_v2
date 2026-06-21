from datetime import datetime, timedelta
from flask import Blueprint, jsonify
from services.sheets import read_range, append_row, clear_range
from services.slack import post_message, post_thread_message, update_message, get_thread_replies
from utils.time_utils import parse_activity_time, absence_notify_time
import os
import logging
import traceback

logging.basicConfig(level=logging.INFO)

schedule_bp = Blueprint("schedule", __name__)

OPEN_CHANNEL = os.environ.get("SLACK_OPEN_CHANNEL")
CLOSED_CHANNEL = os.environ.get("SLACK_CLOSED_CHANNEL")
REFLECTION_CHANNEL = os.environ.get("SLACK_REFLECTION_CHANNEL")


def _get_today_schedule():
    """活動カレンダーから当日の①行を返す。講義なしの場合はNone。"""
    rows = read_range("活動カレンダー!A:K")
    today = datetime.now().strftime("%Y-%m-%d")
    for row in rows[1:]:
        if len(row) < 11:
            continue
        date_val = str(row[1])[:10]
        slot = row[3] if len(row) > 3 else ""
        activity_time = row[10] if len(row) > 10 else ""
        if date_val == today and slot == "①" and activity_time:
            return row
    return None


def _get_absent_names():
    """キャッシュシートA列のSlackIDを部員マスタで名前に変換して返す。"""
    cache = read_range("キャッシュ!A:A")
    members = read_range("部員マスタ!A:B")
    id_to_name = {r[1]: r[0] for r in members[1:] if len(r) >= 2}
    names = []
    for row in cache[1:]:
        if row and row[0]:
            names.append(id_to_name.get(row[0], row[0]))
    return names


def _get_absent_details():
    """欠席届シートから当日分の詳細を返す。"""
    rows = read_range("欠席届!A:F")
    today = datetime.now().strftime("%Y-%m-%d")
    details = []
    for row in rows[1:]:
        if len(row) >= 4 and str(row[2]) == today:
            details.append(row)
    return details


@schedule_bp.route("/check-schedule", methods=["POST"])
def check_schedule():
    row = _get_today_schedule()
    if not row:
        return jsonify({"status": "no_lecture"}), 200

    activity_time = row[10]
    template_type = row[7] if len(row) > 7 else ""
    start, end = parse_activity_time(activity_time)
    notify_time = absence_notify_time(start)

    from services.tasks import schedule_task
    now = datetime.now()

    try:
        if notify_time > now:
            schedule_task("/notify-absence", notify_time)
            logging.info(f"Scheduled /notify-absence at {notify_time}")

        poll_start = notify_time if notify_time > now else now
        poll_time = poll_start + timedelta(minutes=30)
        while poll_time < start:
            schedule_task("/poll-absence", poll_time)
            logging.info(f"Scheduled /poll-absence at {poll_time}")
            poll_time += timedelta(minutes=30)

        schedule_task("/post-reflection", end, payload={"template_type": template_type})
        logging.info(f"Scheduled /post-reflection at {end}")

        remind_time = end.replace(hour=0, minute=0, second=0) + timedelta(days=1)
        schedule_task("/remind-reflection", remind_time)
        logging.info(f"Scheduled /remind-reflection at {remind_time}")

        reset_time = (end + timedelta(days=1)).replace(hour=12, minute=0, second=0)
        schedule_task("/reset-cache", reset_time)
        logging.info(f"Scheduled /reset-cache at {reset_time}")

    except Exception as e:
        logging.error(f"Failed to schedule tasks: {e}\n{traceback.format_exc()}")
        return jsonify({"status": "error", "message": str(e)}), 500

    return jsonify({"status": "scheduled"}), 200


@schedule_bp.route("/notify-absence", methods=["POST"])
def notify_absence():
    names = _get_absent_names()
    details = _get_absent_details()

    if names:
        open_text = "本日の欠席・遅刻者をお知らせします。\n" + "\n".join(f"・{n}" for n in names)
    else:
        open_text = "本日の欠席・遅刻の届け出はありません。"

    open_blocks = [
        {"type": "section", "text": {"type": "mrkdwn", "text": open_text}},
        {
            "type": "actions",
            "elements": [{
                "type": "button",
                "text": {"type": "plain_text", "text": "欠席・遅刻を届け出る"},
                "action_id": "open_absence_modal",
                "style": "primary",
            }],
        },
    ]

    open_res = post_message(OPEN_CHANNEL, open_text, blocks=open_blocks)
    open_ts = open_res["ts"]

    closed_lines = []
    for d in details:
        slack_id, date, kind, arrival, reason = d[1], d[2], d[3], d[4] if len(d) > 4 else "", d[5] if len(d) > 5 else ""
        line = f"<@{slack_id}> / {kind}"
        if arrival:
            line += f" / {arrival}到着予定"
        if reason:
            line += f" / {reason}"
        closed_lines.append(line)

    if closed_lines:
        closed_text = "本日の欠席・遅刻詳細\n" + "\n".join(f"・{l}" for l in closed_lines)
    else:
        closed_text = "本日の欠席・遅刻の届け出はありません。"

    closed_blocks = [
        {"type": "section", "text": {"type": "mrkdwn", "text": closed_text}},
        {
            "type": "actions",
            "elements": [{
                "type": "button",
                "text": {"type": "plain_text", "text": "欠席・遅刻を届け出る"},
                "action_id": "open_absence_modal",
                "style": "primary",
            }],
        },
    ]

    closed_res = post_message(CLOSED_CHANNEL, closed_text, blocks=closed_blocks)
    closed_ts = closed_res["ts"]

    today_label = datetime.now().strftime("%-m月%-d日")
    append_row("ボット本体!A:C", [today_label, "", closed_ts])

    return jsonify({"status": "ok", "open_ts": open_ts, "closed_ts": closed_ts}), 200


@schedule_bp.route("/poll-absence", methods=["POST"])
def poll_absence():
    rows = read_range("欠席届!A:F")
    cache_rows = read_range("キャッシュ!A:A")
    cached_ids = {r[0] for r in cache_rows[1:] if r}
    today = datetime.now().strftime("%Y-%m-%d")

    new_entries = [r for r in rows[1:] if len(r) >= 4 and str(r[2]) == today and r[1] not in cached_ids]
    if not new_entries:
        return jsonify({"status": "no_new"}), 200

    members = read_range("部員マスタ!A:B")
    id_to_name = {r[1]: r[0] for r in members[1:] if len(r) >= 2}

    bot_rows = read_range("ボット本体!A:C")
    closed_ts = bot_rows[-1][2] if bot_rows and len(bot_rows[-1]) >= 3 else None

    for entry in new_entries:
        slack_id = entry[1]
        append_row("キャッシュ!A:A", [slack_id])

        if closed_ts:
            kind = entry[3]
            arrival = entry[4] if len(entry) > 4 else ""
            reason = entry[5] if len(entry) > 5 else ""
            name = id_to_name.get(slack_id, slack_id)
            thread_text = f"追加届け出: {name} / {kind}"
            if arrival:
                thread_text += f" / {arrival}到着予定"
            if reason:
                thread_text += f" / {reason}"
            post_thread_message(CLOSED_CHANNEL, closed_ts, thread_text)

    all_names = [id_to_name.get(r[0], r[0]) for r in read_range("キャッシュ!A:A")[1:] if r]
    open_text = "本日の欠席・遅刻者をお知らせします。\n" + "\n".join(f"・{n}" for n in all_names) if all_names else "本日の欠席・遅刻の届け出はありません。"

    return jsonify({"status": "ok"}), 200


@schedule_bp.route("/post-reflection", methods=["POST"])
def post_reflection():
    from flask import request as freq
    data = freq.get_json(silent=True) or {}
    template_type = data.get("template_type", "")

    templates = read_range("テンプレート!A:B")
    template_map = {r[0]: r[1] for r in templates[1:] if len(r) >= 2}
    body = template_map.get(template_type) or template_map.get("デフォルト", "【学んだこと】\n【今後、どのように活かしていくか】\n【自由記述】")
    body = body.replace("\\n", "\n")

    text = f"本日の振り返りを投稿してください。\n\n{body}"
    res = post_message(REFLECTION_CHANNEL, text)
    ts = res["ts"]

    bot_rows = read_range("ボット本体!A:C")
    if bot_rows and len(bot_rows) >= 2:
        last_row_idx = len(bot_rows)
        from services.sheets import write_cell
        write_cell(f"ボット本体!B{last_row_idx}", ts)

    return jsonify({"status": "ok", "ts": ts}), 200


@schedule_bp.route("/remind-reflection", methods=["POST"])
def remind_reflection():
    members = read_range("部員マスタ!A:D")
    absent = {r[0] for r in read_range("キャッシュ!A:A")[1:] if r}
    done = {r[0] for r in read_range("キャッシュ!B:B")[1:] if r}

    targets = []
    for row in members[1:]:
        if len(row) < 2:
            continue
        excluded = row[3].upper() == "TRUE" if len(row) >= 4 and row[3] else False
        if not excluded and row[1] not in absent and row[1] not in done:
            targets.append(row[1])

    if not targets:
        return jsonify({"status": "no_targets"}), 200

    mention_text = " ".join(f"<@{sid}>" for sid in targets)
    text = f"{mention_text}\n本日の振り返りがまだ投稿されていません。スレッドへの投稿をお願いします。"

    bot_rows = read_range("ボット本体!A:C")
    reflection_ts = bot_rows[-1][1] if bot_rows and len(bot_rows[-1]) >= 2 else None

    if reflection_ts:
        post_thread_message(REFLECTION_CHANNEL, reflection_ts, text)
    else:
        post_message(REFLECTION_CHANNEL, text)

    return jsonify({"status": "ok", "targets": targets}), 200


@schedule_bp.route("/reset-cache", methods=["POST"])
def reset_cache():
    clear_range("キャッシュ!A:B")
    append_row("キャッシュ!A:A", ["欠席/遅刻者SlackID"])
    return jsonify({"status": "ok"}), 200
