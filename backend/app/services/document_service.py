from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.chunk import Chunk
from app.repositories.document_repository import create_document, list_documents
from app.repositories.chunk_repository import create_chunks
from app.services.document_parser_service import parse_document
from app.services.page_parser_service import extract_pages
from app.services.metadata_extraction_service import extract_metadata_with_llm
from app.services.chunking_service import chunk_text
from app.services.embedding_service import generate_embedding


def ingest_document(db: Session, file: UploadFile):
    parsed = parse_document(file)
    markdown = parsed["markdown"]

    metadata = extract_metadata_with_llm(
        markdown=markdown,
        page_count=parsed["page_count"],
    )

    document = create_document(
        db=db,
        filename=file.filename,
        title=metadata.title or file.filename,
        authors=metadata.authors,
        abstract=metadata.abstract,
        page_count=metadata.page_count,
    )

    file.file.seek(0)
    pages = extract_pages(file)

    chunk_rows = []
    chunk_index = 0
    total_text_length = 0

    for page in pages:
        page_chunks = chunk_text(page["text"])
        total_text_length += len(page["text"])

        for chunk in page_chunks:
            chunk_rows.append(
                Chunk(
                    document_id=document.id,
                    chunk_index=chunk_index,
                    page_number=page["page_number"],
                    content=chunk,
                    embedding=generate_embedding(chunk),
                )
            )
            chunk_index += 1

    create_chunks(db, chunk_rows)

    return {
        "id": document.id,
        "filename": document.filename,
        "title": document.title,
        "authors": document.authors,
        "abstract": document.abstract,
        "page_count": document.page_count,
        "text_length": total_text_length,
        "chunk_count": len(chunk_rows),
        "preview": chunk_rows[0].content[:500] if chunk_rows else "",
    }


def get_documents(db: Session):
    return list_documents(db)
