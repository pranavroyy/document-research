from sqlalchemy.orm import Session

from app.repositories.chunk_repository import search_similar_chunks
from app.services.embedding_service import generate_embedding


def retrieve_relevant_chunks(
    db: Session,
    question: str,
    top_k: int,
    document_ids: list[int] | None = None,
):
    question_embedding = generate_embedding(question)

    return search_similar_chunks(
        db=db,
        embedding=question_embedding,
        top_k=top_k,
        document_ids=document_ids,
    )