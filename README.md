# RAG System - Python Core (Phase A + Phase B Integration)

A complete **Retrieval-Augmented Generation (RAG)** system built with Python, integrating document embedding, semantic search, and LLM inference via local Ollama.

**Key Features:**
- ✅ **End-to-end RAG pipeline**: Extract → Chunk → Embed → Retrieve → Generate
- ✅ **Offline & Local**: No external API calls, runs on your machine
- ✅ **Multilingual**: Supports 50+ languages including Vietnamese via sentence-transformers
- ✅ **Vector Database**: Supabase pgvector with IVFFlat indexing for fast similarity search
- ✅ **LLM Integration**: Local inference via Ollama (llama3)
- ✅ **Single-Port Backend**: Express.js backend spawns Python processes on-demand
- ✅ **React Frontend**: Simple demo UI for Q&A

---

## 📦 Architecture

```
Embedding_langchain/
├── src/
│   ├── config.py              # Environment configuration
│   ├── supabase_client.py     # DB operations
│   ├── text_extractor.py      # PDF/Text extraction
│   ├── chunker.py             # Text chunking
│   ├── embedder.py            # Vector generation (sentence-transformers)
│   ├── pipeline.py            # Orchestration (extract → chunk → embed → store)
│   ├── retriever.py           # Semantic search (cosine similarity)
│   ├── prompt_builder.py      # LLM prompt construction
│   ├── llm_client.py          # Ollama API calls
│   └── rag_service.py         # RAG workflow (retrieve → build → generate)
├── scripts/
│   ├── ingest_document.py     # CLI: Ingest PDF → embedding → DB
│   ├── rag_query.py           # CLI: Test RAG queries
│   └── rag_runner.py          # Wrapper for Node.js backend
├── .env.example               # Environment template
├── requirements.txt           # Python dependencies
└── README.md                  # This file

# Documentation
├── PHASE_A_EXPLAINED.md       # Phase A: Python RAG core (detailed)
├── PHASE_B_EXPLAINED.md       # Phase B: Backend integration (detailed)
├── RAG_METHODOLOGY_EXPLAINED.md
└── [12+ additional docs]
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Ollama installed locally (https://ollama.ai)
- Supabase account with pgvector extension
- Node.js (if using Phase B backend)

### 1. Setup Environment

```bash
# Clone repo
cd Embedding_langchain

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Downgrade NumPy for Torch/TensorFlow compatibility
pip install "numpy<2.0.0" --force-reinstall
```

### 2. Configure .env

Copy `.env.example` to `.env`:
```env
SUPABASE_URL="https://your-project.supabase.co"
SUPABASE_SERVICE_KEY="your-service-key"
OLLAMA_URL="http://localhost:11434"
OLLAMA_MODEL="llama3"
CHUNK_SIZE=900
CHUNK_OVERLAP=200
```

### 3. Setup Supabase (One-time)

Create pgvector extension and tables:
```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT,
  filename TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS document_embeddings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
  chunk_index INTEGER,
  chunk_text TEXT,
  embedding vector(768),
  similarity_score FLOAT DEFAULT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create IVFFlat index for fast similarity search
CREATE INDEX ON document_embeddings 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);
```

### 4. Start Ollama

```bash
# Ensure Ollama is running (downloads model on first run)
ollama serve
# In another terminal, pull llama3
ollama pull llama3
```

---

## 📋 Usage

### Phase A: Ingest Documents

Ingest a PDF and create embeddings:
```bash
python scripts/ingest_document.py "path/to/file.pdf" "Document Title"
```

**Output:**
- Extracts text from PDF
- Chunks text (~900 chars, 200-char overlap)
- Generates 768-dim vectors via sentence-transformers
- Stores in Supabase pgvector

### Phase A: Query with RAG

```bash
python scripts/rag_query.py \
  --query "What are the advantages of KNN?" \
  --document-id "01287d1b-ca04-..." \
  --top-k 5 \
  --pretty
```

**Output:**
```json
{
  "answer": "According to the document, KNN advantages include...",
  "sources": [
    {
      "text": "KNN is a simple algorithm...",
      "similarity": 0.92
    }
  ],
  "metadata": {"elapsed_ms": 1234, "model": "llama3"}
}
```

---

## 🔄 Phase B: Backend Integration (Single Port)

### Start Backend (Node.js Express)

```bash
cd ../mindmapnote2/backend
npm install
npm run dev  # Runs on http://localhost:3000
```

### Start Frontend (React)

```bash
cd ../mindmap-notion-interface
npm install
npm run dev  # Runs on http://localhost:5173
```

### Test RAG Endpoint

1. Login at `http://localhost:5173/auth` (get JWT token)
2. Visit `http://localhost:5173/rag-demo`
3. Enter:
   - Document ID
   - Query (e.g., "Explain KNN advantages")
   - Top K (default 5)
4. Click "Ask" → See answer + sources

**How it works:**
```
Frontend (React) 
  → POST /api/rag/chat (with Bearer token)
  → Backend (Express) spawns Python process
  → Python rag_runner.py calls Phase A
  → Returns JSON (answer + sources)
  → Frontend displays result
```

---

## 🧠 How RAG Works

### Retrieval
1. Embed user query using sentence-transformers
2. Find top-k chunks with highest cosine similarity in vector DB
3. Return chunks + similarity scores

### Generation
1. Build prompt: system instruction + context chunks + user query
2. Call Ollama llama3 with prompt
3. Return LLM-generated answer

### Why it works
- **Semantic search** finds relevant context from documents
- **LLM** generates natural answers based on context
- **No hallucination** because answer is grounded in retrieved chunks

---

## 📚 Documentation

For detailed explanations, see:
- `PHASE_A_EXPLAINED.md` - Architecture, components, data flow
- `PHASE_B_EXPLAINED.md` - Backend integration, HTTP flow
- `RAG_METHODOLOGY_EXPLAINED.md` - RAG theory & methodology
- `[12+ additional markdown files]` - Deep dives on specific components

---

## 🛠️ Development

### Project Structure

**Phase A (Core RAG)**
- `src/` - RAG modules (retriever, prompt builder, LLM client)
- `scripts/ingest_document.py` - CLI for embedding ingestion
- `scripts/rag_query.py` - CLI for RAG queries

**Phase B (Backend Integration)**
- `scripts/rag_runner.py` - Wrapper for Node.js spawning
- `../mindmapnote2/backend/src/controllers/ragController.js` - Spawn logic
- `../mindmap-notion-interface/src/services/ragService.ts` - Frontend API client

### Adding a New Feature

1. **Add function to appropriate `src/*.py` module**
2. **Update `rag_service.py` to use it**
3. **Test via CLI**: `python scripts/rag_query.py --query "..."`
4. **Backend will automatically pick it up** (no redeploy needed)

---

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `SUPABASE_URL` | - | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | - | Service role key (admin) |
| `OLLAMA_URL` | http://localhost:11434 | Ollama endpoint |
| `OLLAMA_MODEL` | llama3 | LLM model name |
| `CHUNK_SIZE` | 900 | Characters per chunk |
| `CHUNK_OVERLAP` | 200 | Overlap between chunks |
| `HF_MODEL_NAME` | sentence-transformers/paraphrase-multilingual-mpnet-base-v2 | Embedding model |

### Backend Environment (Phase B)

Set in `mindmapnote2/backend/.env`:
```env
RAG_PYTHON_PATH=C:\Code\DACN_MindMapNote\Embedding_langchain\venv\Scripts\python.exe
RAG_TIMEOUT_MS=180000  # 3 minutes
```

---

## 📊 Performance

| Operation | Time | Notes |
|-----------|------|-------|
| Ingest 50-page PDF | ~2-3 min | First run downloads 500MB model |
| Embed query + retrieve top-5 | ~500ms | Cosine similarity search |
| LLM inference (answer) | 5-30s | Depends on Ollama performance |
| Total RAG call | ~6-35s | First call slower (model loading) |

---

## � Security

- ✅ **Offline**: No external API calls (Supabase is cloud, but data stays yours)
- ✅ **Auth**: Backend checks Bearer token before spawning RAG
- ✅ **No secrets in code**: All sensitive data in `.env`
- ✅ **Service Key only**: Backend uses Supabase service role (admin key)

---

## 🐛 Troubleshooting

### NumPy Compatibility Error
```
Failed to initialize NumPy: _ARRAY_API not found
```
**Solution**: `pip install "numpy<2.0.0" --force-reinstall`

### Encoding Error (Vietnamese characters)
```
'charmap' codec can't encode character '\u1ed5'
```
**Solution**: Backend automatically sets `PYTHONIOENCODING=utf-8`

### Timeout Error
```
Process closed with code: null
```
**Solution**: Increase `RAG_TIMEOUT_MS` in backend `.env` (default 180000ms)

### Ollama Not Found
```
Connection refused: http://localhost:11434
```
**Solution**: Ensure Ollama is running (`ollama serve`)

---

## 📈 Next Steps

1. **Optimize chunking** - Experiment with chunk_size/overlap
2. **Fine-tune prompts** - Customize system instruction in `prompt_builder.py`
3. **Add more LLMs** - Support GPT, Claude via `llm_client.py`
4. **Caching** - Cache embeddings for repeated queries
5. **Frontend improvements** - Better UI, streaming responses
6. **Multi-document search** - Search across all documents

---

## 📝 License

[Your license here]

---

## 👤 Author

Built for learning RAG systems with Python, Supabase, and local LLMs.

---

**Questions?** See documentation files or check code comments.

**Happy RAG-ing! 🚀**

