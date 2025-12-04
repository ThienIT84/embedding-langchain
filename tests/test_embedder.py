"""Tests cho embedding generation."""
import pytest
import numpy as np
from src.embedder import embed_chunks, EmbeddingResult
from src.chunker import TextChunk

def test_embed_chunks_empty_input():
    """Test với danh sách rỗng."""
    result = embed_chunks([])
    assert result == []

def test_embed_chunks_returns_correct_type(mock_sentence_transformer):
    """Test trả về list[EmbeddingResult]."""
    chunks = [TextChunk(text="Python", chunk_index=1)]
    result = embed_chunks(chunks)
    
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], EmbeddingResult)

def test_embed_chunks_vector_dimension(mock_sentence_transformer):
    """Test vector có đúng 768 chiều."""
    chunks = [TextChunk(text="Test", chunk_index=1)]
    result = embed_chunks(chunks)
    
    assert len(result) == 1
    assert result[0].vector.shape == (768,)
    assert result[0].vector.dtype == np.float32

def test_embed_chunks_preserves_chunk_data(mock_sentence_transformer):
    """Test giữ nguyên thông tin chunk."""
    chunk = TextChunk(text="Hello", page_number=3, chunk_index=5)
    result = embed_chunks([chunk])
    
    assert len(result) == 1
    assert result[0].chunk.text == "Hello"
    assert result[0].chunk.page_number == 3
    assert result[0].chunk.chunk_index == 5

def test_embed_chunks_multiple(mock_sentence_transformer):
    """Test embedding nhiều chunks cùng lúc."""
    chunks = [
        TextChunk(text="First chunk", chunk_index=1),
        TextChunk(text="Second chunk", chunk_index=2),
        TextChunk(text="Third chunk", chunk_index=3),
    ]
    result = embed_chunks(chunks)
    
    assert len(result) == 3
    assert all(isinstance(r, EmbeddingResult) for r in result)
    assert all(r.vector.shape == (768,) for r in result)

def test_embed_chunks_vector_values(mock_sentence_transformer):
    """Test vector có giá trị hợp lệ (không NaN, không Inf)."""
    chunks = [TextChunk(text="Test", chunk_index=1)]
    result = embed_chunks(chunks)
    
    vector = result[0].vector
    assert not np.isnan(vector).any()
    assert not np.isinf(vector).any()
    assert np.all(vector >= -1.0) and np.all(vector <= 1.0)

def test_embedding_result_attributes():
    """Test EmbeddingResult có đủ attributes."""
    chunk = TextChunk(text="Test", chunk_index=1)
    vector = np.array([0.1] * 768, dtype=np.float32)
    result = EmbeddingResult(chunk=chunk, vector=vector)
    
    assert hasattr(result, 'chunk')
    assert hasattr(result, 'vector')
    assert result.chunk == chunk
    assert np.array_equal(result.vector, vector)
