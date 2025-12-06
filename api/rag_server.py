#!/usr/bin/env python
"""
FastAPI server cho RAG - Persistent service thay vì spawn process.

Lợi ích:
- Model chỉ load 1 lần khi khởi động (3-5s) → Tái sử dụng cho mọi request
- Không có overhead của spawn process
- Có thể scale với uvicorn workers
- Response nhanh hơn 3-4 lần (1-2s thay vì 5-6s)

Chạy server:
    python api/rag_server.py
    # Hoặc với uvicorn trực tiếp:
    uvicorn api.rag_server:app --host 0.0.0.0 --port 8001 --reload

API Endpoint:
    POST /rag/query
    Body: {
        "query": "câu hỏi",
        "user_id": "uuid-of-user",
        "top_k": 5,
        "system_prompt": "optional custom prompt"
    }
    Response: {
        "answer": "...",
        "sources": [...],
        "metadata": {...}
    }
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import logging
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=PROJECT_ROOT / ".env")
except Exception:
    pass

from src.rag_service import rag_query
from src.embedder import _get_model
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="RAG Service API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],    
)
class RAGRequest(BaseModel):
    query: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1)
    top_k: Optional[int] = Field(5, ge=1, le=20)
    system_prompt: Optional[str] = None
    model: Optional[str] = Field(None, description="Ollama model to use (e.g., 'llama3', 'qwen2.5:7b', 'gemma2:9b')")

    @validator('query')
    def query_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Query không được rỗng')
        return v.strip()

    @validator('user_id')
    def user_id_not_empty(cls, v):
        if not v.strip():
            raise ValueError('User ID không được rỗng')
        return v.strip()


class RAGResponse(BaseModel):
    answer: str
    sources: list
    metadata: dict
    prompt: Optional[str] = None
    raw_llm_response: Optional[dict] = None


@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting RAG Server...")
    logger.info("📦 Pre-loading embedding model...")
    try:
        model = _get_model()
        logger.info(f"✅ Model loaded: {model}")
        logger.info("🎉 RAG Server ready!")
    except Exception as e:
        logger.error(f"❌ Failed to load model: {e}")
        raise


@app.get("/")
async def root():
    return {"status": "healthy", "service": "RAG Server"}


@app.get("/health")
async def health():
    try:
        model = _get_model()
        return {
            "status": "healthy",
            "model_loaded": model is not None
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@app.post("/rag/query", response_model=RAGResponse)
async def query_rag(request: RAGRequest):
    """Full RAG với LLM (~60s)."""
    try:
        result = rag_query(
            query=request.query,
            user_id=request.user_id,
            top_k=request.top_k,
            system_prompt=request.system_prompt,
            model=request.model
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Server error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rag/retrieve")
async def retrieve_chunks(request: RAGRequest):
    """Chỉ retrieve chunks (~1-2s). Frontend tự gọi Gemini."""
    try:
        from src.retriever import retrieve_similar_chunks_by_user
        
        chunks = retrieve_similar_chunks_by_user(
            query=request.query,
            user_id=request.user_id,
            top_k=request.top_k
        )
        
        sources = [{
            "content": chunk.content,
            "chunk_index": chunk.chunk_index,
            "page_number": chunk.page_number,
            "similarity": chunk.similarity,
        } for chunk in chunks]
        
        return {
            "sources": sources,
            "metadata": {"chunk_count": len(sources)}
        }
    except Exception as e:
        logger.error(f"❌ Retrieval error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.rag_server:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
