from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from app.agents.rag_agent import ask_rag_agent
from app.agents.github_agent import ask_github_agent
from app.agents.calendar_agent import ask_calendar_agent
from app.agents.email_agent import ask_email_agent
from app.agents.supervisor import ask_supervisor


class AgentState(TypedDict):
    user_input: str
    response: str


def supervisor_node(state: AgentState):
    """
    Route the user's request to the correct specialist agent.
    """

    user_input = state["user_input"]
    text = user_input.lower().strip()

    # ========================================================
    # RAG AGENT
    # ========================================================

    rag_keywords = [
        "attendance",
        "attendance register",
        "student",
        "students",
        "present",
        "absent",
        "roll number",
    ]

    if any(
        keyword in text
        for keyword in rag_keywords
    ):
        return {
            "response": ask_rag_agent(user_input)
        }

    # ========================================================
    # GITHUB AGENT
    # ========================================================

    github_keywords = [
        "github",
        "repository",
        "repo",
        "readme",
        "github issue",
        "github issues",
        "stars",
        "forks",
    ]

    if any(
        keyword in text
        for keyword in github_keywords
    ):
        return {
            "response": ask_github_agent(user_input)
        }

    # ========================================================
    # EMAIL AGENT
    #
    # IMPORTANT:
    # Email is checked before Calendar because an email
    # request can contain the word "meeting".
    # ========================================================

    email_keywords = [
        "email",
        "e-mail",
        "gmail",
        "mail",
        "draft email",
        "draft an email",
        "create email",
        "create an email",
        "write email",
        "write an email",
        "send email",
        "send an email",
        "send mail",
        "send a mail",
    ]

    if any(
        keyword in text
        for keyword in email_keywords
    ):
        return {
            "response": ask_email_agent(user_input)
        }

    # ========================================================
    # CALENDAR AGENT
    # ========================================================

    calendar_keywords = [
        "calendar",
        "meeting",
        "meetings",
        "schedule",
        "scheduled",
        "event",
        "events",
        "appointment",
        "appointments",
        "fix my meeting",
        "fix a meeting",
        "fix meeting",
        "set my meeting",
        "set a meeting",
        "set meeting",
        "book my meeting",
        "book a meeting",
        "book meeting",
        "arrange a meeting",
        "arrange meeting",
        "create meeting",
        "create a meeting",
        "add meeting",
        "add a meeting",
    ]

    if any(
        keyword in text
        for keyword in calendar_keywords
    ):
        return {
            "response": ask_calendar_agent(user_input)
        }

    # ========================================================
    # GENERAL SUPERVISOR
    # ========================================================

    return {
        "response": ask_supervisor(user_input)
    }


def build_graph():
    """
    Build and compile the LangGraph workflow.
    """

    graph = StateGraph(AgentState)

    graph.add_node(
        "supervisor",
        supervisor_node,
    )

    graph.add_edge(
        START,
        "supervisor",
    )

    graph.add_edge(
        "supervisor",
        END,
    )

    return graph.compile()


workflow = build_graph()