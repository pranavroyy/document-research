from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.chunk import Chunk
from app.services.embedding_service import generate_embedding

router = APIRouter(prefix="/search", tags=["search"])


class SearchRequest(BaseModel):
    question: str
    top_k: int = 5


@router.post("")
def search_chunks(
    request: SearchRequest,
    db: Session = Depends(get_db)
):
    question_embedding = generate_embedding(request.question)

    results = (
        db.query(Chunk)
        .order_by(Chunk.embedding.cosine_distance(question_embedding))
        .limit(request.top_k)
        .all()
    )

    return {
        "question": request.question,
        "results": [
            {
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content[:800]
            }
            for chunk in results
        ]
    }