from sentence_transformers import SentenceTransformer

from app.rag.vectorstore import get_pinecone_index


EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)


def search_pdf(question: str, top_k: int = 3) -> list[str]:
    """
    Search Pinecone for the most relevant PDF chunks.
    """

    index = get_pinecone_index()

    query_embedding = embedding_model.encode(
        question,
        normalize_embeddings=True,
    ).tolist()

    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True,
    )

    chunks = []

    for match in results.matches:
        metadata = match.metadata or {}
        text = metadata.get("text")

        if text:
            chunks.append(text)

    return chunks