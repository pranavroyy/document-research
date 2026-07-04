from sqlalchemy.orm import Session

from app.models.chunk import Chunk
from app.repositories.chunk_repository import (
    search_similar_chunks,
    keyword_search_chunks,
)
from app.services.embedding_service import generate_embedding
from app.services.reranking_service import rerank_chunks


def hybrid_retrieve_chunks(
    db: Session,
    question: str,
    top_k: int = 5,
    document_ids: list[int] | None = None,
) -> list[Chunk]:
    question_embedding = generate_embedding(question)

    candidate_k = max(top_k * 4, 20)

    vector_results = search_similar_chunks(
        db=db,
        embedding=question_embedding,
        top_k=candidate_k,
        document_ids=document_ids,
    )

    keyword_results = keyword_search_chunks(
        db=db,
        query_text=question,
        top_k=candidate_k,
        document_ids=document_ids,
    )

    merged: dict[int, Chunk] = {}

    for chunk in vector_results:
        merged[chunk.id] = chunk

    for chunk in keyword_results:
        merged[chunk.id] = chunk

    candidates = list(merged.values())

    return rerank_chunks(
        question=question,
        chunks=candidates,
        top_k=top_k,
    )
