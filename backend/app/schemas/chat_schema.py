from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    top_k: int = 5
    document_ids: list[int] | None = None