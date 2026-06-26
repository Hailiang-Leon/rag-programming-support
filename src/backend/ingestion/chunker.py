from dataclasses import dataclass


@dataclass
class TextChunk:
    chunk_id: str
    source: str
    text: str
    char_start: int
    char_end: int


def clean_text(text: str) -> str:
    """
    Clean raw text before chunking.
    This keeps the prototype simple and transparent for demonstration.
    """
    lines = [line.strip() for line in text.splitlines()]
    non_empty_lines = [line for line in lines if line]
    return "\n".join(non_empty_lines)


def chunk_text(
    text: str,
    source: str,
    chunk_size: int = 800,
    chunk_overlap: int = 120,
) -> list[TextChunk]:
    """
    Split text into overlapping character-based chunks.

    Character-based chunking is simple, predictable, and easy to explain
    in the interim report and final demonstration.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0.")

    if chunk_overlap < 0:
        raise ValueError("chunk_overlap cannot be negative.")

    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size.")

    cleaned_text = clean_text(text)

    if not cleaned_text:
        return []

    chunks = []
    start = 0
    chunk_number = 1

    while start < len(cleaned_text):
        end = min(start + chunk_size, len(cleaned_text))
        chunk_content = cleaned_text[start:end].strip()

        if chunk_content:
            chunks.append(
                TextChunk(
                    chunk_id=f"{source}_chunk_{chunk_number:03d}",
                    source=source,
                    text=chunk_content,
                    char_start=start,
                    char_end=end,
                )
            )
            chunk_number += 1

        if end == len(cleaned_text):
            break

        start = end - chunk_overlap

    return chunks