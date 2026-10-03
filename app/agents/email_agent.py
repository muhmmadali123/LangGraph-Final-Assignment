from langchain_groq import ChatGroq

from app.config.settings import GROQ_API_KEY, MODEL_NAME
from app.mcp.email_server import (
    create_email_draft,
    send_email,
)


# ==========================================
# LLM
# ==========================================

llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=MODEL_NAME,
    temperature=0,
)


# ==========================================
# EMAIL AGENT
# ==========================================

def ask_email_agent(question: str) -> str:
    """
    Email specialist agent.

    Supports:
    - Writing email content
    - Creating Gmail drafts
    - Sending emails
    """

    question_lower = question.lower()

    try:

        # ==========================================
        # SEND EMAIL
        # ==========================================

        if any(
            keyword in question_lower
            for keyword in [
                "send email",
                "send an email",
                "send mail",
                "send a mail",
            ]
        ):

            return handle_email_request(
                question,
                send=True,
            )

        # ==========================================
        # CREATE DRAFT
        # ==========================================

        if any(
            keyword in question_lower
            for keyword in [
                "draft email",
                "draft an email",
                "create email draft",
                "create a draft",
                "write email",
                "write an email",
            ]
        ):

            return handle_email_request(
                question,
                send=False,
            )

        # ==========================================
        # DEFAULT
        # ==========================================

        return (
            "I can help you with Gmail.\n\n"
            "Examples:\n"
            "• Draft an email to test@example.com "
            "about the project update.\n"
            "• Send an email to test@example.com "
            "with subject Project Update."
        )

    except Exception as error:

        return (
            "Email Agent Error:\n"
            f"{error}"
        )


# ==========================================
# HANDLE EMAIL REQUEST
# ==========================================

def handle_email_request(
    question: str,
    send: bool,
) -> str:
    """
    Extract email details using the LLM,
    then create a draft or send the email.
    """

    extraction_prompt = f"""
You are an email information extraction assistant.

User request:
{question}

Extract the email information.

Return ONLY these three lines:

TO: recipient email address
SUBJECT: email subject
BODY: email body

Rules:

1. Extract the recipient email address exactly.
2. Create a professional subject if one is not provided.
3. Write a clear and professional email body.
4. Do not add extra text.
"""

    response = llm.invoke(
        extraction_prompt
    )

    parsed = parse_email_details(
        response.content
    )

    if not parsed:

        return (
            "I could not understand the email "
            "details.\n\n"
            "Please provide:\n"
            "• Recipient email\n"
            "• Subject or purpose\n"
            "• Message"
        )

    to = parsed["to"]
    subject = parsed["subject"]
    body = parsed["body"]

    # ==========================================
    # SEND EMAIL
    # ==========================================

    if send:

        result = send_email(
            to=to,
            subject=subject,
            body=body,
        )

        return (
            "Email sent successfully.\n\n"
            f"To: {to}\n"
            f"Subject: {subject}\n"
            f"Message ID: {result['message_id']}"
        )

    # ==========================================
    # CREATE DRAFT
    # ==========================================

    result = create_email_draft(
        to=to,
        subject=subject,
        body=body,
    )

    return (
        "Email draft created successfully.\n\n"
        f"To: {to}\n"
        f"Subject: {subject}\n"
        f"Draft ID: {result['draft_id']}"
    )


# ==========================================
# PARSE EMAIL DETAILS
# ==========================================

def parse_email_details(
    text: str,
) -> dict | None:
    """
    Parse structured LLM output.
    """

    values = {}

    for line in text.splitlines():

        if ":" not in line:
            continue

        key, value = line.split(
            ":",
            1,
        )

        key = key.strip().upper()
        value = value.strip()

        if key in {
            "TO",
            "SUBJECT",
            "BODY",
        }:

            values[key] = value

    required = [
        "TO",
        "SUBJECT",
        "BODY",
    ]

    if not all(
        key in values
        for key in required
    ):

        return None

    return {
        "to": values["TO"],
        "subject": values["SUBJECT"],
        "body": values["BODY"],
    }
