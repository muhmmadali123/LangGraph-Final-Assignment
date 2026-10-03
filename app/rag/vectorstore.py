from pinecone import Pinecone

from app.config.settings import (
    PINECONE_API_KEY,
    PINECONE_INDEX_NAME,
)


def get_pinecone_index():
    """Return the Pinecone index used by the RAG system."""

    if not PINECONE_API_KEY:
        raise ValueError("PINECONE_API_KEY is missing from .env")

    pc = Pinecone(api_key=PINECONE_API_KEY)

    return pc.Index(PINECONE_INDEX_NAME)