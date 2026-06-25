import os
import tempfile
from fastapi import UploadFile

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption


def parse_document(file: UploadFile) -> dict:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file.file.read())
        tmp_path = tmp.name

    try:
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = False
        pipeline_options.do_table_structure = False

        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options
                )
            }
        )

        result = converter.convert(tmp_path)
        doc = result.document

        markdown = doc.export_to_markdown()

        return {
            "markdown": markdown,
            "page_count": len(getattr(doc, "pages", []) or []),
        }

    finally:
        os.remove(tmp_path)