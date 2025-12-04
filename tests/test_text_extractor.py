"""Tests cho PDF text extraction."""
import pytest
from pathlib import Path
from src.text_extractor import clean_text, DocumentChunk

def test_clean_text_removes_null_bytes():
    """Test loại bỏ null bytes."""
    text = "Hello\x00World"
    result = clean_text(text)
    assert "\x00" not in result
    assert "Hello" in result
    assert "World" in result

def test_clean_text_joins_hyphenated_words():
    """Test nối từ bị ngắt dòng."""
    text = "process- \ning data"
    result = clean_text(text)
    assert result == "processing data"

def test_clean_text_normalizes_whitespace():
    """Test chuẩn hóa khoảng trắng."""
    text = "Hello    \n\n  World  \t  Test"
    result = clean_text(text)
    assert result == "Hello World Test"

def test_clean_text_empty_input():
    """Test với input rỗng."""
    result = clean_text("")
    assert result == ""

def test_clean_text_none_input():
    """Test với None input."""
    result = clean_text(None)
    assert result == ""

def test_clean_text_multiple_hyphens():
    """Test với nhiều từ bị ngắt dòng."""
    text = "auto- \nmatic trans- \nformation"
    result = clean_text(text)
    assert result == "automatic transformation"

def test_clean_text_preserves_normal_hyphens():
    """Test giữ nguyên dấu gạch ngang bình thường."""
    text = "state-of-the-art technology"
    result = clean_text(text)
    assert "state-of-the-art" in result

def test_document_chunk_to_dict():
    """Test DocumentChunk.to_dict() serialization."""
    chunk = DocumentChunk(text="Test", page_number=5, source_file="test.pdf")
    result = chunk.to_dict()
    
    assert result == {
        "text": "Test",
        "page_number": 5,
        "source_file": "test.pdf"
    }

def test_document_chunk_default_source():
    """Test DocumentChunk với source_file mặc định."""
    chunk = DocumentChunk(text="Test", page_number=1)
    assert chunk.source_file == "unknown"

def test_document_chunk_none_page_number():
    """Test DocumentChunk với page_number=None."""
    chunk = DocumentChunk(text="Test", page_number=None)
    result = chunk.to_dict()
    assert result["page_number"] is None

def test_clean_text_strips_leading_trailing():
    """Test loại bỏ khoảng trắng đầu cuối."""
    text = "   Hello World   "
    result = clean_text(text)
    assert result == "Hello World"

def test_clean_text_complex_whitespace():
    """Test xử lý nhiều loại whitespace."""
    text = "Line1\n\n\nLine2\r\nLine3\t\tLine4"
    result = clean_text(text)
    assert result == "Line1 Line2 Line3 Line4"
