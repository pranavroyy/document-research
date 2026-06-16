import re
from langchain_text_splitters import RecursiveCharacterTextSplitter


def clean_markdown(text: str) -> str:
    lines = []

    for line in text.splitlines():
        stripped = line.strip()

        if not stripped:
            continue

        # remove image placeholders
        if stripped.lower() in {"<!-- image -->", "<!-- image -->"}:
            continue

        # remove markdown table separator rows
        if re.fullmatch(r"[\|\-\:\s]+", stripped):
            continue

        # remove very long dashed lines
        if re.fullmatch(r"[-\s]{20,}", stripped):
            continue

        lines.append(stripped)

    return "\n".join(lines)


def chunk_text(text: str) -> list[str]:
    cleaned_text = clean_markdown(text)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
        is_separator_regex=False,
    )

    chunks = text_splitter.split_text(cleaned_text)

    return [
        chunk.replace("\x00", "").replace("\u0000", "").strip()
        for chunk in chunks
        if len(chunk.strip()) > 80
    ]