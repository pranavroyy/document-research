from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    title: str | None = None
    authors: list[str] = Field(default_factory=list)
    abstract: str | None = None
    keywords: list[str] = Field(default_factory=list)
    page_count: int | None = None