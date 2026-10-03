from app.services.chunking_service import chunk_text, clean_markdown


def test_clean_markdown_removes_image_placeholders_and_blank_lines():
    text = "Hello\n\n<!-- image -->\n\nWorld"
    assert clean_markdown(text) == "Hello\nWorld"


def test_clean_markdown_removes_table_separator_rows():
    text = "| a | b |\n|---|---|\n| 1 | 2 |"
    assert clean_markdown(text) == "| a | b |\n| 1 | 2 |"


def test_chunk_text_drops_very_short_chunks():
    assert chunk_text("too short") == []


def test_chunk_text_splits_long_text_and_respects_size():
    paragraph = "Retrieval augmented generation combines search with language models. " * 40
    chunks = chunk_text(paragraph)
    assert len(chunks) > 1
    assert all(len(c) <= 1000 for c in chunks)


def test_chunk_text_strips_null_bytes():
    text = ("Some research text with a null byte\x00 inside it. " * 10)
    assert all("\x00" not in c for c in chunk_text(text))
