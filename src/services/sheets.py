import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID")


def _get_service():
    creds = service_account.Credentials.from_service_account_file(
        os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"), scopes=SCOPES
    )
    return build("sheets", "v4", credentials=creds)


def read_range(sheet_range: str) -> list:
    service = _get_service()
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=SPREADSHEET_ID, range=sheet_range)
        .execute()
    )
    return result.get("values", [])


def append_row(sheet_range: str, values: list) -> None:
    service = _get_service()
    body = {"values": [values]}
    service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=sheet_range,
        valueInputOption="USER_ENTERED",
        body=body,
    ).execute()


def clear_range(sheet_range: str) -> None:
    service = _get_service()
    service.spreadsheets().values().clear(
        spreadsheetId=SPREADSHEET_ID, range=sheet_range
    ).execute()


def write_cell(cell: str, value: str) -> None:
    service = _get_service()
    body = {"values": [[value]]}
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=cell,
        valueInputOption="USER_ENTERED",
        body=body,
    ).execute()
