import json
import os
from datetime import datetime
from google.cloud import tasks_v2
from google.protobuf import timestamp_pb2

PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
LOCATION = "asia-northeast1"
QUEUE = "namahage-queue"
SERVICE_URL = os.environ.get("CLOUD_RUN_URL")


def schedule_task(path: str, run_at: datetime, payload: dict = None) -> None:
    client = tasks_v2.CloudTasksClient()
    parent = client.queue_path(PROJECT_ID, LOCATION, QUEUE)

    body = json.dumps(payload or {}).encode()
    ts = timestamp_pb2.Timestamp()
    ts.FromDatetime(run_at)

    task = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": f"{SERVICE_URL}{path}",
            "headers": {"Content-Type": "application/json"},
            "body": body,
        },
        "schedule_time": ts,
    }

    client.create_task(request={"parent": parent, "task": task})
