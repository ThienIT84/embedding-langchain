"""Tests cho RAG service (end-to-end workflow)."""
import pytest
from src.rag_service import rag_query, _serialize_chunk
from src.retriever import RetrievedChunk

def test_serialize_chunk():
    """Test _serialize_chunk helper function."""
    chunk = RetrievedChunk(
        content="Test content",
        chunk_index=5,
        page_number=3,
        similarity=0.95
    )
    
    result = _serialize_chunk(chunk)
    
    assert result == {
        "content": "Test content",
        "chunk_index": 5,
        "page_number": 3,
        "similarity": 0.95
    }

def test_rag_query_returns_dict(mock_sentence_transformer, mock_supabase_client, mock_ollama):
    """Test rag_query trả về dictionary với đủ fields."""
    # Mock Supabase trả về empty (no chunks)
    mock_supabase_client.rpc().execute.return_value.data = []
    
    result = rag_query(
        query="What is Python?",
        user_id="user-123",
        top_k=5
    )
    
    assert isinstance(result, dict)
    assert "answer" in result
    assert "sources" in result
    assert "metadata" in result
    assert "prompt" in result

def test_rag_query_metadata_structure(mock_sentence_transformer, mock_supabase_client, mock_ollama):
    """Test metadata có đủ thông tin."""
    mock_supabase_client.rpc().execute.return_value.data = []
    
    result = rag_query(
        query="Test",
        user_id="user-123",
        top_k=3
    )
    
    metadata = result["metadata"]
    assert "model" in metadata
    assert "query_time_ms" in metadata
    assert "chunk_count" in metadata
    assert isinstance(metadata["query_time_ms"], (int, float))

def test_rag_query_sources_is_list(mock_sentence_transformer, mock_supabase_client, mock_ollama):
    """Test sources là list."""
    mock_supabase_client.rpc().execute.return_value.data = []
    
    result = rag_query(query="Test", user_id="user-123")
    
    assert isinstance(result["sources"], list)

def test_rag_query_with_custom_top_k(mock_sentence_transformer, mock_supabase_client, mock_ollama):
    """Test với custom top_k parameter."""
    mock_supabase_client.rpc().execute.return_value.data = []
    
    result = rag_query(
        query="Test",
        user_id="user-123",
        top_k=10
    )
    
    # Metadata nên phản ánh số chunks
    assert result["metadata"]["chunk_count"] == 0  # Vì mock return empty

def test_rag_query_with_system_prompt(mock_sentence_transformer, mock_supabase_client, mock_ollama):
    """Test với custom system prompt."""
    mock_supabase_client.rpc().execute.return_value.data = []
    
    custom_prompt = "You are a Python expert."
    result = rag_query(
        query="Test",
        user_id="user-123",
        system_prompt=custom_prompt
    )
    
    # System prompt nên xuất hiện trong prompt
    assert custom_prompt in result["prompt"]

def test_rag_query_answer_type(mock_sentence_transformer, mock_supabase_client, mock_ollama):
    """Test answer là string."""
    mock_supabase_client.rpc().execute.return_value.data = []
    
    result = rag_query(query="Test", user_id="user-123")
    
    assert isinstance(result["answer"], str)
    assert len(result["answer"]) > 0

def test_rag_query_includes_raw_response(mock_sentence_transformer, mock_supabase_client, mock_ollama):
    """Test có raw_llm_response để debug."""
    mock_supabase_client.rpc().execute.return_value.data = []
    
    result = rag_query(query="Test", user_id="user-123")
    
    assert "raw_llm_response" in result
    assert isinstance(result["raw_llm_response"], dict)
