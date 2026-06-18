from datetime import datetime, timedelta
import re


def parse_activity_time(time_str: str) -> tuple[datetime, datetime]:
    """'17:30-21:00' 形式の文字列をdatetimeのタプルに変換して返す"""
    match = re.match(r"(\d{2}):(\d{2})-(\d{2}):(\d{2})", time_str)
    if not match:
        raise ValueError(f"Invalid time format: {time_str}")
    now = datetime.now()
    start = now.replace(hour=int(match[1]), minute=int(match[2]), second=0, microsecond=0)
    end = now.replace(hour=int(match[3]), minute=int(match[4]), second=0, microsecond=0)
    return start, end


def absence_notify_time(lecture_start: datetime) -> datetime:
    """講義開始の5時間前を返す"""
    return lecture_start - timedelta(hours=5)
