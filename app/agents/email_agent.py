import json

from langchain_groq import ChatGroq

from app.config.settings import GROQ_API_KEY, MODEL_NAME
from app.mcp.email_client import call_email_tool_sync


llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=MODEL_NAME,
    temperature=0,
)


def ask_email_agent(question: str) -> str:
    """
    Email Agent using a real MCP client.

    Supports:
    - Writing emails
    - Creating Gmail drafts
    - Sending emails
    """

    try:
        action = detect_email_action(question)

        if action == "DRAFT":
            return create_draft_from_question(question)

        if action == "SEND":
            return send_email_from_question(question)

        if action == "WRITE":
            return write_email_from_question(question)

        return (
            "I can help you with email.\n\n"
            "Examples:\n"
            "• Write an email to someone\n"
            "• Draft an email to someone\n"
            "• Send an email to someone"
        )

    except Exception as error:
        return (
            "Email Agent Error:\n"
            f"{error}"
        )


def detect_email_action(question: str) -> str:
    """
    Detect the requested email operation.
    """

    question_lower = question.lower()

    if any(
        phrase in question_lower
        for phrase in [
            "draft",
            "save as draft",
            "create draft",
        ]
    ):
        return "DRAFT"

    if any(
        phrase in question_lower
        for phrase in [
            "send",
            "send email",
            "send an email",
            "send mail",
            "send a mail",
        ]
    ):
        return "SEND"

    if any(
        phrase in question_lower
        for phrase in [
            "write",
            "compose",
            "create email",
            "create an email",
        ]
    ):
        return "WRITE"

    return "UNKNOWN"


def write_email_from_question(
    question: str,
) -> str:
    """
    Generate an email without sending it.
    """

    extraction = extract_email_details(
        question
    )

    if not extraction:
        return (
            "I could not understand the email "
            "details.\n\n"
            "Example:\n"
            "Write an email to ali@example.com "
            "about my assignment."
        )

    return (
        "Email written successfully.\n\n"
        f"To: {extraction['to']}\n"
        f"Subject: {extraction['subject']}\n\n"
        f"{extraction['body']}"
    )


def create_draft_from_question(
    question: str,
) -> str:
    """
    Create a Gmail draft through MCP.
    """

    email = extract_email_details(
        question
    )

    if not email:
        return (
            "I could not understand the email "
            "details.\n\n"
            "Example:\n"
            "Draft an email to "
            "ali@example.com about my assignment."
        )

    result = call_email_tool_sync(
        "create_email_draft",
        {
            "to": email["to"],
            "subject": email["subject"],
            "body": email["body"],
        },
    )

    data = extract_mcp_json(result)

    return (
        "Email draft created successfully.\n\n"
        f"To: {email['to']}\n"
        f"Subject: {email['subject']}\n"
        f"Draft ID: "
        f"{data.get('draft_id', 'Not available')}"
    )


def send_email_from_question(
    question: str,
) -> str:
    """
    Send an email through Gmail MCP.
    """

    email = extract_email_details(
        question
    )

    if not email:
        return (
            "I could not understand the email "
            "details.\n\n"
            "Example:\n"
            "Send an email to "
            "ali@example.com about my assignment."
        )

    result = call_email_tool_sync(
        "send_email",
        {
            "to": email["to"],
            "subject": email["subject"],
            "body": email["body"],
        },
    )

    data = extract_mcp_json(result)

    return (
        "Email sent successfully.\n\n"
        f"To: {email['to']}\n"
        f"Subject: {email['subject']}\n"
        f"Message ID: "
        f"{data.get('message_id', 'Not available')}"
    )


def extract_email_details(
    question: str,
) -> dict | None:
    """
    Use the LLM to extract recipient, subject,
    and email body.
    """

    prompt = f"""
You are an email information extraction assistant.

User request:
{question}

Extract:

TO
SUBJECT
BODY

Return ONLY these three lines:

TO: recipient email address
SUBJECT: email subject
BODY: email body

Rules:

1. Extract the email address exactly if provided.

2. If the user provides a person name but no email
   address, do not invent an email address.

3. If no subject is provided, create a short
   professional subject.

4. Write a professional and natural email body.

5. Do not add explanations.

6. Return exactly:
TO:
SUBJECT:
BODY:
"""

    response = llm.invoke(prompt)

    return parse_email_details(
        response.content
    )


def parse_email_details(
    text: str,
) -> dict | None:
    """
    Parse the LLM email extraction response.
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

    if not all(
        key in values
        for key in [
            "TO",
            "SUBJECT",
            "BODY",
        ]
    ):
        return None

    if not values["TO"]:
        return None

    return {
        "to": values["TO"],
        "subject": values["SUBJECT"],
        "body": values["BODY"],
    }


def extract_mcp_json(result):
    """
    Extract JSON from an MCP response.
    """

    if getattr(result, "isError", False):

        raise RuntimeError(
            "Gmail MCP tool returned an error."
        )

    if not result.content:

        raise RuntimeError(
            "Gmail MCP tool returned no content."
        )

    # Prefer structured content if available.
    structured = getattr(
        result,
        "structuredContent",
        None,
    )

    if structured:

        data = structured.get("result")

        if data is not None:
            return data

    # Fallback to text content.
    for content in result.content:

        if hasattr(content, "text"):

            text = content.text

            if text:

                return json.loads(text)

    raise RuntimeError(
        "Gmail MCP tool returned no readable data."
    )
