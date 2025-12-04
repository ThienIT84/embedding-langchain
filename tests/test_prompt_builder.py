"""Tests cho prompt construction."""
import pytest
from src.prompt_builder import build_rag_prompt
from src.retriever import RetrievedChunk

def test_build_rag_prompt_empty_query():
    """Test query rỗng → raise ValueError."""
    with pytest.raises(ValueError, match="Query không được để trống"):
        build_rag_prompt(query="", chunks=[])

def test_build_rag_prompt_query_only_spaces():
    """Test query chỉ có spaces → raise ValueError."""
    with pytest.raises(ValueError, match="Query không được để trống"):
        build_rag_prompt(query="   ", chunks=[])

def test_build_rag_prompt_no_chunks():
    """Test không có chunks → hiển thị thông báo không có context."""
    prompt = build_rag_prompt(query="Test question", chunks=[])
    
    assert "Test question" in prompt
    assert "Không có context phù hợp" in prompt

def test_build_rag_prompt_with_chunks():
    """Test với chunks hợp lệ."""
    chunks = [
        RetrievedChunk(content="Python is great", chunk_index=1, page_number=5, similarity=0.95),
        RetrievedChunk(content="AI is powerful", chunk_index=2, page_number=6, similarity=0.85),
    ]
    prompt = build_rag_prompt(query="What is Python?", chunks=chunks)
    
    assert "What is Python?" in prompt
    assert "Python is great" in prompt
    assert "AI is powerful" in prompt
    assert "Trang 5" in prompt
    assert "0.9500" in prompt

def test_build_rag_prompt_custom_system_prompt():
    """Test custom system prompt."""
    custom_prompt = "You are a helpful assistant."
    chunks = [RetrievedChunk(content="Test", chunk_index=1, page_number=1, similarity=0.9)]
    
    result = build_rag_prompt(query="Test", chunks=chunks, system_prompt=custom_prompt)
    assert "You are a helpful assistant." in result

def test_build_rag_prompt_default_system_prompt():
    """Test sử dụng default system prompt."""
    chunks = [RetrievedChunk(content="Test", chunk_index=1, page_number=1, similarity=0.9)]
    result = build_rag_prompt(query="Test", chunks=chunks)
    
    # Kiểm tra có system prompt mặc định
    assert "trợ lý AI" in result.lower() or "assistant" in result.lower()

def test_build_rag_prompt_chunk_without_page_number():
    """Test chunk không có page_number."""
    chunks = [
        RetrievedChunk(content="Content without page", chunk_index=1, page_number=None, similarity=0.9)
    ]
    prompt = build_rag_prompt(query="Test", chunks=chunks)
    
    assert "Content without page" in prompt

def test_build_rag_prompt_multiple_chunks_ordering():
    """Test thứ tự chunks được giữ nguyên."""
    chunks = [
        RetrievedChunk(content="First", chunk_index=1, page_number=1, similarity=0.9),
        RetrievedChunk(content="Second", chunk_index=2, page_number=2, similarity=0.8),
        RetrievedChunk(content="Third", chunk_index=3, page_number=3, similarity=0.7),
    ]
    prompt = build_rag_prompt(query="Test", chunks=chunks)
    
    # Kiểm tra thứ tự xuất hiện
    first_pos = prompt.find("First")
    second_pos = prompt.find("Second")
    third_pos = prompt.find("Third")
    
    assert first_pos < second_pos < third_pos

def test_build_rag_prompt_strips_query():
    """Test query được strip whitespace."""
    chunks = [RetrievedChunk(content="Test", chunk_index=1, page_number=1, similarity=0.9)]
    prompt = build_rag_prompt(query="  What is this?  ", chunks=chunks)
    
    assert "What is this?" in prompt
    # Không nên có leading/trailing spaces xung quanh query
    assert "  What is this?  " not in prompt
