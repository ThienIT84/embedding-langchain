from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterable, List

import numpy as np

from .config import settings
from .embedder import _get_model  # sử dụng lại model embedding
from .supabase_client import get_supabase_client

"""Truy vấn Supabase để lấy các đoạn văn bản liên quan nhất tới câu hỏi."""


@dataclass(slots=True)
class RetrievedChunk:
    """Đại diện cho một đoạn văn bản được truy xuất cùng điểm tương đồng."""

    content: str
    chunk_index: int
    page_number: int | None
    similarity: float


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Tính cosine similarity giữa hai vector."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def retrieve_similar_chunks(query: str, document_id: str, top_k: int = 5) -> List[RetrievedChunk]:
    """Lấy top_k đoạn văn bản gần nhất với truy vấn theo cosine similarity."""
    if not query.strip():
        raise ValueError("Query không được để trống")
    if not document_id.strip():
        raise ValueError("document_id không được để trống")

    client = get_supabase_client()
    response = (
        client.table("document_embeddings")
        .select("content, chunk_index, page_number, embedding")
        .eq("document_id", document_id)
        .execute()
    )

    rows = response.data or []
    if not rows:
        return []

    model = _get_model()
    query_vector = model.encode([query])[0]
    query_vector = np.asarray(query_vector, dtype=np.float32)

    scored: list[RetrievedChunk] = []
    for row in rows:
        embedding_data = row.get("embedding")
        if embedding_data is None:
            continue

        if isinstance(embedding_data, str):
            try:
                embedding_data = json.loads(embedding_data)
            except json.JSONDecodeError:
                continue

        if not isinstance(embedding_data, Iterable):
            continue

        embedding = np.asarray(list(embedding_data), dtype=np.float32)
        if embedding.size == 0:
            continue
        score = _cosine_similarity(query_vector, embedding)
        scored.append(
            RetrievedChunk(
                content=row["content"],
                chunk_index=row.get("chunk_index", 0) or 0,
                page_number=row.get("page_number"),
                similarity=score,
            )
        )

    scored.sort(key=lambda item: item.similarity, reverse=True)
    return scored[: max(top_k, 1)]
