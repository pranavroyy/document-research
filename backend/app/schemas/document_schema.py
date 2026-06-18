from pydantic import BaseModel
from datetime import datetime


class DocumentResponse(BaseModel):
    id: int
    filename: str
    title: str | None
    created_at: datetime

    class Config:
        from_attributes = True