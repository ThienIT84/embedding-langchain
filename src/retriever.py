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


def retrieve_similar_chunks_by_user(query: str, user_id: str, top_k: int = 5) -> List[RetrievedChunk]:
    """
    Lấy top_k đoạn văn bản gần nhất với truy vấn từ TẤT CẢ documents của user.
    
    Thay vì search trong 1 document cụ thể, function này:
    1. Encode câu hỏi thành vector embedding (768 chiều)
    2. Gọi RPC function 'match_embeddings_by_user' trong Supabase
    3. RPC function sẽ tìm các chunks tương đồng nhất trong TẤT CẢ documents của user
    4. Trả về danh sách chunks đã được sort theo similarity (cao → thấp)
    
    Args:
        query: Câu hỏi của người dùng (VD: "Khái niệm OOP là gì?")
        user_id: UUID của user (lấy từ JWT token)
        top_k: Số lượng chunks muốn lấy (mặc định 5)
    
    Returns:
        List[RetrievedChunk]: Danh sách chunks có similarity cao nhất
    """
    # Kiểm tra input không được rỗng
    if not query.strip():
        raise ValueError("Query không được để trống")
    if not user_id.strip():
        raise ValueError("user_id không được để trống")

    # Bước 1: Encode câu hỏi thành vector embedding
    # Sử dụng sentence-transformers model (paraphrase-multilingual-mpnet-base-v2)
    # Output: vector 768 chiều
    model = _get_model()
    query_vector = model.encode([query])[0]  # Encode 1 câu → lấy vector đầu tiên
    query_vector = np.asarray(query_vector, dtype=np.float32)  # Chuyển sang float32
    
    # Bước 2: Chuyển numpy array thành Python list để gửi qua RPC
    # Supabase RPC cần list, không nhận numpy array
    query_embedding_list = query_vector.tolist()
    
    # Bước 3: Gọi RPC function trong Supabase
    # RPC function sẽ:
    # - JOIN bảng document_embeddings với documents
    # - Filter theo created_by = user_id
    # - Tính cosine similarity bằng pgvector (1 - cosine distance)
    # - Sort theo similarity giảm dần
    # - Limit top_k kết quả
    client = get_supabase_client()
    response = client.rpc(
        'match_embeddings_by_user',
        {
            'query_embedding': query_embedding_list,  # Vector 768 chiều dạng list
            'user_id_filter': user_id,                # UUID của user
            'match_count': max(top_k, 1)              # Số lượng kết quả (tối thiểu 1)
        }
    ).execute()
    
    # Bước 4: Parse kết quả từ RPC
    rows = response.data or []
    if not rows:
        # Không tìm thấy documents nào của user hoặc không có chunk tương đồng
        return []
    
    # Bước 5: Chuyển đổi kết quả thành RetrievedChunk objects
    # RPC đã tính similarity và sort rồi, chỉ cần parse data
    chunks: list[RetrievedChunk] = []
    for row in rows:
        chunks.append(
            RetrievedChunk(
                content=row.get("content", ""),           # Nội dung chunk
                chunk_index=row.get("chunk_index", 0) or 0,  # Thứ tự chunk trong document
                page_number=row.get("page_number"),       # Số trang (có thể None)
                similarity=row.get("similarity", 0.0) or 0.0,  # Điểm tương đồng (0-1)
            )
        )
    
    return chunks
