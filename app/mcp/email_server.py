import base64
from email.message import EmailMessage
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from mcp.server.fastmcp import FastMCP


# ==========================================
# GMAIL PERMISSIONS
# ==========================================

SCOPES = [
    "https://www.googleapis.com/auth/gmail.compose",
]


# ==========================================
# PROJECT FILES
# ==========================================

BASE_DIR = Path(__file__).resolve().parents[2]

CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "gmail_token.json"


# ==========================================
# MCP SERVER
# ==========================================

mcp = FastMCP("Gmail MCP Server")


# ==========================================
# GMAIL SERVICE
# ==========================================

def get_gmail_service():
    """
    Authenticate with Gmail and return
    the Gmail API service.
    """

    credentials = None

    # --------------------------------------
    # Load existing Gmail token
    # --------------------------------------

    if TOKEN_FILE.exists():

        credentials = (
            Credentials.from_authorized_user_file(
                str(TOKEN_FILE),
                SCOPES,
            )
        )

    # --------------------------------------
    # Refresh or create authentication
    # --------------------------------------

    if not credentials or not credentials.valid:

        if (
            credentials
            and credentials.expired
            and credentials.refresh_token
        ):

            credentials.refresh(
                Request()
            )

        else:

            if not CREDENTIALS_FILE.exists():

                raise FileNotFoundError(
                    f"credentials.json not found at: "
                    f"{CREDENTIALS_FILE}"
                )

            flow = (
                InstalledAppFlow
                .from_client_secrets_file(
                    str(CREDENTIALS_FILE),
                    SCOPES,
                )
            )

            credentials = flow.run_local_server(
                port=0
            )

        # ----------------------------------
        # Save Gmail token
        # ----------------------------------

        TOKEN_FILE.write_text(
            credentials.to_json(),
            encoding="utf-8",
        )

    # --------------------------------------
    # Create Gmail service
    # --------------------------------------

    return build(
        "gmail",
        "v1",
        credentials=credentials,
    )


# ==========================================
# GET GMAIL ACCOUNT
# ==========================================

@mcp.tool()
def get_gmail_account() -> dict:
    """
    Get the authenticated Gmail account.
    """

    service = get_gmail_service()

    profile = (
        service.users()
        .getProfile(
            userId="me"
        )
        .execute()
    )

    return {
        "email": profile.get(
            "emailAddress"
        ),
        "messages_total": profile.get(
            "messagesTotal"
        ),
        "threads_total": profile.get(
            "threadsTotal"
        ),
    }


# ==========================================
# CREATE GMAIL DRAFT
# ==========================================

@mcp.tool()
def create_email_draft(
    to: str,
    subject: str,
    body: str,
) -> dict:
    """
    Create a Gmail draft.
    """

    service = get_gmail_service()

    message = EmailMessage()

    message["To"] = to
    message["Subject"] = subject

    message.set_content(body)

    encoded_message = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    draft_body = {
        "message": {
            "raw": encoded_message
        }
    }

    draft = (
        service.users()
        .drafts()
        .create(
            userId="me",
            body=draft_body,
        )
        .execute()
    )

    return {
        "draft_id": draft.get("id"),
        "message": "Email draft created successfully.",
    }


# ==========================================
# SEND EMAIL
# ==========================================

@mcp.tool()
def send_email(
    to: str,
    subject: str,
    body: str,
) -> dict:
    """
    Send an email through Gmail.
    """

    service = get_gmail_service()

    message = EmailMessage()

    message["To"] = to
    message["Subject"] = subject

    message.set_content(body)

    encoded_message = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    send_body = {
        "raw": encoded_message
    }

    sent_message = (
        service.users()
        .messages()
        .send(
            userId="me",
            body=send_body,
        )
        .execute()
    )

    return {
        "message_id": sent_message.get(
            "id"
        ),
        "thread_id": sent_message.get(
            "threadId"
        ),
        "message": "Email sent successfully.",
    }


# ==========================================
# MCP SERVER
# ==========================================

if __name__ == "__main__":
    mcp.run()