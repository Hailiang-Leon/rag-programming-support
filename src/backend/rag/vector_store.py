import argparse
import json
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from src.backend.config import settings


DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def load_chunks(chunks_file: Path) -> list[dict]:
    """
    Load processed text chunks from a JSON file created by the ingestion pipeline.
    """
    if not chunks_file.exists():
        raise FileNotFoundError(
            f"Chunks file not found: {chunks_file}. "
            "Run the document ingestion step first."
        )

    data = json.loads(chunks_file.read_text(encoding="utf-8"))
    return data.get("chunks", [])


def create_chroma_client(persist_dir: Path) -> chromadb.PersistentClient:
    """
    Create a persistent ChromaDB client.
    The database files are stored locally and ignored by Git.
    """
    persist_dir.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(persist_dir))


def get_or_create_collection(
    client: chromadb.PersistentClient,
    collection_name: str,
):
    """
    Create or reuse a ChromaDB collection.
    Cosine distance is suitable for sentence embedding similarity.
    """
    return client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )


def build_vector_store(
    chunks_file: Path,
    persist_dir: Path,
    collection_name: str,
    embedding_model_name: str = DEFAULT_EMBEDDING_MODEL,
) -> dict:
    """
    Build or update a ChromaDB vector store from processed chunks.
    """
    chunks = load_chunks(chunks_file)

    if not chunks:
        raise ValueError("No chunks found. Run document ingestion with valid source files first.")

    model = SentenceTransformer(embedding_model_name)
    client = create_chroma_client(persist_dir)
    collection = get_or_create_collection(client, collection_name)

    ids = [chunk["chunk_id"] for chunk in chunks]
    documents = [chunk["text"] for chunk in chunks]
    metadatas = [
        {
            "source": chunk["source"],
            "char_start": chunk["char_start"],
            "char_end": chunk["char_end"],
        }
        for chunk in chunks
    ]

    embeddings = model.encode(documents, convert_to_numpy=True).tolist()

    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    return {
        "collection_name": collection_name,
        "persist_dir": str(persist_dir),
        "embedding_model": embedding_model_name,
        "chunk_count": len(chunks),
    }


def query_vector_store(
    query: str,
    persist_dir: Path,
    collection_name: str,
    embedding_model_name: str = DEFAULT_EMBEDDING_MODEL,
    top_k: int = 3,
) -> list[dict]:
    """
    Query the vector store and return the most relevant chunks.
    """
    model = SentenceTransformer(embedding_model_name)
    client = create_chroma_client(persist_dir)
    collection = get_or_create_collection(client, collection_name)

    query_embedding = model.encode([query], convert_to_numpy=True).tolist()[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
    )

    retrieved_chunks = []

    for index, chunk_id in enumerate(results["ids"][0]):
        retrieved_chunks.append(
            {
                "chunk_id": chunk_id,
                "source": results["metadatas"][0][index]["source"],
                "text": results["documents"][0][index],
                "distance": results["distances"][0][index],
            }
        )

    return retrieved_chunks


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build and query a ChromaDB vector store from processed chunks."
    )
    parser.add_argument("--chunks-file", default="data/processed/chunks.json")
    parser.add_argument("--persist-dir", default=settings.vector_db_path)
    parser.add_argument("--collection-name", default=settings.collection_name)
    parser.add_argument("--embedding-model", default=DEFAULT_EMBEDDING_MODEL)
    parser.add_argument("--query", default="What is a variable in Python?")
    parser.add_argument("--top-k", type=int, default=settings.top_k)

    args = parser.parse_args()

    build_summary = build_vector_store(
        chunks_file=Path(args.chunks_file),
        persist_dir=Path(args.persist_dir),
        collection_name=args.collection_name,
        embedding_model_name=args.embedding_model,
    )

    print("Vector store build completed.")
    print(f"Collection: {build_summary['collection_name']}")
    print(f"Chunks stored: {build_summary['chunk_count']}")
    print(f"Persist directory: {build_summary['persist_dir']}")
    print(f"Embedding model: {build_summary['embedding_model']}")

    print("\nTest query:")
    print(args.query)

    retrieved_chunks = query_vector_store(
        query=args.query,
        persist_dir=Path(args.persist_dir),
        collection_name=args.collection_name,
        embedding_model_name=args.embedding_model,
        top_k=args.top_k,
    )

    print("\nRetrieved chunks:")
    for rank, chunk in enumerate(retrieved_chunks, start=1):
        print(f"\nRank {rank}")
        print(f"Chunk ID: {chunk['chunk_id']}")
        print(f"Source: {chunk['source']}")
        print(f"Distance: {chunk['distance']:.4f}")
        print(f"Text preview: {chunk['text'][:250]}...")


if __name__ == "__main__":
    main()