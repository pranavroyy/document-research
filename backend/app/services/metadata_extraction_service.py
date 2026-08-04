import json
import ollama

from app.core.config import OLLAMA_HOST, OLLAMA_MODEL
from app.schemas.metadata_schema import DocumentMetadata

client = ollama.Client(host=OLLAMA_HOST)


def extract_metadata_with_llm(
    markdown: str,
    page_count: int | None = None,
) -> DocumentMetadata:
    sample = markdown[:4000]

    prompt = f"""
Extract document metadata from the text below.

Return ONLY valid JSON. Do not include markdown. Do not include explanation.

Schema:
{{
  "title": string or null,
  "authors": array of author names only,
  "abstract": string or null,
  "keywords": array of strings
}}

Rules:
- Authors must be individual names only.
- Do not include affiliations, universities, countries, emails, footnote symbols, or section titles as authors.
- If unsure, return an empty array for authors.
- Do not invent metadata.

Document text:
{sample}
"""

    response = client.chat(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}],
        format="json",
    )

    raw = response["message"]["content"]
    data = json.loads(raw)

    metadata = DocumentMetadata(**data)
    metadata.page_count = page_count

    return metadata