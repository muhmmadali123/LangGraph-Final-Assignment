from datetime import datetime, timedelta
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from mcp.server.fastmcp import FastMCP


# Google Calendar permissions
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
]


# Project root
BASE_DIR = Path(__file__).resolve().parents[2]

CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"


# MCP server
mcp = FastMCP("Google Calendar MCP Server")


def get_calendar_service():
    """
    Authenticate with Google Calendar and return the API service.
    """

    credentials = None

    # Load existing token
    if TOKEN_FILE.exists():
        credentials = Credentials.from_authorized_user_file(
            str(TOKEN_FILE),
            SCOPES,
        )

    # Refresh or create authentication
    if not credentials or not credentials.valid:

        if (
            credentials
            and credentials.expired
            and credentials.refresh_token
        ):
            credentials.refresh(Request())

        else:
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    f"credentials.json not found at: "
                    f"{CREDENTIALS_FILE}"
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE),
                SCOPES,
            )

            credentials = flow.run_local_server(
                port=0
            )

        # Save authentication token
        TOKEN_FILE.write_text(
            credentials.to_json(),
            encoding="utf-8",
        )

    return build(
        "calendar",
        "v3",
        credentials=credentials,
    )


@mcp.tool()
def list_upcoming_events(
    max_results: int = 10,
) -> list[dict]:
    """
    List upcoming Google Calendar events.
    """

    service = get_calendar_service()

    now = datetime.now().astimezone().isoformat()

    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )

    events = events_result.get("items", [])

    results = []

    for event in events:

        start = event.get("start", {})

        start_time = (
            start.get("dateTime")
            or start.get("date")
            or "Unknown"
        )

        results.append(
            {
                "id": event.get("id"),
                "summary": event.get(
                    "summary",
                    "No title",
                ),
                "start": start_time,
                "end": event.get(
                    "end",
                    {},
                ).get(
                    "dateTime"
                    )
                    or event.get(
                        "end",
                        {},
                    ).get(
                        "date"
                    ),
                "description": event.get(
                    "description",
                    "",
                ),
                "location": event.get(
                    "location",
                    "",
                ),
            }
        )

    return results


@mcp.tool()
def create_calendar_event(
    summary: str,
    start_time: str,
    end_time: str,
    description: str = "",
) -> dict:
    """
    Create a Google Calendar event.

    Datetime format:
    2026-10-03T15:00:00+05:00
    """

    service = get_calendar_service()

    event = {
        "summary": summary,
        "description": description,
        "start": {
            "dateTime": start_time,
            "timeZone": "Asia/Karachi",
        },
        "end": {
            "dateTime": end_time,
            "timeZone": "Asia/Karachi",
        },
    }

    created_event = (
        service.events()
        .insert(
            calendarId="primary",
            body=event,
        )
        .execute()
    )

    return {
        "id": created_event.get("id"),
        "summary": created_event.get(
            "summary"
        ),
        "start": created_event.get(
            "start",
            {},
        ).get("dateTime"),
        "end": created_event.get(
            "end",
            {},
        ).get("dateTime"),
        "html_link": created_event.get(
            "htmlLink"
        ),
    }


if __name__ == "__main__":
    mcp.run()