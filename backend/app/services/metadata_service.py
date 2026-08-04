import re


def extract_document_metadata(pages: list[dict]) -> dict:
    first_page_text = pages[0]["text"] if pages else ""
    lines = [line.strip() for line in first_page_text.split("\n") if line.strip()]

    title = extract_title(lines)
    authors = extract_authors(lines)
    abstract = extract_abstract("\n".join(page["text"] for page in pages[:3]))

    return {
        "title": title,
        "authors": authors,
        "abstract": abstract,
        "page_count": len(pages),
    }


def extract_title(lines: list[str]) -> str | None:
    if not lines:
        return None

    candidates = []

    for line in lines[:15]:
        if len(line) > 15 and not line.lower().startswith(("abstract", "keywords", "index terms")):
            candidates.append(line)

    return candidates[0] if candidates else lines[0]


def extract_authors(lines: list[str]) -> str | None:
    # Simple heuristic:
    # Usually authors appear immediately after title in academic PDFs.
    possible_author_lines = []

    for line in lines[1:12]:
        lower = line.lower()

        if lower.startswith(("abstract", "keywords", "index terms", "introduction")):
            break

        if any(x in lower for x in ["university", "department", "institute", "school", "college"]):
            continue

        if "@" in line:
            continue

        if re.search(r"\d{4}", line):
            continue

        if len(line) > 3:
            possible_author_lines.append(line)

    if not possible_author_lines:
        return None

    return ", ".join(possible_author_lines[:3])


def extract_abstract(text: str) -> str | None:
    match = re.search(
        r"(?i)abstract\s*[\—\-:]?\s*(.*?)(?=\n\s*(?:keywords|index terms|1\.?\s*introduction|introduction)\b)",
        text,
        re.DOTALL,
    )

    if not match:
        return None

    abstract = " ".join(match.group(1).split())
    return abstract[:2000] if abstract else None