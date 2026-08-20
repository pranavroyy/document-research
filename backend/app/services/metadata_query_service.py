
def build_metadata_answer(intent, documents) -> str:
    if not documents:
        return "No documents found."

    lines = []

    for doc in documents:
        name = doc.title or doc.filename

        if intent.entity == "authors":
            authors = normalize_authors(doc.authors)

            if not authors:
                value = "Authors not found."
            elif intent.operation == "count":
                value = (
                    f"There are {len(authors)} authors:\n"
                    + "\n".join(
                        [f"{i + 1}. {author}" for i, author in enumerate(authors)]
                    )
                )
            else:
                value = (
                    "Authors:\n"
                    + "\n".join(
                        [f"{i + 1}. {author}" for i, author in enumerate(authors)]
                    )
                )

            lines.append(f"{name}\n{value}")

        elif intent.entity == "abstract":
            value = doc.abstract or "Abstract not found."
            lines.append(f"{name}\nAbstract: {value}")

        elif intent.entity == "title":
            lines.append(f"Title: {name}")

        elif intent.entity == "page_count":
            value = doc.page_count or "Unknown"
            lines.append(f"{name}\nPages: {value}")

        else:
            lines.append(f"{name}\nMetadata not available for this request.")

    return "\n\n".join(lines)


def build_metadata_sources(intent, documents):
    return [
        {
            "source_number": i + 1,
            "document_id": doc.id,
            "filename": doc.filename,
            "page_number": None,
            "chunk_id": None,
            "chunk_index": None,
            "content_preview": metadata_preview(intent, doc),
        }
        for i, doc in enumerate(documents)
    ]


def metadata_preview(intent, doc) -> str:
    if intent.entity == "authors":
        authors = normalize_authors(doc.authors)
        return ", ".join(authors) if authors else "Authors not found."

    if intent.entity == "abstract":
        return doc.abstract or "Abstract not found."

    if intent.entity == "title":
        return doc.title or doc.filename

    if intent.entity == "page_count":
        return str(doc.page_count or "Unknown")

    return doc.title or doc.filename


def normalize_authors(authors) -> list[str]:
    if not authors:
        return []

    if isinstance(authors, list):
        return [str(author).strip() for author in authors if str(author).strip()]

    if isinstance(authors, str):
        return [authors.strip()] if authors.strip() else []

    return []