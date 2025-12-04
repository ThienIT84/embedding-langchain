"""Tests cho Pydantic validators."""
import pytest
from pydantic import ValidationError
from src.validators import (
    RAGQueryRequest,
    DocumentIngestRequest,
    ChunkConfig,
    RetrievalConfig,
    EmbeddingModelConfig
)

# ===== RAGQueryRequest Tests =====

def test_rag_query_request_valid():
    """Test valid RAG query request."""
    request = RAGQueryRequest(
        query="What is Python?",
        user_id="123e4567-e89b-12d3-a456-426614174000",
        top_k=5
    )
    
    assert request.query == "What is Python?"
    assert request.user_id == "123e4567-e89b-12d3-a456-426614174000"
    assert request.top_k == 5

def test_rag_query_request_strips_query():
    """Test query được strip whitespace."""
    request = RAGQueryRequest(
        query="  What is Python?  ",
        user_id="123e4567-e89b-12d3-a456-426614174000"
    )
    
    assert request.query == "What is Python?"

def test_rag_query_request_empty_query():
    """Test query rỗng → ValidationError."""
    with pytest.raises(ValidationError, match="Query không được chỉ chứa khoảng trắng"):
        RAGQueryRequest(
            query="",
            user_id="123e4567-e89b-12d3-a456-426614174000"
        )

def test_rag_query_request_invalid_uuid():
    """Test user_id không phải UUID → ValidationError."""
    with pytest.raises(ValidationError, match="user_id phải là UUID hợp lệ"):
        RAGQueryRequest(
            query="Test",
            user_id="not-a-uuid"
        )

def test_rag_query_request_top_k_out_of_range():
    """Test top_k ngoài range [1, 20]."""
    with pytest.raises(ValidationError):
        RAGQueryRequest(
            query="Test",
            user_id="123e4567-e89b-12d3-a456-426614174000",
            top_k=0  # < 1
        )
    
    with pytest.raises(ValidationError):
        RAGQueryRequest(
            query="Test",
            user_id="123e4567-e89b-12d3-a456-426614174000",
            top_k=25  # > 20
        )

def test_rag_query_request_with_system_prompt():
    """Test với custom system prompt."""
    request = RAGQueryRequest(
        query="Test",
        user_id="123e4567-e89b-12d3-a456-426614174000",
        system_prompt="You are a helpful assistant."
    )
    
    assert request.system_prompt == "You are a helpful assistant."

# ===== DocumentIngestRequest Tests =====

def test_document_ingest_request_valid():
    """Test valid document ingest request."""
    request = DocumentIngestRequest(
        document_id="123e4567-e89b-12d3-a456-426614174000"
    )
    
    assert request.document_id == "123e4567-e89b-12d3-a456-426614174000"
    assert request.force_refresh is False

def test_document_ingest_request_invalid_uuid():
    """Test document_id không phải UUID."""
    with pytest.raises(ValidationError, match="document_id phải là UUID hợp lệ"):
        DocumentIngestRequest(document_id="invalid-id")

def test_document_ingest_request_force_refresh():
    """Test force_refresh flag."""
    request = DocumentIngestRequest(
        document_id="123e4567-e89b-12d3-a456-426614174000",
        force_refresh=True
    )
    
    assert request.force_refresh is True

# ===== ChunkConfig Tests =====

def test_chunk_config_valid():
    """Test valid chunk configuration."""
    config = ChunkConfig(chunk_size=1000, chunk_overlap=100)
    
    assert config.chunk_size == 1000
    assert config.chunk_overlap == 100

def test_chunk_config_defaults():
    """Test default values."""
    config = ChunkConfig()
    
    assert config.chunk_size == 900
    assert config.chunk_overlap == 200

def test_chunk_config_overlap_greater_than_size():
    """Test chunk_overlap >= chunk_size → ValidationError."""
    with pytest.raises(ValidationError, match="chunk_overlap phải nhỏ hơn chunk_size"):
        ChunkConfig(chunk_size=500, chunk_overlap=500)
    
    with pytest.raises(ValidationError, match="chunk_overlap phải nhỏ hơn chunk_size"):
        ChunkConfig(chunk_size=500, chunk_overlap=600)

def test_chunk_config_size_out_of_range():
    """Test chunk_size ngoài range [100, 2000]."""
    with pytest.raises(ValidationError):
        ChunkConfig(chunk_size=50)  # < 100
    
    with pytest.raises(ValidationError):
        ChunkConfig(chunk_size=3000)  # > 2000

# ===== RetrievalConfig Tests =====

def test_retrieval_config_valid():
    """Test valid retrieval configuration."""
    config = RetrievalConfig(top_k=10, similarity_threshold=0.7)
    
    assert config.top_k == 10
    assert config.similarity_threshold == 0.7

def test_retrieval_config_defaults():
    """Test default values."""
    config = RetrievalConfig()
    
    assert config.top_k == 5
    assert config.similarity_threshold == 0.0

def test_retrieval_config_threshold_out_of_range():
    """Test similarity_threshold ngoài [0, 1]."""
    with pytest.raises(ValidationError):
        RetrievalConfig(similarity_threshold=-0.1)
    
    with pytest.raises(ValidationError):
        RetrievalConfig(similarity_threshold=1.5)

# ===== EmbeddingModelConfig Tests =====

def test_embedding_model_config_valid():
    """Test valid embedding model configuration."""
    config = EmbeddingModelConfig(
        model_name="custom-model",
        embedding_dimension=512,
        batch_size=64
    )
    
    assert config.model_name == "custom-model"
    assert config.embedding_dimension == 512
    assert config.batch_size == 64

def test_embedding_model_config_defaults():
    """Test default values."""
    config = EmbeddingModelConfig()
    
    assert config.model_name == "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    assert config.embedding_dimension == 768
    assert config.batch_size == 32

def test_embedding_model_config_dimension_out_of_range():
    """Test embedding_dimension ngoài range."""
    with pytest.raises(ValidationError):
        EmbeddingModelConfig(embedding_dimension=64)  # < 128
    
    with pytest.raises(ValidationError):
        EmbeddingModelConfig(embedding_dimension=5000)  # > 4096
