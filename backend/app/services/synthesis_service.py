import ollama

from app.core.config import OLLAMA_HOST, OLLAMA_MODEL

client = ollama.Client(host=OLLAMA_HOST)


def synthesize_answer(question: str, documents) -> str:
    document_blocks = []

    for doc in documents:
        block = f"""
Document: {doc.title or doc.filename}
Authors: {", ".join(doc.authors or []) if isinstance(doc.authors, list) else doc.authors or "Unknown"}
Abstract: {doc.abstract or "Not available"}
Pages: {doc.page_count or "Unknown"}
"""
        document_blocks.append(block)

    context = "\n---\n".join(document_blocks)

    prompt = f"""
You are an AI research assistant.

Answer the user's request directly using the document metadata below.
Do not say "based on the provided sources" unless necessary.
Do not mention Source 1, Source 2.
If the user asks for a summary, provide a clear concise summary.
If the user asks for an explanation, explain the document in a helpful way.

Document metadata:
{context}

User request:
{question}
"""

    response = client.chat(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )

    return response["message"]["content"]