from sentence_transformers import CrossEncoder

from app.models.chunk import Chunk

reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


def rerank_chunks(
    question: str,
    chunks: list[Chunk],
    top_k: int = 5,
) -> list[Chunk]:
    if not chunks:
        return []

    pairs = [(question, chunk.content) for chunk in chunks]
    scores = reranker.predict(pairs)

    ranked = sorted(
        zip(chunks, scores),
        key=lambda item: item[1],
        reverse=True,
    )

    return [chunk for chunk, _score in ranked[:top_k]]