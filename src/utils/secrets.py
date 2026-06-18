import os
import json
import tempfile
from google.cloud import secretmanager


def _get_secret(secret_id: str, project_id: str) -> str:
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("utf-8")


def load_secrets():
    project_id = os.environ.get("GCP_PROJECT_ID")
    if not project_id:
        return

    os.environ["SLACK_BOT_TOKEN"] = _get_secret("SLACK_BOT_TOKEN", project_id)
    os.environ["SLACK_SIGNING_SECRET"] = _get_secret("SLACK_SIGNING_SECRET", project_id)
    os.environ["SPREADSHEET_ID"] = _get_secret("SPREADSHEET_ID", project_id)

    sa_json = _get_secret("GOOGLE_SA_JSON", project_id)
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    tmp.write(sa_json)
    tmp.close()
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = tmp.name
