import ollama

from app.core.config import OLLAMA_MODEL, OLLAMA_HOST

client = ollama.Client(host=OLLAMA_HOST)

OLLAMA_OPTIONS = {
    "temperature": 0.2,
}


def build_rag_prompt(question: str, contexts: list[str]) -> str:
    context_text = "\n\n---\n\n".join(contexts)

    return f"""
You are an AI research assistant.

Answer the user's question using only the retrieved context below.

Rules:
- Answer directly and naturally.
- Do not say "Source 1", "Source 2", "provided sources", or "retrieved context".
- Do not mention citations inside the answer.
- The UI displays sources separately.
- If the context does not contain enough information, say so clearly.
- If values conflict, explain the conflict naturally.
- Be concise but complete.

Retrieved context:
{context_text}

User question:
{question}
"""


def generate_answer(question: str, contexts: list[str]) -> str:
    prompt = build_rag_prompt(question, contexts)

    response = client.chat(
        model=OLLAMA_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        options=OLLAMA_OPTIONS,
    )

    return response["message"]["content"]


def stream_answer(question: str, contexts: list[str]):
    prompt = build_rag_prompt(question, contexts)

    stream = client.chat(
        model=OLLAMA_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        stream=True,
        options=OLLAMA_OPTIONS,
    )

    for chunk in stream:
        content = chunk.get("message", {}).get("content", "")
        if content:
            yield content