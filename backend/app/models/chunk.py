from sqlalchemy import Column, Integer, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.db.database import Base

class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(384), nullable=True)
    page_number = Column(Integer, nullable=True)
    document = relationship("Document", back_populates="chunks")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    document = relationship("Document")