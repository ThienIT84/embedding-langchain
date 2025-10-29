from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.rag_service import rag_query

router = APIRouter(prefix="/api/rag", tags=["rag"])


class RAGRequest(BaseModel):
    query: str = Field(..., description="Câu hỏi của người dùng")
    document_id: str = Field(..., description="UUID tài liệu trong Supabase")
    top_k: int = Field(5, ge=1, le=20, description="Số đoạn context lấy ra")
    system_prompt: Optional[str] = Field(None, description="Ghi đè system prompt (tùy chọn)")


class SourceItem(BaseModel):
    content: str
    chunk_index: int
    page_number: Optional[int] = None
    similarity: float


class Metadata(BaseModel):
    model: str
    query_time_ms: float
    chunk_count: int


class RAGResponse(BaseModel):
    answer: str
    sources: List[SourceItem]
    metadata: Metadata


@router.post("/chat", response_model=RAGResponse)
async def chat_with_rag(payload: RAGRequest) -> Dict[str, Any]:
    if not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query không được để trống")
    if not payload.document_id.strip():
        raise HTTPException(status_code=400, detail="document_id không được để trống")

    try:
        result = rag_query(
            query=payload.query,
            document_id=payload.document_id,
            top_k=payload.top_k,
            system_prompt=payload.system_prompt,
        )
        # result đã đúng schema theo rag_service, FastAPI sẽ validate theo RAGResponse
        return {
            "answer": result["answer"],
            "sources": result.get("sources", []),
            "metadata": result.get("metadata", {}),
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        # Không để lộ traceback nội bộ
        raise HTTPException(status_code=500, detail=f"RAG lỗi xử lý: {exc}") from exc
