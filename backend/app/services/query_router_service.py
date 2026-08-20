import json

import ollama
from pydantic import ValidationError

from app.core.config import OLLAMA_HOST, OLLAMA_MODEL
from app.schemas.intent_schema import QueryIntent

client = ollama.Client(host=OLLAMA_HOST)


def detect_intent(question: str) -> QueryIntent:
    deterministic_intent = detect_deterministic_intent(question)

    if deterministic_intent:
        return deterministic_intent

    prompt = f"""
        You are an intent classifier for a document question-answering system.

        Return ONLY valid JSON.

        Choose exactly one route:

        1. metadata
        Use for document-level bibliographic properties only.

        Valid metadata entities:
        - title
        - authors
        - abstract
        - page_count
        - keywords
        - year
        - venue
        - doi

        2. synthesis
        Use for broad document-level requests such as summaries, explanations, overviews, simplification, key points, or main ideas.

        3. comparison
        Use when the user asks to compare or contrast documents, methods, ideas, results, claims, strengths, or weaknesses.

        4. rag
        Use for specific factual questions that require reading document content, including definitions, technical terms, acronyms, methods, datasets, experiments, metrics, equations, results, limitations, and findings.

        Rules:
        - For metadata route, entity MUST be one of the valid metadata entities listed above.
        - Do not invent entity names.
        - If the question asks for a document-level property, use metadata.
        - If the question asks about content inside the paper, use rag.
        - If unsure, use rag.

        Return schema:
        {{
        "route": "metadata" | "synthesis" | "comparison" | "rag",
        "entity": "title" | "authors" | "abstract" | "page_count" | "keywords" | "year" | "venue" | "doi" | null,
        "operation": "get" | "list" | "count" | "summarize" | "explain" | "compare" | null,
        "confidence": number
        }}

        User question:
        {question}
        """

    try:
        response = client.chat(
            model=OLLAMA_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            format="json",
        )

        data = json.loads(response["message"]["content"])
        intent = QueryIntent(**data)

        if intent.route == "rag" and intent.confidence == 0:
            intent.confidence = 0.5

        return intent

    except (json.JSONDecodeError, ValidationError, KeyError, TypeError):
        return QueryIntent(
            route="rag",
            entity=None,
            operation=None,
            confidence=0.5,
        )


def detect_deterministic_intent(question: str) -> QueryIntent | None:
    q = question.lower().strip().replace("?", "")

    # Short technical terms/acronyms should go to RAG, not metadata.
    if len(q.split()) <= 3 and q not in {
        "title",
        "authors",
        "author",
        "abstract",
        "keywords",
        "pages",
        "page",
    }:
        return QueryIntent(
            route="rag",
            entity=None,
            operation=None,
            confidence=0.8,
        )

    if "page" in q:
        return QueryIntent(
            route="metadata",
            entity="page_count",
            operation="count",
            confidence=1.0,
        )

    return None
