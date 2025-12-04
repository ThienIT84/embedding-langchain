"""Tests cho text chunking module."""
import pytest
from src.chunker import split_chunks, TextChunk
from src.text_extractor import DocumentChunk

def test_split_chunks_empty_input():
    """Test với input rỗng."""
    chunks = list(split_chunks([]))
    assert len(chunks) == 0

def test_split_chunks_single_small_chunk():
    """Test với 1 chunk nhỏ hơn chunk_size."""
    doc_chunk = DocumentChunk(text="Python là ngôn ngữ lập trình.", page_number=1)
    result = list(split_chunks([doc_chunk]))
    
    assert len(result) >= 1
    assert "Python" in result[0].text
    assert result[0].page_number == 1
    assert result[0].chunk_index >= 1

def test_split_chunks_preserves_page_number():
    """Test giữ nguyên page_number từ DocumentChunk."""
    doc_chunk = DocumentChunk(text="A" * 1000, page_number=5)
    result = list(split_chunks([doc_chunk]))
    
    assert len(result) >= 1
    assert all(chunk.page_number == 5 for chunk in result)

def test_split_chunks_increments_index():
    """Test chunk_index tăng dần."""
    doc_chunks = [
        DocumentChunk(text="A" * 1000, page_number=1),
        DocumentChunk(text="B" * 1000, page_number=2),
    ]
    result = list(split_chunks(doc_chunks))
    
    # Kiểm tra có chunks được tạo ra
    assert len(result) > 0
    
    # Kiểm tra chunk_index tăng liên tục
    for i in range(len(result) - 1):
        assert result[i + 1].chunk_index > result[i].chunk_index

def test_split_chunks_removes_empty():
    """Test loại bỏ chunks rỗng sau khi strip."""
    doc_chunk = DocumentChunk(text="   \n\n   ", page_number=1)
    result = list(split_chunks([doc_chunk]))
    
    assert len(result) == 0

def test_split_chunks_long_text(sample_long_text):
    """Test chunking với text dài."""
    doc_chunk = DocumentChunk(text=sample_long_text, page_number=1)
    result = list(split_chunks([doc_chunk]))
    
    # Phải tạo ra nhiều chunks
    assert len(result) > 1
    
    # Mỗi chunk không được rỗng
    assert all(len(chunk.text) > 0 for chunk in result)

def test_text_chunk_to_dict():
    """Test TextChunk.to_dict() serialization."""
    chunk = TextChunk(
        text="Test content",
        page_number=3,
        chunk_index=5,
        source_file="test.pdf"
    )
    result = chunk.to_dict()
    
    assert result["text"] == "Test content"
    assert result["page_number"] == 3
    assert result["chunk_index"] == 5
    assert result["source_file"] == "test.pdf"

def test_split_chunks_preserves_source_file():
    """Test giữ nguyên source_file metadata."""
    doc_chunk = DocumentChunk(
        text="Test content",
        page_number=1,
        source_file="document.pdf"
    )
    result = list(split_chunks([doc_chunk]))
    
    assert len(result) >= 1
    assert result[0].source_file == "document.pdf"
