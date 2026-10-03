from pathlib import Path

from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.rag.vectorstore import get_pinecone_index


# Embedding model
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)


def load_pdf(pdf_path: str) -> str:
    """Extract text from a PDF file."""

    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    reader = PdfReader(str(path))

    pages = []

    for page in reader.pages:
        text = page.extract_text()

        if text:
            pages.append(text)

    return "\n\n".join(pages)


def split_text(text: str):
    """Split PDF text into smaller chunks."""

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
    )

    return splitter.split_text(text)


def ingest_pdf(pdf_path: str):
    """Load, split, embed and upload a PDF to Pinecone."""

    print(f"Loading PDF: {pdf_path}")

    text = load_pdf(pdf_path)

    if not text.strip():
        raise ValueError("No readable text was found in the PDF.")

    chunks = split_text(text)

    print(f"Created {len(chunks)} chunks.")

    embeddings = embedding_model.encode(
        chunks,
        normalize_embeddings=True,
    )

    index = get_pinecone_index()

    vectors = []

    for i, (chunk, embedding) in enumerate(
        zip(chunks, embeddings)
    ):
        vectors.append(
            {
                "id": f"pdf-chunk-{i}",
                "values": embedding.tolist(),
                "metadata": {
                    "source": Path(pdf_path).name,
                    "text": chunk,
                    "chunk": i,
                },
            }
        )

    index.upsert(vectors=vectors)

    print(f"Uploaded {len(vectors)} vectors to Pinecone.")

    return len(vectors)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python -m app.rag.ingest <pdf_path>")
        raise SystemExit(1)

    ingest_pdf(sys.argv[1])