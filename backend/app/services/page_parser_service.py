import os
import tempfile
from fastapi import UploadFile
from pypdf import PdfReader


def clean_text(text: str) -> str:
    return text.replace("\x00", "").replace("\u0000", "").strip()


def extract_pages(file: UploadFile) -> list[dict]:
    file.file.seek(0)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file.file.read())
        tmp_path = tmp.name

    try:
        reader = PdfReader(tmp_path)
        pages = []

        for index, page in enumerate(reader.pages):
            text = clean_text(page.extract_text() or "")

            if text:
                pages.append(
                    {
                        "page_number": index + 1,
                        "text": text,
                    }
                )

        return pages

    finally:
        os.remove(tmp_path)