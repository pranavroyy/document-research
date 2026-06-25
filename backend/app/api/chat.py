import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.config import RETRIEVAL_MODE, RERANKING_ENABLED
from app.db.database import get_db
from app.repositories.document_repository import get_documents_by_ids
from app.schemas.chat_schema import ChatRequest
from app.services.comparison_service import compare_documents
from app.services.hybrid_retrieval_service import hybrid_retrieve_chunks
from app.services.llm_service import generate_answer, stream_answer
from app.services.metadata_query_service import (
    build_metadata_answer,
    build_metadata_sources,
)
from app.services.query_router_service import detect_intent
from app.services.synthesis_service import synthesize_answer

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
def chat_with_documents(request: ChatRequest, db: Session = Depends(get_db)):
    intent = detect_intent(request.question)
    documents = get_documents_by_ids(db, request.document_ids)

    if intent.route == "metadata":
        return {
            "question": request.question,
            "intent": intent.model_dump(),
            "answer": build_metadata_answer(intent, documents),
            "sources": build_metadata_sources(intent, documents),
        }

    if intent.route == "synthesis":
        answer = synthesize_answer(request.question, documents)
        return {
            "question": request.question,
            "intent": intent.model_dump(),
            "answer": answer,
            "sources": build_document_sources(documents),
        }

    if intent.route == "comparison":
        answer, chunks = compare_documents(
            question=request.question,
            documents=documents,
            db=db,
        )
        return {
            "question": request.question,
            "intent": intent.model_dump(),
            "answer": answer,
            "sources": build_chunk_sources(chunks),
        }

    chunks = hybrid_retrieve_chunks(
        db=db,
        question=request.question,
        top_k=request.top_k,
        document_ids=request.document_ids,
    )

    answer = generate_answer(request.question, [chunk.content for chunk in chunks])

    return {
        "question": request.question,
        "intent": intent.model_dump(),
        "retrieval": build_retrieval_metadata(request.top_k),
        "answer": answer,
        "sources": build_chunk_sources(chunks),
    }


@router.post("/stream")
def stream_chat_with_documents(request: ChatRequest, db: Session = Depends(get_db)):
    return StreamingResponse(
        stream_chat_events(request=request, db=db),
        media_type="text/event-stream",
    )


def stream_chat_events(request: ChatRequest, db: Session):
    intent = detect_intent(request.question)
    documents = get_documents_by_ids(db, request.document_ids)

    yield sse("intent", intent.model_dump())

    if intent.route == "metadata":
        answer = build_metadata_answer(intent, documents)
        sources = build_metadata_sources(intent, documents)

        yield sse("token", answer)
        yield sse("sources", sources)
        yield sse("done", {"done": True})
        return

    if intent.route == "synthesis":
        answer = synthesize_answer(request.question, documents)
        sources = build_document_sources(documents)

        yield sse("token", answer)
        yield sse("sources", sources)
        yield sse("done", {"done": True})
        return

    if intent.route == "comparison":
        answer, chunks = compare_documents(
            question=request.question,
            documents=documents,
            db=db,
        )

        yield sse("token", answer)
        yield sse("sources", build_chunk_sources(chunks))
        yield sse("done", {"done": True})
        return

    chunks = hybrid_retrieve_chunks(
        db=db,
        question=request.question,
        top_k=request.top_k,
        document_ids=request.document_ids,
    )

    yield sse("retrieval", build_retrieval_metadata(request.top_k))

    contexts = [chunk.content for chunk in chunks]

    for token in stream_answer(request.question, contexts):
        yield sse("token", token)

    yield sse("sources", build_chunk_sources(chunks))
    yield sse("done", {"done": True})


def sse(event: str, data):
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def build_retrieval_metadata(top_k: int):
    return {
        "mode": RETRIEVAL_MODE,
        "reranking": RERANKING_ENABLED,
        "top_k": top_k,
    }


def build_chunk_sources(chunks):
    return [
        {
            "source_number": i + 1,
            "chunk_id": chunk.id,
            "document_id": chunk.document_id,
            "filename": chunk.document.filename if chunk.document else None,
            "page_number": chunk.page_number,
            "chunk_index": chunk.chunk_index,
            "content_preview": chunk.content[:300],
        }
        for i, chunk in enumerate(chunks)
    ]


def build_document_sources(documents):
    return [
        {
            "source_number": i + 1,
            "document_id": doc.id,
            "filename": doc.filename,
            "page_number": None,
            "chunk_id": None,
            "chunk_index": None,
            "content_preview": doc.abstract or doc.title or doc.filename,
        }
        for i, doc in enumerate(documents)
    ]