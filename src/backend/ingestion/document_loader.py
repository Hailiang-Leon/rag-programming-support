import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from pypdf import PdfReader

from src.backend.ingestion.chunker import chunk_text


SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf"}


def read_text_file(file_path: Path) -> str:
    return file_path.read_text(encoding="utf-8")


def read_pdf_file(file_path: Path) -> str:
    reader = PdfReader(str(file_path))
    pages = []

    for page in reader.pages:
        page_text = page.extract_text() or ""
        pages.append(page_text)

    return "\n".join(pages)


def load_document(file_path: Path) -> dict:
    extension = file_path.suffix.lower()

    if extension == ".pdf":
        text = read_pdf_file(file_path)
    elif extension in {".txt", ".md"}:
        text = read_text_file(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_path}")

    return {
        "source": file_path.name,
        "path": str(file_path),
        "text": text,
    }


def load_documents(input_dir: Path) -> list[dict]:
    documents = []

    for file_path in sorted(input_dir.iterdir()):
        if file_path.name.startswith("."):
            continue

        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        documents.append(load_document(file_path))

    return documents


def build_chunks(
    input_dir: Path,
    output_file: Path,
    chunk_size: int = 800,
    chunk_overlap: int = 120,
) -> dict:
    documents = load_documents(input_dir)
    all_chunks = []

    for document in documents:
        chunks = chunk_text(
            text=document["text"],
            source=document["source"],
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        for chunk in chunks:
            all_chunks.append(
                {
                    "chunk_id": chunk.chunk_id,
                    "source": chunk.source,
                    "text": chunk.text,
                    "char_start": chunk.char_start,
                    "char_end": chunk.char_end,
                }
            )

    output = {
        "metadata": {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "input_dir": str(input_dir),
            "document_count": len(documents),
            "chunk_count": len(all_chunks),
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
        },
        "chunks": all_chunks,
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(output, indent=2), encoding="utf-8")

    return output


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build text chunks from raw source documents."
    )
    parser.add_argument("--input-dir", default="data/raw")
    parser.add_argument("--output-file", default="data/processed/chunks.json")
    parser.add_argument("--chunk-size", type=int, default=800)
    parser.add_argument("--chunk-overlap", type=int, default=120)

    args = parser.parse_args()

    output = build_chunks(
        input_dir=Path(args.input_dir),
        output_file=Path(args.output_file),
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )

    print("Document ingestion completed.")
    print(f"Documents processed: {output['metadata']['document_count']}")
    print(f"Chunks created: {output['metadata']['chunk_count']}")
    print(f"Output file: {args.output_file}")


if __name__ == "__main__":
    main()