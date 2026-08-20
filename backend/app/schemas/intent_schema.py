from pydantic import BaseModel
from typing import Literal


class QueryIntent(BaseModel):
    route: Literal["metadata", "synthesis", "comparison", "rag"]
    entity: Literal[
        "title",
        "authors",
        "abstract",
        "page_count",
        "keywords",
        "year",
        "venue",
        "doi",
    ] | None = None
    operation: Literal["get", "list", "count", "summarize", "explain", "compare"] | None = None
    confidence: float = 0.0