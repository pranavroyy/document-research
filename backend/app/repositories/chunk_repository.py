from sqlalchemy import func, desc
from sqlalchemy.orm import Session
from app.models.chunk import Chunk


def create_chunks(db: Session, chunks: list[Chunk]) -> None:
    db.add_all(chunks)
    db.commit()

def keyword_search_chunks(
    db: Session,
    query_text: str,
    top_k: int,
    document_ids: list[int] | None = None,
) -> list[Chunk]:
    query = db.query(Chunk)

    if document_ids:
        query = query.filter(Chunk.document_id.in_(document_ids))

    search_query = func.plainto_tsquery("english", query_text)
    search_vector = func.to_tsvector("english", Chunk.content)

    return (
        query
        .filter(search_vector.op("@@")(search_query))
        .order_by(desc(func.ts_rank(search_vector, search_query)))
        .limit(top_k)
        .all()
    )

def search_similar_chunks(
    db: Session,
    embedding: list[float],
    top_k: int,
    document_ids: list[int] | None = None,
) -> list[Chunk]:
    query = db.query(Chunk)

    if document_ids:
        query = query.filter(Chunk.document_id.in_(document_ids))

    return (
        query
        .order_by(Chunk.embedding.cosine_distance(embedding))
        .limit(top_k)
        .all()
    )


def search_similar_chunks_for_document(
    db: Session,
    embedding: list[float],
    document_id: int,
    top_k: int,
) -> list[Chunk]:
    return (
        db.query(Chunk)
        .filter(Chunk.document_id == document_id)
        .order_by(Chunk.embedding.cosine_distance(embedding))
        .limit(top_k)
        .all()
    )