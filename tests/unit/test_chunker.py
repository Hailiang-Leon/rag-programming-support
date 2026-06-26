import pytest

from src.backend.ingestion.chunker import clean_text, chunk_text


def test_clean_text_removes_empty_lines_and_extra_spaces():
    raw_text = """
        Python Basics

        A variable stores a value.

        A list stores multiple values.
    """

    cleaned = clean_text(raw_text)

    assert cleaned == "Python Basics\nA variable stores a value.\nA list stores multiple values."


def test_chunk_text_returns_chunks_with_metadata():
    text = (
        "A variable is a name that stores a value. "
        "A list is a collection of values. "
        "A for loop repeats code for each item in a sequence."
    )

    chunks = chunk_text(
        text=text,
        source="sample.txt",
        chunk_size=60,
        chunk_overlap=10,
    )

    assert len(chunks) > 1
    assert chunks[0].chunk_id == "sample.txt_chunk_001"
    assert chunks[0].source == "sample.txt"
    assert chunks[0].char_start == 0
    assert chunks[0].char_end <= 60
    assert "variable" in chunks[0].text


def test_chunk_text_returns_empty_list_for_empty_text():
    chunks = chunk_text(
        text="   \n\n   ",
        source="empty.txt",
    )

    assert chunks == []


def test_chunk_text_rejects_invalid_chunk_size():
    with pytest.raises(ValueError, match="chunk_size must be greater than 0"):
        chunk_text(
            text="Some text",
            source="sample.txt",
            chunk_size=0,
            chunk_overlap=0,
        )


def test_chunk_text_rejects_negative_chunk_overlap():
    with pytest.raises(ValueError, match="chunk_overlap cannot be negative"):
        chunk_text(
            text="Some text",
            source="sample.txt",
            chunk_size=100,
            chunk_overlap=-1,
        )


def test_chunk_text_rejects_overlap_larger_than_chunk_size():
    with pytest.raises(ValueError, match="chunk_overlap must be smaller than chunk_size"):
        chunk_text(
            text="Some text",
            source="sample.txt",
            chunk_size=100,
            chunk_overlap=100,
        )