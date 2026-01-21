# Jarvis: Self-hosted RAG Assistant

- Backend: FastAPI, sentence-transformers embeddings, Pinecone vector DB.
- LLM: Ollama local server (default model `llama3.1:8b`).
- Frontend: React + Vite + Tailwind chat UI.

## Prerequisites
- Python 3.10+
- Node.js 18+
- Ollama installed and running: https://ollama.com
  - Pull a model, e.g.: `ollama pull llama3.1:8b`
- Pinecone account and API key.

## Setup
1. Copy `.env.example` to `.env` and fill your values.
2. Backend
   ```bash
   python -m venv .venv
   .venv/Scripts/activate  # Windows PowerShell
   pip install -r backend/requirements.txt
   uvicorn backend.app:app --reload --port 8000
   ```
3. Frontend (new terminal)
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Ingest knowledge
Place `.txt` or `.md` files into `knowledge/`, then run:
```bash
.venv/Scripts/activate
python -m backend.ingest
```

## Use
Open the frontend (default http://localhost:5173). Ask questions; the backend retrieves top matches from Pinecone and generates an answer via Ollama.

## Config
- Edit `.env` to change Pinecone settings, model name, or embedding dimensions.
- The embedder is `all-MiniLM-L6-v2` (384 dims); ensure your Pinecone index dimension matches `EMBED_DIM`.
