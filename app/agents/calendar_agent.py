from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from langchain_groq import ChatGroq

from app.config.settings import GROQ_API_KEY, MODEL_NAME
from app.mcp.calendar_server import (
    list_upcoming_events,
    create_calendar_event,
)


# ============================================================
# LLM
# ============================================================

llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=MODEL_NAME,
    temperature=0,
)


# Pakistan Standard Time
TIMEZONE = ZoneInfo("Asia/Karachi")


# ============================================================
# MAIN CALENDAR AGENT
# ============================================================

def ask_calendar_agent(question: str) -> str:
    """
    Calendar specialist agent.

    Supports:
    - Listing upcoming meetings
    - Creating/scheduling meetings
    - Natural language date and time
    """

    try:

        # ----------------------------------------------------
        # First determine what the user wants.
        # ----------------------------------------------------

        action = detect_calendar_action(question)

        # ----------------------------------------------------
        # CREATE MEETING
        # ----------------------------------------------------

        if action == "CREATE":
            return create_meeting_from_question(question)

        # ----------------------------------------------------
        # LIST MEETINGS
        # ----------------------------------------------------

        if action == "LIST":
            return show_upcoming_meetings()

        # ----------------------------------------------------
        # UNKNOWN
        # ----------------------------------------------------

        return (
            "I can help you with Google Calendar.\n\n"
            "Examples:\n"
            "• Show my upcoming meetings\n"
            "• Create a meeting today from 5 PM to 6 PM\n"
            "• Fix my meeting today from 5 PM to 6 PM\n"
            "• Schedule an AI meeting tomorrow at 4 PM"
        )

    except Exception as error:

        return (
            "Calendar Agent Error:\n"
            f"{error}"
        )


# ============================================================
# DETECT CALENDAR ACTION
# ============================================================

def detect_calendar_action(
    question: str,
) -> str:
    """
    Determine whether the user wants to CREATE
    or LIST calendar events.
    """

    prompt = f"""
You are a Google Calendar intent classifier.

User request:
{question}

Classify the request into exactly ONE of these:

CREATE
LIST
UNKNOWN

Rules:

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


# ============================================================
# SHOW UPCOMING MEETINGS
# ============================================================

def show_upcoming_meetings() -> str:
    """
    Get and display upcoming Google Calendar events.
    """

    events = list_upcoming_events(10)

    if not events:
        return (
            "You don't have any upcoming "
            "calendar events."
        )

    result = [
        "Your upcoming calendar events:"
    ]

    for event in events:

        start_display = format_pakistan_datetime(
            event["start"]
        )

        end_display = format_pakistan_datetime(
            event["end"]
        )

        if (
            start_display["date"]
            == end_display["date"]
        ):
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

        result.append(
            f"\n• {event['summary']}"
            f"\n  Date: {start_display['date']}"
            f"\n  Time: {time_text} "
            f"(Pakistan Time)"
            f"\n  Location: "
            f"{event['location'] or 'Not specified'}"
        )

    return "\n".join(result)


# ============================================================
# CREATE MEETING FROM NATURAL LANGUAGE
# ============================================================

def create_meeting_from_question(
    question: str,
) -> str:
    """
    Understand natural-language meeting request,
    extract date/time information,
    and create the event.
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

    response = llm.invoke(
        extraction_prompt
    )

    parsed = parse_meeting_details(
        response.content
    )

    if not parsed:
        return (
            "I could not understand the meeting "
            "details.\n\n"
            "Example:\n"
            "Fix my meeting today from 5 PM to 6 PM."
        )

    title = parsed["title"]
    start = parsed["start"]
    end = parsed["end"]
    description = parsed["description"]

    # --------------------------------------------------------
    # Convert to datetime
    # --------------------------------------------------------

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
            "Fix my meeting today from 5 PM to 6 PM."
        )

    # --------------------------------------------------------
    # Make sure end is after start
    # --------------------------------------------------------

    if end_dt <= start_dt:

        end_dt = start_dt + timedelta(
            hours=1
        )

    # --------------------------------------------------------
    # Prevent past meetings
    # --------------------------------------------------------

    current_time = datetime.now(TIMEZONE)

    if start_dt < current_time:

        return (
            "The requested meeting time has already "
            "passed.\n\n"
            "Please provide a future time."
        )

    # --------------------------------------------------------
    # Create Google Calendar event
    # --------------------------------------------------------

    created = create_calendar_event(
        summary=title,
        start_time=start_dt.isoformat(),
        end_time=end_dt.isoformat(),
        description=description,
    )

    # --------------------------------------------------------
    # Format response
    # --------------------------------------------------------

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


# ============================================================
# PARSE MEETING DETAILS
# ============================================================

def parse_meeting_details(
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


# ============================================================
# FORMAT PAKISTAN DATETIME
# ============================================================

def format_pakistan_datetime(
    datetime_string: str,
) -> dict:
    """
    Convert ISO datetime to readable
    Pakistan date/time.
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