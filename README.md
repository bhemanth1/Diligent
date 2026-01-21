# Jarvis: Self‑hosted RAG Assistant

- Backend: FastAPI + Sentence-Transformers embeddings + Pinecone vector DB
- LLM: Local via Ollama (default model `llama3.1:8b`)
- Frontend: React + Vite + Tailwind chat UI

This README is tailored for Windows PowerShell.

## 1) Prerequisites
- Node.js 18+
- Python 3.12 (we run the backend in a 3.12 virtual env for best wheels compatibility)
- Pinecone account + API key
- Ollama for Windows
  - Install with one of:
    - winget: `winget install Ollama.Ollama`
    - or download installer: https://ollama.com/download/windows

## 2) Configure environment (.env)
From the `jarvis` folder:
- Copy `.env.example` to `.env`
- Set values (example):
```
PINECONE_API_KEY=YOUR_PINECONE_KEY
PINECONE_INDEX=jarvis-knowledge
PINECONE_ENV=us-east-1-aws
OLLAMA_BASE_URL=http://localhost:11434
MODEL_NAME=llama3.1:8b
EMBED_DIM=384
```
Notes:
- `EMBED_DIM` must match the embedding model (we use `all-MiniLM-L6-v2` → 384 dims).
- Keep `.env` out of source control.

## 3) Backend (Python 3.12 virtual env)
Run these in PowerShell from the `jarvis` folder:
```
py -3.12 -m venv .venv312
.\.venv312\Scripts\Activate
python -V            # should show Python 3.12.x
python -m pip install -U pip
python -m pip install -r backend\requirements.txt
```
Start the API (from `jarvis` root):
```
python -m uvicorn backend.app:app --reload --port 8000
```
Health check: http://127.0.0.1:8000/api/health → `{ "status": "ok" }`

## 4) Ollama model
Ensure Ollama service is running (reopen PowerShell after install so PATH is updated), then:
```
ollama pull llama3.1:8b
# optional quick test
ollama run llama3.1:8b
```
Verify the API is reachable:
```
Invoke-WebRequest http://localhost:11434/api/tags | Select-Object -ExpandProperty Content
```

## 5) Frontend
Open a new terminal:
```
cd frontend
npm install
npm run dev
```
Open http://localhost:5173

## 6) Ingest knowledge (optional but recommended)
Place `.txt` or `.md` files into `knowledge/`. Then (from `jarvis` root, with venv active):
```
python -m jarvis.backend.ingest
```
This creates/updates the Pinecone index with 384‑dim vectors.

## 7) Using the app
- Ask a question in the UI. The backend retrieves top documents from Pinecone and generates an answer via Ollama, returning citations.

## 8) API quick test
```
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/chat -ContentType 'application/json' -Body (@{message='hello'; top_k=2} | ConvertTo-Json)
```

## 9) Troubleshooting
- 500 on `/api/chat` with message about Ollama:
  - Make sure Ollama is installed and running; pull the model (`ollama pull llama3.1:8b`).
  - Check `OLLAMA_BASE_URL` in `.env` (default `http://localhost:11434`).
- `ModuleNotFoundError` for Python deps:
  - Ensure you activated the 3.12 venv (`.venv312`) before installing/running.
- Pinecone errors or empty answers:
  - Verify `PINECONE_API_KEY` and `PINECONE_ENV` in `.env`.
  - Make sure your index dimension matches `EMBED_DIM` (384). The backend will auto-create the index on first run.
- Frontend builds but can’t reach backend:
  - Backend must be running at `http://127.0.0.1:8000`. Set `VITE_API_BASE` in a `frontend/.env` if you changed ports.

## 10) Useful commands
```
# Activate venv (3.12)
.\.venv312\Scripts\Activate

# Start backend (from jarvis root)
python -m uvicorn backend.app:app --reload --port 8000

# Start frontend (from jarvis/frontend)
npm run dev

# Ingest documents (from jarvis root)
python -m jarvis.backend.ingest
```

  
# Screen Shots
<img width="1919" height="1011" alt="image" src="https://github.com/user-attachments/assets/6916eb09-389a-4814-b779-a0aa4f5abdb7" />
<img width="1919" height="1017" alt="image" src="https://github.com/user-attachments/assets/e1bd64db-fdd7-4ba6-83eb-b1216040bee5" />
<img width="1919" height="1015" alt="image" src="https://github.com/user-attachments/assets/69abd817-5ec0-400e-8cb5-5eb5963bf304" />

--
By:
- Bandi Hemanth
- 22WU0106028
- hemanth.bandi_2026@woxsen.edu.in
- BIC - SECTION
- WOXSEN UNIVERSITY



