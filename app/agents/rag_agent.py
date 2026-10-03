from langchain_groq import ChatGroq

from app.config.settings import GROQ_API_KEY, MODEL_NAME
from app.rag.retriever import search_pdf


llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=MODEL_NAME,
    temperature=0,
)


def ask_rag_agent(question: str) -> str:
    """
    Answer a question using information retrieved from the PDF.
    """

    relevant_chunks = search_pdf(question)

    if not relevant_chunks:
        return "I could not find relevant information in the provided PDF."

    context = "\n\n---\n\n".join(relevant_chunks)

    prompt = f"""
You are a document-based RAG assistant.

Answer the user's question using ONLY the information
provided in the PDF context below.

If the answer cannot be found in the context, say:
"I could not find that information in the provided PDF."

Do not invent information.

PDF CONTEXT:
{context}

USER QUESTION:
{question}
"""

    response = llm.invoke(prompt)

    return response.content