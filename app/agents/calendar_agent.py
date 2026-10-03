from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import json

from langchain_groq import ChatGroq

from app.config.settings import GROQ_API_KEY, MODEL_NAME
from app.mcp.calendar_client import call_calendar_tool_sync


llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=MODEL_NAME,
    temperature=0,
)

TIMEZONE = ZoneInfo("Asia/Karachi")


def ask_calendar_agent(question: str) -> str:
    """
    Google Calendar Agent using a real MCP client.

    Supported tasks:
    - Show upcoming meetings
    - Create meetings
    - Schedule meetings for specific dates/times
    """

    try:
        action = detect_calendar_action(question)

        if action == "CREATE":
            return create_meeting_from_question(question)

        if action == "LIST":
            return show_upcoming_meetings()

        return (
            "I can help you with Google Calendar.\n\n"
            "Examples:\n"
            "• Show my upcoming meetings\n"
            "• Create a meeting today from 5 PM to 6 PM\n"
            "• Create an AI meeting tomorrow at 4 PM\n"
            "• Schedule a meeting tomorrow at 5 PM for 30 minutes"
        )

    except Exception as error:
        return (
            "Calendar Agent Error:\n"
            f"{error}"
        )


def detect_calendar_action(question: str) -> str:
    """
    Detect whether the user wants to list or create calendar events.
    """

    prompt = f"""
You are a Google Calendar intent classifier.

User request:
{question}

Classify the request into exactly ONE of these:

CREATE
LIST
UNKNOWN

CREATE means the user wants to:
- create a meeting
- schedule a meeting
- fix/set/book a meeting
- add a meeting
- arrange a meeting
- put a meeting on the calendar
- create an event
- schedule an event

Examples:
"fix my meeting today from 5 to 6 pm" = CREATE
"set my meeting tomorrow at 4 pm" = CREATE
"book a meeting today at 5 pm" = CREATE
"create an AI meeting for tomorrow" = CREATE

LIST means the user wants to:
- see upcoming meetings
- show calendar events
- list meetings
- check their calendar
- see their calendar

Examples:
"show my upcoming meetings" = LIST
"what meetings do I have?" = LIST
"show my calendar" = LIST

Return ONLY:
CREATE
or
LIST
or
UNKNOWN
"""

    response = llm.invoke(prompt)

    result = response.content.strip().upper()

    if "CREATE" in result:
        return "CREATE"

    if "LIST" in result:
        return "LIST"

    return "UNKNOWN"


def show_upcoming_meetings() -> str:
    """
    Get upcoming meetings through the Calendar MCP server.
    """

    result = call_calendar_tool_sync(
        "list_upcoming_events",
        {
            "max_results": 10,
        },
    )

    events = extract_mcp_json(result)

    if not events:
        return (
            "You don't have any upcoming "
            "calendar events."
        )

    output = [
        "Your upcoming calendar events:"
    ]

    for event in events:

        start_display = format_pakistan_datetime(
            event["start"]
        )

        end_display = format_pakistan_datetime(
            event["end"]
        )

        if start_display["date"] == end_display["date"]:

            time_text = (
                f"{start_display['time']} - "
                f"{end_display['time']}"
            )

        else:

            time_text = (
                f"{start_display['date']} "
                f"{start_display['time']} - "
                f"{end_display['date']} "
                f"{end_display['time']}"
            )

        output.append(
            f"\n• {event.get('summary', 'Untitled Event')}"
            f"\n  Date: {start_display['date']}"
            f"\n  Time: {time_text} "
            f"(Pakistan Time)"
            f"\n  Location: "
            f"{event.get('location') or 'Not specified'}"
        )

    return "\n".join(output)


def create_meeting_from_question(
    question: str,
) -> str:
    """
    Extract meeting information using the LLM,
    then create the event through the Calendar MCP server.
    """

    now = datetime.now(TIMEZONE)

    extraction_prompt = f"""
You are a Google Calendar information extraction assistant.

Current date and time in Pakistan:
{now.strftime("%Y-%m-%d %I:%M %p")}

Current date:
{now.strftime("%Y-%m-%d")}

User request:
{question}

Extract the meeting information.

Return ONLY these four lines:

TITLE: meeting title
START: YYYY-MM-DD HH:MM
END: YYYY-MM-DD HH:MM
DESCRIPTION: description

Rules:

1. Use Pakistan timezone: Asia/Karachi.

2. "today" means:
{now.strftime("%Y-%m-%d")}

3. "tomorrow" means the next calendar date.

4. If the user gives a start and end time,
   use those exact times.

5. Example:
   "today from 5 to 6 pm"
   means:

   START: {now.strftime("%Y-%m-%d")} 17:00
   END: {now.strftime("%Y-%m-%d")} 18:00

6. If the user gives a duration,
   calculate the end time.

7. If only a start time is provided,
   use 1 hour duration.

8. If no title is provided,
   use:

   Meeting

9. Keep the description short.

10. Do not add explanations.

11. Return exactly the four required lines.
"""

    response = llm.invoke(extraction_prompt)

    parsed = parse_meeting_details(
        response.content
    )

    if not parsed:
        return (
            "I could not understand the meeting "
            "details.\n\n"
            "Example:\n"
            "Create a meeting today from 5 PM to 6 PM."
        )

    title = parsed["title"]
    start = parsed["start"]
    end = parsed["end"]
    description = parsed["description"]

    try:

        start_dt = datetime.strptime(
            start,
            "%Y-%m-%d %H:%M",
        ).replace(
            tzinfo=TIMEZONE
        )

        end_dt = datetime.strptime(
            end,
            "%Y-%m-%d %H:%M",
        ).replace(
            tzinfo=TIMEZONE
        )

    except ValueError:

        return (
            "I could not understand the meeting "
            "date or time.\n\n"
            "Example:\n"
            "Create a meeting today from 5 PM to 6 PM."
        )

    # If end time is before/equal to start,
    # use a one-hour duration.
    if end_dt <= start_dt:
        end_dt = start_dt + timedelta(hours=1)

    current_time = datetime.now(TIMEZONE)

    if start_dt < current_time:

        return (
            "The requested meeting time has already "
            "passed.\n\n"
            "Please provide a future time."
        )

    # Create event through MCP client.
    result = call_calendar_tool_sync(
        "create_calendar_event",
        {
            "summary": title,
            "start_time": start_dt.isoformat(),
            "end_time": end_dt.isoformat(),
            "description": description,
        },
    )

    created = extract_mcp_json(result)

    # MCP may return the created event as a list.
    if isinstance(created, list):

        if not created:
            return (
                "Calendar MCP created no event."
            )

        created = created[0]

    created_start = format_pakistan_datetime(
        created["start"]
    )

    created_end = format_pakistan_datetime(
        created["end"]
    )

    return (
        "Meeting created successfully.\n\n"
        f"Title: {created['summary']}\n"
        f"Date: {created_start['date']}\n"
        f"Time: {created_start['time']} - "
        f"{created_end['time']} "
        f"(Pakistan Time)\n"
        f"Calendar: {created['html_link']}"
    )


def extract_mcp_json(result):
    """
    Extract JSON data from an MCP tool response.

    Calendar list_upcoming_events can return
    multiple TextContent JSON objects, while
    structuredContent can contain the complete list.
    """

    if getattr(result, "isError", False):

        raise RuntimeError(
            "Google Calendar MCP tool returned an error."
        )

    # -------------------------------------------------
    # First try structuredContent.
    # -------------------------------------------------

    structured = getattr(
        result,
        "structuredContent",
        None,
    )

    if structured:

        data = structured.get("result")

        if data is not None:
            return data

    # -------------------------------------------------
    # Fallback to text content.
    # -------------------------------------------------

    if not result.content:

        raise RuntimeError(
            "Google Calendar MCP tool returned no content."
        )

    texts = []

    for content in result.content:

        if hasattr(content, "text"):

            text = content.text

            if text:
                texts.append(text)

    if not texts:

        raise RuntimeError(
            "Google Calendar MCP tool returned "
            "no readable content."
        )

    # -------------------------------------------------
    # Multiple JSON objects.
    # -------------------------------------------------

    if len(texts) > 1:

        return [
            json.loads(text)
            for text in texts
        ]

    # -------------------------------------------------
    # Single JSON object.
    # -------------------------------------------------

    return json.loads(texts[0])


def parse_meeting_details(
    text: str,
) -> dict | None:
    """
    Parse the four-line response produced by
    the LLM.
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
            "TITLE",
            "START",
            "END",
            "DESCRIPTION",
        }:

            values[key] = value

    required = [
        "TITLE",
        "START",
        "END",
    ]

    if not all(
        key in values
        for key in required
    ):
        return None

    return {
        "title": values["TITLE"] or "Meeting",
        "start": values["START"],
        "end": values["END"],
        "description": values.get(
            "DESCRIPTION",
            "",
        ),
    }


def format_pakistan_datetime(
    datetime_string: str,
) -> dict:
    """
    Convert an ISO datetime into readable
    Pakistan time.
    """

    dt = datetime.fromisoformat(
        datetime_string
    )

    dt = dt.astimezone(
        TIMEZONE
    )

    return {
        "date": dt.strftime(
            "%B %d, %Y"
        ),
        "time": dt.strftime(
            "%I:%M %p"
        ).lstrip("0"),
    }