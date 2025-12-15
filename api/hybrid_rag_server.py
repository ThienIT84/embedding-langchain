#!/usr/bin/env python
"""
FastAPI server cho Hybrid RAG (Internal + Web Search).
Chạy trên port 8002 để tránh conflict với RAG server gốc (8001).

Usage:
    python api/hybrid_rag_server.py
"""

import sys
import logging
import os
import torch
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# --- 1. Setup Environment & Paths ---
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=PROJECT_ROOT / ".env")
except Exception as e:
    print(f"⚠️ Warning: Could not load .env file: {e}")

# --- 2. Local Imports ---
# Import các module core của bạn
try:
    from src.hybrid_retriever import hybrid_retriever
    from src.prompt_builder import build_rag_prompt
    from src.llm_client import generate_answer
except ImportError as e:
    print(f"❌ Error importing src modules: {e}")
    print("👉 Hãy chắc chắn bạn đang chạy từ root folder hoặc đã set PYTHONPATH.")
    sys.exit(1)

# --- 3. Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("HybridRAG")

# --- 4. Lifespan Manager (Thay thế on_event startup) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup Logic ---
    logger.info("🚀 Starting Hybrid RAG Server...")
    
    # Kiểm tra GPU
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        logger.info(f"✅ GPU Detected: {gpu_name}")
    else:
        logger.warning("⚠️ GPU not found. Running on CPU (Performance may be slow)")

    # Kiểm tra Tavily API Key
    if not os.getenv("TAVILY_API_KEY"):
        logger.warning("⚠️ TAVILY_API_KEY is missing. Web search might fail.")
    
    # Kiểm tra model
    if hybrid_retriever.tavily_retriever is None:
        logger.warning("⚠️ Tavily Retriever not initialized inside hybrid_retriever.")

    yield  # Server chạy tại điểm này

    # --- Shutdown Logic ---
    logger.info("🛑 Shutting down Hybrid RAG Server...")

# --- 5. App Definition ---
app = FastAPI(
    title="Hybrid RAG Service API", 
    version="1.0.0",
    lifespan=lifespan  # Gắn lifespan vào app
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],    
)

# --- 6. Pydantic Models ---
class HybridRetrieveRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Câu hỏi người dùng")
    user_id: str = Field(..., description="ID người dùng để lọc document cá nhân")
    top_k: int = Field(5, ge=1, le=20)
    include_web: bool = True
    web_max_results: int = 3
    internal_max_results: int = 5

class HybridQueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    user_id: str
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    top_k: int = 5
    include_web: bool = True
    web_max_results: int = 3
    internal_max_results: int = 5

# Thêm model tương thích với frontend (cho endpoint /api/rag/chat)
class RAGChatRequest(BaseModel):
    query: str = Field(..., min_length=1)
    topK: Optional[int] = Field(5, ge=1, le=20)
    mode: Optional[str] = "fast"  # fast hoặc deepthink
    includeWeb: Optional[bool] = False  # Bật web search
    documentId: Optional[str] = None  # ⭐ NEW: Nếu có = chỉ tìm trong document này

# --- 7. Endpoints ---

@app.get("/health")
async def health():
    """Kiểm tra trạng thái server."""
    return {
        "status": "healthy",
        "service": "Hybrid RAG Server",
        "gpu_available": torch.cuda.is_available(),
        "tavily_enabled": hybrid_retriever.tavily_retriever is not None
    }

@app.post("/hybrid/retrieve")
async def hybrid_retrieve(request: HybridRetrieveRequest):
    """
    ENDPOINT: /hybrid/retrieve
    Mục đích: Chỉ thực hiện bước tìm kiếm (Retrieve) từ Internal DB + Web.
    Dùng cho: 
      - Debug xem hệ thống tìm thấy gì
      - Frontend muốn tự gọi LLM và chỉ cần context
    """
    try:
        logger.info(f"🔍 Retrieving for: '{request.query}' (User: {request.user_id})")
        
        # GỌI LOGIC TÌM KIẾM TRUNG TÂM (HybridRetriever)
        result = hybrid_retriever.retrieve(
            query=request.query,
            user_id=request.user_id,
            top_k=request.top_k,
            include_web=request.include_web,
            web_max_results=request.web_max_results,
            internal_max_results=request.internal_max_results
        )
        
        # Format lại kết quả trả về
        sources = [{
            "content": chunk.content,
            "chunk_index": chunk.chunk_index,
            "page_number": chunk.page_number,
            "similarity": chunk.similarity,
            # Nếu chunk có field metadata (từ web hoặc internal)
            "metadata": chunk.metadata,
            "source_type": chunk.metadata.get('source', 'internal') if chunk.metadata else 'internal'
        } for chunk in result.sources]
        
        logger.info(f"✅ Found {len(sources)} sources.")

        return {
            "sources": sources,
            "context_preview": "\n\n".join([s["content"][:200] + "..." for s in sources]),
            "metadata": result.metadata
        }
    except Exception as e:
        logger.error(f"❌ Hybrid retrieval error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/hybrid/query")
async def hybrid_query(request: HybridQueryRequest):
    """
    Full Flow: Retrieve (Hybrid) -> Prompt -> LLM (Ollama/OpenAI) -> Answer.
    """
    try:
        logger.info(f"🧠 Processing Query: '{request.query}'")

        # 1. Retrieve Hybrid
        retrieval_result = hybrid_retriever.retrieve(
            query=request.query,
            user_id=request.user_id,
            top_k=request.top_k,
            include_web=request.include_web,
            web_max_results=request.web_max_results,
            internal_max_results=request.internal_max_results
        )
        
        # 2. Build Prompt
        prompt = build_rag_prompt(
            query=request.query,
            chunks=retrieval_result.sources,
            system_prompt=request.system_prompt
        )
        
        # 3. Call LLM
        model_name = request.model or os.getenv("OLLAMA_MODEL", "llama3")
        logger.info(f"🤖 Sending prompt to LLM ({model_name})...")
        
        llm_response = generate_answer(
            prompt=prompt,
            model=model_name
        )
        
        # 4. Format Response
        sources_list = [{
            "content": chunk.content,
            "similarity": chunk.similarity,
            "source": chunk.metadata.get("source", "internal") if chunk.metadata else "internal"
        } for chunk in retrieval_result.sources]

        logger.info("🎉 Query processed successfully.")

        return {
            "answer": llm_response.answer,
            "sources": sources_list,
            "metadata": {
                **retrieval_result.metadata,
                "model_used": llm_response.model,
                "generation_time": llm_response.total_duration,
            }
        }

    except Exception as e:
        logger.error(f"❌ Hybrid query error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/rag/chat")
async def rag_chat_compatible(request: RAGChatRequest, authorization: Optional[str] = Header(None)):
    """
    Endpoint tương thích với frontend hiện tại.
    Khi includeWeb=True, sẽ search cả web (Tavily) + internal documents.
    """
    try:
        # Lấy user_id từ JWT token (Supabase)
        import jwt
        import json
        
        # Extract token từ Authorization header
        user_id = None
        # startwith kiểm tra chuỗi có bắt đầu bằng chuỗi "Bearer"
        if authorization and authorization.startswith('Bearer '): 
            token = authorization.replace('Bearer ', '')
            try:
                # Decode JWT (không verify signature vì chỉ cần user_id)
                # Trong production nên verify với Supabase JWT secret
                decoded = jwt.decode(token, options={"verify_signature": False})
                user_id = decoded.get('sub')  # 'sub' chứa user_id trong Supabase JWT
                logger.info(f"✅ Extracted user_id from JWT: {user_id}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to decode JWT: {e}")
        
        # Fallback nếu không có token hoặc decode fail
        if not user_id:
            user_id = "00000000-0000-0000-0000-000000000000"  # Default test user
            logger.warning(f"⚠️ Using fallback user_id: {user_id}")
        
        logger.info(f"🔍 RAG Chat: '{request.query}' (includeWeb={request.includeWeb})")
        
        # Nếu includeWeb=True, dùng hybrid retrieval
        if request.includeWeb:
            logger.info("🌐 Web search ENABLED - Using Hybrid Retrieval")
            retrieval_result = hybrid_retriever.retrieve(
                query=request.query,
                user_id=user_id,
                document_id=request.documentId,  # ⭐ Pass document context (if any)
                top_k=request.topK or 8,
                include_web=True,
                web_max_results=3,
                internal_max_results=request.topK or 5
            )
        else:
            # Chỉ search internal
            logger.info("📚 Internal only - Using standard retrieval")
            from src.retriever import retrieve_similar_chunks_by_user, retrieve_similar_chunks_by_document
            from src.embedder import embed_text
            
            if request.documentId:
                # ⭐ Document-specific search
                logger.info(f"📄 Searching in specific document: {request.documentId}")
                internal_chunks = retrieve_similar_chunks_by_document(
                    query=request.query,
                    document_id=request.documentId,
                    top_k=request.topK or 5
                )
            else:
                # Global search
                internal_chunks = retrieve_similar_chunks_by_user(
                    query=request.query,
                    user_id=user_id,
                    top_k=request.topK or 5
                )
            
            # Convert to HybridRetrievalResult format
            from src.hybrid_retriever import HybridRetrievalResult, RetrievedChunk
            retrieval_result = HybridRetrievalResult(
                sources=internal_chunks,
                metadata={"internal_count": len(internal_chunks), "web_count": 0}
            )
        
        # Format sources cho frontend
        sources = []
        for chunk in retrieval_result.sources:
            source_dict = {
                "chunk_id": getattr(chunk, "chunk_id", None),
                "text": chunk.content,
                "content": chunk.content,
                "similarity": chunk.similarity,
                "chunk_index": chunk.chunk_index,
                "page_number": chunk.page_number,
            }
            
            # Thêm type cho web sources
            if hasattr(chunk, 'metadata') and chunk.metadata:
                if chunk.metadata.get('source') == 'web':
                    source_dict['type'] = 'web'
                    source_dict['url'] = chunk.metadata.get('url')
                    source_dict['title'] = chunk.metadata.get('title', 'Web Result')
                else:
                    source_dict['type'] = 'internal'
            else:
                source_dict['type'] = 'internal'
            
            sources.append(source_dict)
        
        logger.info(f"✅ Retrieved {len(sources)} sources (Web: {sum(1 for s in sources if s.get('type') == 'web')})")
        
        return {
            "answer": "",  # Frontend sẽ tự generate với LLM
            "sources": sources,
            "metadata": {
                **retrieval_result.metadata,
                "query_time_ms": retrieval_result.metadata.get("elapsed_ms", 0),
                "chunk_count": len(sources)
            }
        }
        
    except Exception as e:
        logger.error(f"❌ RAG chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Chạy trên port 8002
    print("Starting Uvicorn on port 8002...")
    uvicorn.run(
        "api.hybrid_rag_server:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )