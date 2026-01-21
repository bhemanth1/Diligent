import os
import asyncio
import time
from typing import List, Tuple
import numpy as np
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
import httpx

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "jarvis-knowledge")
PINECONE_ENV = os.getenv("PINECONE_ENV", "us-east-1-aws")
EMBED_DIM = int(os.getenv("EMBED_DIM", "384"))
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL_NAME = os.getenv("MODEL_NAME", "llama3.1:8b")


def ensure_index(pc: Pinecone, name: str, dimension: int):
    # Parse env like "us-east-1-aws" -> region, cloud
    parts = PINECONE_ENV.split("-")
    if len(parts) >= 4:
        region = "-".join(parts[0:3])
        cloud = parts[3]
    elif len(parts) == 2:
        region, cloud = parts[0], parts[1]
    else:
        region, cloud = "us-east-1", "aws"

    existing = [idx["name"] for idx in pc.list_indexes()]  # type: ignore
    if name not in existing:
        pc.create_index(
            name=name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(cloud=cloud, region=region),
        )
        # Wait until the index is ready
        while True:
            desc = pc.describe_index(name)
            status = desc.get("status", {}) if isinstance(desc, dict) else desc.status
            if getattr(status, "ready", status.get("ready", False)):
                break
            time.sleep(1)


class RAGPipeline:
    def __init__(self):
        if not PINECONE_API_KEY:
            raise RuntimeError("PINECONE_API_KEY not set")
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        self.pc = Pinecone(api_key=PINECONE_API_KEY)
        ensure_index(self.pc, PINECONE_INDEX, EMBED_DIM)
        self.index = self.pc.Index(PINECONE_INDEX)
        self.http = httpx.AsyncClient(timeout=60)

    async def aclose(self):
        await self.http.aclose()

    def _embed(self, texts: List[str]) -> List[List[float]]:
        vecs = self.embedder.encode(texts, normalize_embeddings=True)
        if isinstance(vecs, np.ndarray):
            return vecs.astype(np.float32).tolist()
        return vecs  # type: ignore

    async def retrieve(self, query: str, top_k: int = 4) -> List[dict]:
        qv = self._embed([query])[0]
        res = self.index.query(vector=qv, top_k=top_k, include_metadata=True)
        matches = res["matches"] if isinstance(res, dict) else res.matches
        docs = []
        for m in matches:
            md = m["metadata"] if isinstance(m, dict) else m.metadata
            score = m["score"] if isinstance(m, dict) else m.score
            docs.append({"text": md.get("text", ""), "source": md.get("source", "unknown"), "score": score})
        return docs

    async def generate(self, prompt: str) -> str:
        url = f"{OLLAMA_BASE_URL}/api/generate"
        payload = {"model": MODEL_NAME, "prompt": prompt, "stream": False}
        try:
            r = await self.http.post(url, json=payload)
        except httpx.TransportError as te:
            raise RuntimeError("Cannot reach Ollama at OLLAMA_BASE_URL. Ensure Ollama is running and the model is pulled.") from te
        r.raise_for_status()
        data = r.json()
        return data.get("response", "")

    def _build_prompt(self, question: str, docs: List[dict]) -> str:
        context = "\n---\n".join([f"Source: {d['source']}\n{d['text']}" for d in docs])
        system = (
            "You are Jarvis, a concise enterprise assistant. Answer the user's question using the provided context. "
            "If the answer is not in the context, say you don't know. Cite sources as [source] at the end."
        )
        return f"{system}\n\nContext:\n{context}\n\nQuestion: {question}\nAnswer:"

    async def answer(self, question: str, top_k: int = 4) -> Tuple[str, List[dict]]:
        docs = await self.retrieve(question, top_k=top_k)
        prompt = self._build_prompt(question, docs)
        answer = await self.generate(prompt)
        sources = []
        seen = set()
        for d in docs:
            s = d["source"]
            if s not in seen:
                sources.append({"source": s, "score": d["score"]})
                seen.add(s)
        return answer.strip(), sources
