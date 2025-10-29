from __future__ import annotations

from typing import Iterable, List

import numpy as np
from sentence_transformers import SentenceTransformer

from .config import settings
from .chunker import TextChunk


"""Sinh vector embedding cho từng đoạn văn bản đã được chunk."""


class EmbeddingResult:
    """Đóng gói TextChunk cùng vector embedding tương ứng."""
    __slots__ = ("chunk", "vector")

    def __init__(self, chunk: TextChunk, vector: np.ndarray) -> None:
        self.chunk = chunk
        self.vector = vector


_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    """Khởi tạo (hoặc tái sử dụng) model SentenceTransformer dùng chung."""
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.hf_model_name)
    return _model


def embed_chunks(chunks: Iterable[TextChunk]) -> List[EmbeddingResult]:
    """Sinh embedding cho danh sách TextChunk và trả về kết quả dạng list."""
    chunk_list = list(chunks)
    if not chunk_list:
        return []
    model = _get_model()
    embeddings = model.encode([chunk.text for chunk in chunk_list], show_progress_bar=True)
    return [EmbeddingResult(chunk=chunk, vector=np.array(vector, dtype=np.float32)) for chunk, vector in zip(chunk_list, embeddings)]
