from __future__ import annotations

from time import perf_counter
from typing import Any, Dict

from .llm_client import LLMResponse, generate_answer
from .prompt_builder import build_rag_prompt
from .retriever import RetrievedChunk, retrieve_similar_chunks

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
    document_id: str,
    top_k: int = 5,
    system_prompt: str | None = None,
) -> Dict[str, Any]:
    """Thực hiện đầy đủ vòng RAG và trả về answer, sources, metadata."""
    start = perf_counter()

    retrieved_chunks = retrieve_similar_chunks(query=query, document_id=document_id, top_k=top_k)
    prompt = build_rag_prompt(query=query, chunks=retrieved_chunks, system_prompt=system_prompt)
    llm_response: LLMResponse = generate_answer(prompt=prompt)

    elapsed_ms = (perf_counter() - start) * 1000

    return {
        "answer": llm_response.answer,
        "sources": [_serialize_chunk(chunk) for chunk in retrieved_chunks],
        "metadata": {
            "model": llm_response.model,
            "query_time_ms": round(elapsed_ms, 2),
            "chunk_count": len(retrieved_chunks),
        },
        "prompt": prompt,
        "raw_llm_response": llm_response.raw,
    }
