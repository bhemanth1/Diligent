import os
import uuid
from typing import List
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone

load_dotenv()

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "knowledge")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "jarvis-knowledge")


def read_files(paths: List[str]):
    for p in paths:
        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read().strip()
            if text:
                yield {"text": text, "source": os.path.basename(p)}


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunks.append(text[start:end])
        start = end - overlap
        if start < 0:
            start = 0
        if start >= len(text):
            break
    return chunks


def main():
    if not PINECONE_API_KEY:
        raise RuntimeError("PINECONE_API_KEY not set in environment")
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX)
    embedder = SentenceTransformer("all-MiniLM-L6-v2")

    paths = []
    for root, _, files in os.walk(DATA_DIR):
        for name in files:
            if name.lower().endswith((".txt", ".md")):
                paths.append(os.path.join(root, name))
    if not paths:
        print("No .txt or .md files found in knowledge/. Add files and rerun.")
        return

    vectors = []
    for doc in read_files(paths):
        for i, ch in enumerate(chunk_text(doc["text"])):
            vec = embedder.encode([ch], normalize_embeddings=True)[0].tolist()
            vid = str(uuid.uuid4())
            vectors.append({
                "id": vid,
                "values": vec,
                "metadata": {"text": ch, "source": doc["source"]},
            })

            if len(vectors) >= 100:
                index.upsert(vectors=vectors)
                vectors = []
    if vectors:
        index.upsert(vectors=vectors)
    print("Ingestion complete.")


if __name__ == "__main__":
    main()
