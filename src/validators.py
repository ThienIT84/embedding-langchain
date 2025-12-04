"""Input validation schemas với Pydantic."""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
import uuid

class RAGQueryRequest(BaseModel):
    """Validation cho RAG query request."""
    query: str = Field(..., min_length=1, max_length=2000, description="Câu hỏi của user")
    user_id: str = Field(..., description="UUID của user (từ JWT token)")
    top_k: int = Field(default=5, ge=1, le=20, description="Số chunks muốn retrieve")
    system_prompt: Optional[str] = Field(None, max_length=1000, description="Custom system prompt")
    
    @field_validator('query')
    @classmethod
    def query_not_empty(cls, v: str) -> str:
        """Validate query không rỗng và strip whitespace."""
        if not v.strip():
            raise ValueError('Query không được chỉ chứa khoảng trắng')
        return v.strip()
    
    @field_validator('user_id')
    @classmethod
    def validate_uuid(cls, v: str) -> str:
        """Validate user_id là UUID hợp lệ."""
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError('user_id phải là UUID hợp lệ')
        return v
    
    @field_validator('system_prompt')
    @classmethod
    def strip_system_prompt(cls, v: Optional[str]) -> Optional[str]:
        """Strip system prompt nếu có."""
        if v is not None:
            return v.strip() if v.strip() else None
        return v


class DocumentIngestRequest(BaseModel):
    """Validation cho document ingestion request."""
    document_id: str = Field(..., description="UUID của document cần ingest")
    force_refresh: bool = Field(default=False, description="Force re-embedding dù đã có embeddings")
    
    @field_validator('document_id')
    @classmethod
    def validate_uuid(cls, v: str) -> str:
        """Validate document_id là UUID hợp lệ."""
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError('document_id phải là UUID hợp lệ')
        return v


class ChunkConfig(BaseModel):
    """Validation cho chunking configuration."""
    chunk_size: int = Field(default=900, ge=100, le=2000, description="Kích thước mỗi chunk (characters)")
    chunk_overlap: int = Field(default=200, ge=0, le=500, description="Overlap giữa các chunks")
    
    @field_validator('chunk_overlap')
    @classmethod
    def overlap_less_than_size(cls, v: int, info) -> int:
        """Validate chunk_overlap < chunk_size."""
        chunk_size = info.data.get('chunk_size')
        if chunk_size is not None and v >= chunk_size:
            raise ValueError('chunk_overlap phải nhỏ hơn chunk_size')
        return v


class RetrievalConfig(BaseModel):
    """Validation cho retrieval configuration."""
    top_k: int = Field(default=5, ge=1, le=50, description="Số chunks retrieve")
    similarity_threshold: float = Field(
        default=0.0, 
        ge=0.0, 
        le=1.0,
        description="Ngưỡng similarity tối thiểu (0-1)"
    )
    
    @field_validator('similarity_threshold')
    @classmethod
    def validate_threshold(cls, v: float) -> float:
        """Validate similarity threshold trong khoảng [0, 1]."""
        if not 0.0 <= v <= 1.0:
            raise ValueError('similarity_threshold phải trong khoảng [0.0, 1.0]')
        return v


class EmbeddingModelConfig(BaseModel):
    """Validation cho embedding model configuration."""
    model_name: str = Field(
        default="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        description="Tên model từ HuggingFace"
    )
    embedding_dimension: int = Field(
        default=768,
        ge=128,
        le=4096,
        description="Số chiều của embedding vector"
    )
    batch_size: int = Field(
        default=32,
        ge=1,
        le=256,
        description="Batch size khi encoding"
    )
