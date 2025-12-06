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
    """Khởi tạo model và move to GPU nếu có."""
    global _model
    if _model is None:
        import torch
        _model = SentenceTransformer(settings.hf_model_name)
        
        # Auto-detect và sử dụng GPU
        if torch.cuda.is_available():
            _model = _model.to('cuda')
            print(f"✅ Model on GPU: {torch.cuda.get_device_name(0)}")
        else:
            print("⚠️ GPU not available, using CPU")
    return _model


def embed_chunks(chunks: Iterable[TextChunk]) -> List[EmbeddingResult]:
    """Sinh embedding với GPU acceleration nếu có."""
    chunk_list = list(chunks)
    if not chunk_list:
        return []
    
    model = _get_model()
    
    # Optimize batch size cho GPU (GTX 1650 4GB VRAM)
    import torch
    batch_size = 64 if torch.cuda.is_available() else 32
    
    embeddings = model.encode(
        [chunk.text for chunk in chunk_list],
        batch_size=batch_size,
        show_progress_bar=True,
        convert_to_numpy=True
    )
    
    return [EmbeddingResult(chunk=chunk, vector=np.array(vector, dtype=np.float32)) 
            for chunk, vector in zip(chunk_list, embeddings)]
