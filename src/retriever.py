from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Iterable, List, Dict, Any, Optional

import numpy as np

from .config import settings
from .embedder import _get_model  # sử dụng lại model embedding
from .supabase_client import get_supabase_client

"""Truy vấn Supabase để lấy các đoạn văn bản liên quan nhất tới câu hỏi."""


@dataclass
class RetrievedChunk:
    """Đại diện cho một đoạn văn bản được truy xuất cùng điểm tương đồng."""

    content: str
    chunk_index: int
    page_number: int | None
    similarity: float
    metadata: Dict[str, Any] = field(default_factory=dict)  # Thêm metadata field


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


def retrieve_similar_chunks_by_document(
    query: str, 
    document_id: str, 
    top_k: int = 5
) -> List[RetrievedChunk]:
    """
    Tìm chunks CHỈ trong 1 document cụ thể (Metadata Filtering).
    
    Use case: User đang chat về 1 file cụ thể
    VD: User đang xem file "SoK_Explainable_ML.pdf" và hỏi:
        "Bài báo này có đề cập RAG không?"
    
    Điều này đảm bảo hệ thống:
    - ✅ CHỈ tìm trong file này
    - ✅ KHÔNG lấy thông tin từ file khác (PROJECT_OVERVIEW.md, etc.)
    - ✅ Tránh lẫn lộn knowledge
    
    Args:
        query: Câu hỏi ("Bài báo này nói về gì?")
        document_id: UUID của document cụ thể
        top_k: Số chunks cần lấy (mặc định 5)
        
    Returns:
        List[RetrievedChunk] chỉ từ document này
    """
    if not query.strip():
        raise ValueError("Query không được để trống")
    if not document_id.strip():
        raise ValueError("document_id không được để trống")

    # Encode câu hỏi thành vector
    model = _get_model()
    query_vector = model.encode([query])[0]
    query_vector = np.asarray(query_vector, dtype=np.float32)
    query_embedding_list = query_vector.tolist()
    
    # Gọi RPC function với document filter
    client = get_supabase_client()
    response = client.rpc(
        'match_embeddings_by_document',  # ⭐ Function mới có metadata filtering
        {
            'query_embedding': query_embedding_list,
            'document_id_filter': document_id,  # ⭐ CHỈ tìm trong document này
            'match_count': max(top_k, 1)
        }
    ).execute()
    
    # Parse kết quả
    rows = response.data or []
    if not rows:
        return []
    
    chunks: list[RetrievedChunk] = []
    for row in rows:
        chunks.append(
            RetrievedChunk(
                content=row.get("content", ""),
                chunk_index=row.get("chunk_index", 0) or 0,
                page_number=row.get("page_number"),
                similarity=row.get("similarity", 0.0) or 0.0,
                metadata={
                    "document_id": row.get("document_id"),
                    "document_title": row.get("document_title"),
                    "source": "internal"
                }
            )
        )
    
    return chunks


def hybrid_retrieve(
    query: str,
    user_id: str,
    top_k: int = 5,
    alpha: float = 0.5
) -> List[RetrievedChunk]:
    """
    ⚡ HYBRID SEARCH: Kết hợp Semantic Search + Keyword Search (BM25).
    
    Đây là phương pháp retrieval tiên tiến nhất hiện nay:
    - Semantic Search: Hiểu ngữ nghĩa, đồng nghĩa (vector similarity)
    - Keyword Search: Tìm chính xác từ khóa (BM25)
    
    Args:
        query: Câu hỏi
        user_id: UUID của user
        top_k: Số kết quả trả về
        alpha: Trọng số cho semantic search (0.0 - 1.0)
               alpha = 0.5: cân bằng cả hai
               alpha = 1.0: chỉ semantic
               alpha = 0.0: chỉ keyword
    
    Returns:
        List[RetrievedChunk] đã được re-ranked
    """
    if not query.strip():
        raise ValueError("Query không được để trống")
    if not user_id.strip():
        raise ValueError("user_id không được để trống")
    
    # Bước 1: Semantic Search (Vector Search)
    model = _get_model()
    query_vector = model.encode([query])[0]
    query_vector = np.asarray(query_vector, dtype=np.float32)
    query_embedding_list = query_vector.tolist()
    
    client = get_supabase_client()
    
    # Gọi RPC cho semantic search
    semantic_response = client.rpc(
        'match_embeddings_by_user',
        {
            'query_embedding': query_embedding_list,
            'user_id_filter': user_id,
            'match_count': top_k * 2  # Lấy nhiều hơn để merge
        }
    ).execute()
    
    semantic_results = semantic_response.data or []
    
    # Bước 2: Keyword Search (Full-text Search)
    # Sử dụng PostgreSQL full-text search (tsvector + tsquery)
    keyword_response = client.rpc(
        'keyword_search_by_user',
        {
            'query_text': query,
            'user_id_filter': user_id,
            'match_count': top_k * 2
        }
    ).execute()
    
    keyword_results = keyword_response.data or []
    
    # Bước 3: Reciprocal Rank Fusion (RRF) để merge kết quả
    # RRF formula: score = 1 / (k + rank)
    k = 60  # Hằng số RRF (thường dùng 60)
    
    # Map để lưu điểm tổng hợp
    merged_scores: Dict[str, Dict[str, Any]] = {}
    
    # Xử lý semantic results
    for rank, item in enumerate(semantic_results, start=1):
        chunk_id = f"{item.get('chunk_index')}_{item.get('document_id')}"
        rrf_score = alpha / (k + rank)
        
        if chunk_id not in merged_scores:
            merged_scores[chunk_id] = {
                'content': item.get('content', ''),
                'chunk_index': item.get('chunk_index', 0),
                'page_number': item.get('page_number'),
                'semantic_score': item.get('similarity', 0.0),
                'keyword_score': 0.0,
                'rrf_score': 0.0,
                'metadata': {
                    'document_id': item.get('document_id'),
                    'source': 'hybrid_semantic'
                }
            }
        merged_scores[chunk_id]['rrf_score'] += rrf_score
    
    # Xử lý keyword results
    for rank, item in enumerate(keyword_results, start=1):
        chunk_id = f"{item.get('chunk_index')}_{item.get('document_id')}"
        rrf_score = (1 - alpha) / (k + rank)
        
        if chunk_id not in merged_scores:
            merged_scores[chunk_id] = {
                'content': item.get('content', ''),
                'chunk_index': item.get('chunk_index', 0),
                'page_number': item.get('page_number'),
                'semantic_score': 0.0,
                'keyword_score': item.get('rank', 0.0),
                'rrf_score': 0.0,
                'metadata': {
                    'document_id': item.get('document_id'),
                    'source': 'hybrid_keyword'
                }
            }
        merged_scores[chunk_id]['rrf_score'] += rrf_score
        merged_scores[chunk_id]['keyword_score'] = item.get('rank', 0.0)
    
    # Bước 4: Sort theo RRF score và lấy top_k
    sorted_results = sorted(
        merged_scores.values(),
        key=lambda x: x['rrf_score'],
        reverse=True
    )[:top_k]
    
    # Bước 5: Convert thành RetrievedChunk
    final_chunks: List[RetrievedChunk] = []
    for item in sorted_results:
        final_chunks.append(
            RetrievedChunk(
                content=item['content'],
                chunk_index=item['chunk_index'],
                page_number=item['page_number'],
                similarity=item['rrf_score'],  # Dùng RRF score làm similarity
                metadata=item['metadata']
            )
        )
    
    return final_chunks
