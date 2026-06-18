import os
from slack_sdk import WebClient

_client = None


def get_client() -> WebClient:
    global _client
    if _client is None:
        _client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))
    return _client


def post_message(channel: str, text: str, blocks: list = None) -> dict:
    return get_client().chat_postMessage(channel=channel, text=text, blocks=blocks)


def post_thread_message(channel: str, thread_ts: str, text: str) -> dict:
    return get_client().chat_postMessage(
        channel=channel, thread_ts=thread_ts, text=text
    )


def get_thread_replies(channel: str, thread_ts: str) -> list:
    response = get_client().conversations_replies(channel=channel, ts=thread_ts)
    return response.get("messages", [])


def open_modal(trigger_id: str, view: dict) -> dict:
    return get_client().views_open(trigger_id=trigger_id, view=view)
