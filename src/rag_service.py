from __future__ import annotations

from time import perf_counter
from typing import Any, Dict
from pydantic import ValidationError

from .llm_client import LLMResponse, generate_answer
from .prompt_builder import build_rag_prompt
from .retriever import RetrievedChunk, retrieve_similar_chunks, retrieve_similar_chunks_by_user
from .validators import RAGQueryRequest

"""Orchestrator kết hợp retrieval + prompt + LLM để tạo câu trả lời cuối."""


def _serialize_chunk(chunk: RetrievedChunk) -> Dict[str, Any]:
    """Chuyển RetrievedChunk thành dict đơn giản để trả về cho client."""
    return {
        "content": chunk.content,
        "chunk_index": chunk.chunk_index,
        "page_number": chunk.page_number,
        "similarity": chunk.similarity,
    }


def rag_query(
    query: str,
    user_id: str,  # ĐÃ ĐỔI: Từ document_id → user_id để search toàn bộ documents của user
    top_k: int = 5,
    system_prompt: str | None = None,
) -> Dict[str, Any]:
    """
    Thực hiện đầy đủ vòng RAG và trả về answer, sources, metadata.
    
    PHASE C1: Search trong TẤT CẢ documents của user, không cần chọn document cụ thể.
    
    Quy trình:
    1. Retrieval: Tìm top_k chunks tương đồng nhất từ TẤT CẢ documents của user
       (Gọi retrieve_similar_chunks_by_user → RPC function match_embeddings_by_user)
    2. Prompt Building: Ghép query + context chunks thành prompt cho LLM
    3. LLM Generation: Gửi prompt tới Ollama llama3 để sinh câu trả lời
    4. Response: Trả về answer + sources (chunks) + metadata (thời gian, model...)
    
    Args:
        query: Câu hỏi của người dùng
        user_id: UUID của user (lấy từ JWT token backend)
        top_k: Số lượng chunks sử dụng làm context (mặc định 5)
        system_prompt: Custom system prompt (optional, có default trong prompt_builder)
    
    Returns:
        Dict chứa:
        - answer: Câu trả lời từ LLM
        - sources: Danh sách chunks được sử dụng làm context (có similarity score)
        - metadata: Model name, thời gian xử lý, số lượng chunks
        - prompt: Full prompt đã gửi cho LLM (để debug)
        - raw_llm_response: Raw response từ LLM (để debug)
    
    Raises:
        ValueError: Nếu input validation thất bại
    """
    # Validate input với Pydantic
    try:
        validated = RAGQueryRequest(
            query=query,
            user_id=user_id,
            top_k=top_k,
            system_prompt=system_prompt
        )
    except ValidationError as e:
        raise ValueError(f"Invalid input parameters: {e}") from e
    
    # Đo thời gian xử lý toàn bộ pipeline
    start = perf_counter()

    # Bước 1: RETRIEVAL - Tìm chunks tương đồng từ TẤT CẢ documents của user
    # Sử dụng validated data
    retrieved_chunks = retrieve_similar_chunks_by_user(
        query=validated.query,
        user_id=validated.user_id,
        top_k=validated.top_k
    )
    
    # Bước 2: PROMPT BUILDING - Ghép query + chunks thành prompt
    prompt = build_rag_prompt(
        query=validated.query,
        chunks=retrieved_chunks,
        system_prompt=validated.system_prompt
    )
    
    # Bước 3: LLM GENERATION - Gửi prompt tới Ollama để sinh câu trả lời
    # Model: llama3 (local), temperature=0.7, max_tokens=1000
    llm_response: LLMResponse = generate_answer(prompt=prompt)

    # Tính tổng thời gian xử lý (ms)
    elapsed_ms = (perf_counter() - start) * 1000

    # Bước 4: RESPONSE - Trả về kết quả đầy đủ
    return {
        "answer": llm_response.answer,  # Câu trả lời từ LLM
        "sources": [_serialize_chunk(chunk) for chunk in retrieved_chunks],  # Chunks context
        "metadata": {
            "model": llm_response.model,           # Tên model (llama3)
            "query_time_ms": round(elapsed_ms, 2), # Thời gian xử lý (ms)
            "chunk_count": len(retrieved_chunks),  # Số chunks đã dùng
        },
        "prompt": prompt,                     # Full prompt (để debug)
        "raw_llm_response": llm_response.raw, # Raw response từ LLM (để debug)
    }
