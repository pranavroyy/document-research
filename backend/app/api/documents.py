from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.document_service import ingest_document, get_documents

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload")
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    return ingest_document(db, file)


@router.get("")
def list_documents(db: Session = Depends(get_db)):
    return get_documents(db)