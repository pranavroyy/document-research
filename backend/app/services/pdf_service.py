from pypdf import PdfReader
from fastapi import UploadFile
import tempfile
import os


def clean_text(text: str) -> str:
    return text.replace("\x00", "").replace("\u0000", "").strip()


def extract_pages_from_pdf(file: UploadFile) -> list[dict]:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file.file.read())
        tmp_path = tmp.name

    try:
        reader = PdfReader(tmp_path)
        pages = []

        for i, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            page_text = clean_text(page_text)

            if page_text:
                pages.append({
                    "page_number": i + 1,
                    "text": page_text,
                })

        return pages

    finally:
        os.remove(tmp_path)