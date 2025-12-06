# RAG System - Document Embedding & Semantic Search

Hệ thống RAG (Retrieval-Augmented Generation) với document embedding, vector search và LLM generation.

## ✨ Tính năng

- 📄 Process PDF/text documents → chunking → embedding → vector storage
- 🔍 Semantic search với cosine similarity
- 🤖 LLM generation qua Ollama (local) hoặc Gemini (cloud)
- 🚀 FastAPI server với RAG endpoints
- 🔐 User-scoped search (JWT authentication)
- 🌏 Multilingual support (Vietnamese, English, 50+ languages)

## 🚀 Quick Start

### 1. Install
```bash
pip install -r requirements.txt
```

### 2. Config
```bash
cp .env.example .env
# Sửa SUPABASE_URL, SUPABASE_SERVICE_KEY
```

### 3. Run
```bash
python scripts/start_rag_server.py
```

Server: http://localhost:8001  
Docs: http://localhost:8001/docs

## 📁 Cấu trúc

```
Embedding_langchain/
├── api/                   # FastAPI application
├── src/                   # Core modules
│   ├── embedder.py       # Text → vectors
│   ├── retriever.py      # Semantic search
│   ├── llm_client.py     # Ollama LLM
│   ├── rag_service.py    # Main RAG workflow
│   └── pipeline.py       # Document processing
├── scripts/              # CLI tools
├── tests/                # Unit tests
└── docs/                 # Documentation
```

## 🔌 API Endpoints

### Query RAG (Full)
```bash
POST /api/rag/query
{
  "query": "Câu hỏi?",
  "user_id": "uuid",
  "top_k": 5
}

Response:
{
  "answer": "...",
  "sources": [...],
  "metadata": {...}
}
```

### Retrieve Only (Fast)
```bash
POST /api/rag/retrieve
{
  "query": "Câu hỏi?",
  "user_id": "uuid",
  "top_k": 5
}

Response:
{
  "sources": [...]
}
```

## 🛠️ Scripts

### Process document
```bash
python scripts/ingest_document.py --document-id <uuid>
```

### Run server
```bash
# Production
python scripts/start_rag_server.py

# Development
python scripts/start_rag_server.py --reload
```

## 📊 Performance

| Operation | Time |
|-----------|------|
| Retrieve chunks | ~0.5-2s |
| LLM (Ollama) | ~5-30s |
| LLM (Gemini) | ~2-8s |
| Total RAG | ~6-35s |

## 🧪 Testing

```bash
pytest                      # Run tests
pytest --cov=src           # With coverage
```

## 📖 Docs

- [Code Reading Guide](docs/CODE_READING_GUIDE.md)
- [RAG Server Guide](RAG_SERVER_GUIDE.md)
- [Phase A Explained](docs/PHASE_A_EXPLAINED.md)
- [Testing Guide](docs/TESTING_GUIDE.md)

## 🔧 Config

Key environment variables:

```bash
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=xxx
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3
CHUNK_SIZE=900
CHUNK_OVERLAP=200
```

## 🐛 Troubleshooting

**NumPy error:**
```bash
pip install "numpy<2.0.0" --force-reinstall
```

**Ollama not running:**
```bash
ollama serve
ollama pull llama3
```

## 📝 Notes

- Embedding model auto-downloads (~500MB) lần đầu
- Ollama phải chạy local cho LLM generation
- Supabase cần pgvector extension
