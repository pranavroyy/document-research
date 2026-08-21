import ollama

from app.core.config import OLLAMA_HOST, OLLAMA_MODEL
from app.services.embedding_service import generate_embedding
from app.repositories.chunk_repository import search_similar_chunks_for_document

client = ollama.Client(host=OLLAMA_HOST)


def compare_documents(question: str, documents, db) -> tuple[str, list]:
    question_embedding = generate_embedding(question)

    context_blocks = []
    all_chunks = []

    for doc in documents:
        chunks = search_similar_chunks_for_document(
            db=db,
            embedding=question_embedding,
            document_id=doc.id,
            top_k=3,
        )

        all_chunks.extend(chunks)

        chunk_text = "\n\n".join(
            [f"Chunk {chunk.chunk_index}:\n{chunk.content}" for chunk in chunks]
        )

        authors = (
            ", ".join(doc.authors)
            if isinstance(doc.authors, list)
            else doc.authors or "Unknown"
        )

        context_blocks.append(
            f"""
Document: {doc.title or doc.filename}
Authors: {authors}
Abstract: {doc.abstract or "Not available"}

Relevant excerpts:
{chunk_text}
"""
        )

    context = "\n---\n".join(context_blocks)

    prompt = f"""
You are an AI research assistant.

Compare the documents using only the metadata and excerpts below.
Be direct, structured, and balanced.
Do not let one document dominate the answer.
Mention uncertainty if the excerpts do not contain enough evidence.

Context:
{context}

User request:
{question}
"""

    response = client.chat(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )

    return response["message"]["content"], all_chunks