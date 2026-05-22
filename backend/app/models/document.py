from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base

class Document(Base):
    __tablename__ = "documents"
    
    chunks = relationship("Chunk", back_populates="document")
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    title = Column(String, nullable=True)
    authors = Column(JSON, nullable=True)
    abstract = Column(Text, nullable=True)
    page_count = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())