from langchain_groq import ChatGroq

from app.config.settings import GROQ_API_KEY, MODEL_NAME


llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=MODEL_NAME,
    temperature=0,
)


def ask_supervisor(user_input: str) -> str:
    """
    Basic supervisor LLM.
    Later this will become the LangGraph router.
    """

    system_prompt = """
You are the supervisor of a multi-agent LangGraph system.

The system will contain these specialist agents:

1. RAG Agent
   - Answers questions from documents/PDF files.

2. GitHub Agent
   - Handles GitHub-related questions using MCP.

3. Calendar Agent
   - Reads and manages Google Calendar meetings using MCP.

4. Email Agent
   - Writes drafts and sends emails using MCP.

For now, simply answer the user's request naturally.
Do not pretend that tools are available when they have not yet been connected.
"""

    response = llm.invoke(
        [
            ("system", system_prompt),
            ("human", user_input),
        ]
    )

    return response.content