from sqlalchemy.orm import Session
from app.models.document import Document


def create_document(
    db: Session,
    filename: str,
    title: str | None = None,
    authors: str | None = None,
    abstract: str | None = None,
    page_count: int | None = None,
) -> Document:
    document = Document(
        filename=filename,
        title=title,
        authors=authors,
        abstract=abstract,
        page_count=page_count,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document

def get_documents_by_ids(db: Session, document_ids: list[int] | None = None) -> list[Document]:
    query = db.query(Document)

    if document_ids:
        query = query.filter(Document.id.in_(document_ids))

    return query.order_by(Document.created_at.desc()).all()

def list_documents(db: Session) -> list[Document]:
    return db.query(Document).order_by(Document.created_at.desc()).all()