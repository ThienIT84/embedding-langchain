"""Tests cho retrieval & similarity search."""
import pytest
import numpy as np
from src.retriever import _cosine_similarity, retrieve_similar_chunks, RetrievedChunk

def test_cosine_similarity_identical_vectors():
    """Test 2 vectors giống nhau → similarity = 1.0."""
    a = np.array([1.0, 2.0, 3.0])
    b = np.array([1.0, 2.0, 3.0])
    
    similarity = _cosine_similarity(a, b)
    assert abs(similarity - 1.0) < 0.0001

def test_cosine_similarity_orthogonal_vectors():
    """Test 2 vectors vuông góc → similarity = 0.0."""
    a = np.array([1.0, 0.0])
    b = np.array([0.0, 1.0])
    
    similarity = _cosine_similarity(a, b)
    assert abs(similarity - 0.0) < 0.0001

def test_cosine_similarity_zero_vector():
    """Test với zero vector → similarity = 0.0."""
    a = np.array([0.0, 0.0, 0.0])
    b = np.array([1.0, 2.0, 3.0])
    
    similarity = _cosine_similarity(a, b)
    assert similarity == 0.0

def test_cosine_similarity_opposite_vectors():
    """Test 2 vectors ngược hướng → similarity = -1.0."""
    a = np.array([1.0, 0.0])
    b = np.array([-1.0, 0.0])
    
    similarity = _cosine_similarity(a, b)
    assert abs(similarity - (-1.0)) < 0.0001

def test_retrieve_similar_chunks_empty_query():
    """Test query rỗng → raise ValueError."""
    with pytest.raises(ValueError, match="Query không được để trống"):
        retrieve_similar_chunks(query="", document_id="abc")

def test_retrieve_similar_chunks_empty_query_with_spaces():
    """Test query chỉ có spaces → raise ValueError."""
    with pytest.raises(ValueError, match="Query không được để trống"):
        retrieve_similar_chunks(query="   ", document_id="abc")

def test_retrieve_similar_chunks_empty_document_id():
    """Test document_id rỗng → raise ValueError."""
    with pytest.raises(ValueError, match="document_id không được để trống"):
        retrieve_similar_chunks(query="test", document_id="")

def test_retrieve_similar_chunks_empty_document_id_with_spaces():
    """Test document_id chỉ có spaces → raise ValueError."""
    with pytest.raises(ValueError, match="document_id không được để trống"):
        retrieve_similar_chunks(query="test", document_id="   ")

def test_retrieve_similar_chunks_no_results(mock_sentence_transformer, mock_supabase_client):
    """Test khi không có chunks trong DB → trả về empty list."""
    # Mock Supabase trả về rỗng
    mock_supabase_client.table().select().eq().execute.return_value.data = []
    
    result = retrieve_similar_chunks(query="test", document_id="doc-123", top_k=5)
    
    assert result == []

def test_retrieved_chunk_dataclass():
    """Test RetrievedChunk dataclass."""
    chunk = RetrievedChunk(
        content="Test content",
        chunk_index=5,
        page_number=3,
        similarity=0.95
    )
    
    assert chunk.content == "Test content"
    assert chunk.chunk_index == 5
    assert chunk.page_number == 3
    assert chunk.similarity == 0.95

def test_cosine_similarity_normalized_vectors():
    """Test với vectors đã normalized."""
    a = np.array([1.0, 0.0, 0.0])
    b = np.array([0.707, 0.707, 0.0])  # 45 degrees
    
    similarity = _cosine_similarity(a, b)
    assert 0.7 < similarity < 0.71  # cos(45°) ≈ 0.707
