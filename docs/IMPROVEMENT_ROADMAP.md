# 🚀 ROADMAP CẢI THIỆN HỆ THỐNG RAG - EMBEDDING_LANGCHAIN

**Ngày tạo:** 2 tháng 12, 2025  
**Đánh giá hiện tại:** 7.5-8/10  
**Mục tiêu:** 9-9.5/10

---

## 📊 TÓM TẮT ĐÁNH GIÁ

### ✅ Điểm mạnh
- Kiến trúc RAG pipeline rõ ràng, tách biệt module tốt
- Documentation xuất sắc (PHASE_A/B_EXPLAINED.md)
- Code clean, có comments tiếng Việt đầy đủ
- Integration với backend Node.js tốt
- Memory optimization với `__slots__`, generators

### ❌ Điểm yếu chính
1. **Không có Unit Tests** (nghiêm trọng nhất)
2. Thiếu Error Recovery & Retry Logic
3. Thiếu Performance Monitoring
4. Thiếu Caching Layer
5. Chưa có Batch Processing

---

# 🔴 PHASE 1: CRITICAL FIXES (BẮT BUỘC)

## ✅ BƯỚC 1: Thêm Unit Tests (Ưu tiên cao nhất)

### 1.1. Setup Testing Framework

```bash
# Cài đặt dependencies
cd Embedding_langchain
pip install pytest pytest-cov pytest-mock pytest-asyncio

# Thêm vào requirements.txt
echo "pytest>=7.4.0" >> requirements.txt
echo "pytest-cov>=4.1.0" >> requirements.txt
echo "pytest-mock>=3.12.0" >> requirements.txt
```

### 1.2. Tạo cấu trúc thư mục tests

```
Embedding_langchain/
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures dùng chung
│   ├── test_text_extractor.py   # Test PDF extraction
│   ├── test_chunker.py          # Test text chunking
│   ├── test_embedder.py         # Test embedding generation
│   ├── test_retriever.py        # Test similarity search
│   ├── test_pipeline.py         # Test orchestration
│   ├── test_rag_service.py      # Test RAG workflow
│   ├── test_prompt_builder.py   # Test prompt construction
│   └── test_llm_client.py       # Test Ollama integration
├── pytest.ini                   # Pytest configuration
└── .coveragerc                  # Coverage configuration
```

### 1.3. File: `tests/conftest.py`

```python
"""Pytest fixtures và configuration dùng chung."""
import pytest
from pathlib import Path
import tempfile
import shutil
from unittest.mock import MagicMock

@pytest.fixture
def temp_dir():
    """Tạo thư mục tạm cho tests."""
    tmp = tempfile.mkdtemp()
    yield Path(tmp)
    shutil.rmtree(tmp, ignore_errors=True)

@pytest.fixture
def sample_text():
    """Text mẫu cho testing."""
    return """
    Python là một ngôn ngữ lập trình bậc cao.
    Python được sử dụng rộng rãi trong AI và Machine Learning.
    LangChain là framework để xây dựng LLM applications.
    """

@pytest.fixture
def mock_supabase_client(mocker):
    """Mock Supabase client."""
    mock_client = MagicMock()
    mocker.patch('src.supabase_client.get_supabase_client', return_value=mock_client)
    return mock_client

@pytest.fixture
def mock_sentence_transformer(mocker):
    """Mock SentenceTransformer model."""
    mock_model = MagicMock()
    mock_model.encode.return_value = [[0.1] * 768]  # Fake 768-dim vector
    mocker.patch('sentence_transformers.SentenceTransformer', return_value=mock_model)
    return mock_model
```

### 1.4. File: `tests/test_chunker.py`

```python
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
    
    assert len(result) == 1
    assert result[0].text == "Python là ngôn ngữ lập trình."
    assert result[0].page_number == 1
    assert result[0].chunk_index == 1

def test_split_chunks_preserves_page_number():
    """Test giữ nguyên page_number từ DocumentChunk."""
    doc_chunk = DocumentChunk(text="A" * 1000, page_number=5)
    result = list(split_chunks([doc_chunk]))
    
    assert all(chunk.page_number == 5 for chunk in result)

def test_split_chunks_increments_index():
    """Test chunk_index tăng dần."""
    doc_chunks = [
        DocumentChunk(text="A" * 1000, page_number=1),
        DocumentChunk(text="B" * 1000, page_number=2),
    ]
    result = list(split_chunks(doc_chunks))
    
    # Kiểm tra chunk_index tăng liên tục
    for i, chunk in enumerate(result, start=1):
        assert chunk.chunk_index == i

def test_split_chunks_removes_empty():
    """Test loại bỏ chunks rỗng sau khi strip."""
    doc_chunk = DocumentChunk(text="   \n\n   ", page_number=1)
    result = list(split_chunks([doc_chunk]))
    
    assert len(result) == 0
```

### 1.5. File: `tests/test_embedder.py`

```python
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
    
    assert result[0].vector.shape == (768,)
    assert result[0].vector.dtype == np.float32

def test_embed_chunks_preserves_chunk_data(mock_sentence_transformer):
    """Test giữ nguyên thông tin chunk."""
    chunk = TextChunk(text="Hello", page_number=3, chunk_index=5)
    result = embed_chunks([chunk])
    
    assert result[0].chunk.text == "Hello"
    assert result[0].chunk.page_number == 3
    assert result[0].chunk.chunk_index == 5
```

### 1.6. File: `tests/test_retriever.py`

```python
"""Tests cho retrieval & similarity search."""
import pytest
import numpy as np
from src.retriever import _cosine_similarity, retrieve_similar_chunks

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

def test_retrieve_similar_chunks_empty_query():
    """Test query rỗng → raise ValueError."""
    with pytest.raises(ValueError, match="Query không được để trống"):
        retrieve_similar_chunks(query="", document_id="abc")

def test_retrieve_similar_chunks_empty_document_id():
    """Test document_id rỗng → raise ValueError."""
    with pytest.raises(ValueError, match="document_id không được để trống"):
        retrieve_similar_chunks(query="test", document_id="")
```

### 1.7. File: `tests/test_text_extractor.py`

```python
"""Tests cho PDF text extraction."""
import pytest
from pathlib import Path
from src.text_extractor import clean_text, DocumentChunk

def test_clean_text_removes_null_bytes():
    """Test loại bỏ null bytes."""
    text = "Hello\x00World"
    result = clean_text(text)
    assert "\x00" not in result
    assert result == "Hello World"

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

def test_document_chunk_to_dict():
    """Test DocumentChunk.to_dict() serialization."""
    chunk = DocumentChunk(text="Test", page_number=5, source_file="test.pdf")
    result = chunk.to_dict()
    
    assert result == {
        "text": "Test",
        "page_number": 5,
        "source_file": "test.pdf"
    }
```

### 1.8. File: `tests/test_prompt_builder.py`

```python
"""Tests cho prompt construction."""
import pytest
from src.prompt_builder import build_rag_prompt
from src.retriever import RetrievedChunk

def test_build_rag_prompt_empty_query():
    """Test query rỗng → raise ValueError."""
    with pytest.raises(ValueError, match="Query không được để trống"):
        build_rag_prompt(query="", chunks=[])

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
```

### 1.9. File: `pytest.ini`

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --cov=src
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=70
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
```

### 1.10. File: `.coveragerc`

```ini
[run]
source = src
omit = 
    */tests/*
    */__pycache__/*
    */venv/*

[report]
precision = 2
show_missing = True
skip_covered = False

[html]
directory = htmlcov
```

### 1.11. Chạy Tests

```bash
# Chạy tất cả tests
pytest

# Chạy với coverage report
pytest --cov=src --cov-report=html

# Chạy test cụ thể
pytest tests/test_chunker.py -v

# Chạy tests theo marker
pytest -m "not slow"

# Xem coverage report
# Mở file htmlcov/index.html trong browser
```

---

## ✅ BƯỚC 2: Thêm Error Recovery & Retry Logic

### 2.1. File: `src/retry_utils.py` (MỚI)

```python
"""Utilities cho retry logic với exponential backoff."""
import time
import logging
from functools import wraps
from typing import Callable, Type, Tuple

logger = logging.getLogger(__name__)

def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorator retry với exponential backoff.
    
    Args:
        max_retries: Số lần retry tối đa
        initial_delay: Delay ban đầu (giây)
        backoff_factor: Hệ số nhân cho mỗi lần retry
        exceptions: Tuple các exception cần retry
    
    Example:
        @retry_with_backoff(max_retries=3, exceptions=(requests.RequestException,))
        def call_api():
            return requests.get("https://api.example.com")
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        logger.error(
                            f"{func.__name__} failed after {max_retries} retries: {e}"
                        )
                        raise
                    
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {delay:.1f}s: {e}"
                    )
                    time.sleep(delay)
                    delay *= backoff_factor
            
            raise last_exception
        
        return wrapper
    return decorator
```

### 2.2. Cập nhật `src/llm_client.py`

```python
# Thêm import
from .retry_utils import retry_with_backoff

# Thay đổi function generate_answer
@retry_with_backoff(
    max_retries=3,
    initial_delay=2.0,
    exceptions=(requests.RequestException, requests.Timeout)
)
def generate_answer(prompt: str, model: str | None = None, timeout: int = 120) -> LLMResponse:
    """Gọi Ollama generate API với retry logic."""
    if not prompt.strip():
        raise ValueError("Prompt không được để trống")

    target_model = model or settings.ollama_model
    if not target_model:
        raise ValueError("Chưa cấu hình OLLAMA_MODEL")

    url = settings.ollama_url.rstrip("/") + "/api/generate"
    payload = {
        "model": target_model,
        "prompt": prompt,
        "stream": False,
    }

    # Thêm timeout cho mỗi request
    response = requests.post(url, json=payload, timeout=timeout)

    if response.status_code != 200:
        text = response.text[:500]
        raise LLMClientError(f"Ollama trả về mã lỗi {response.status_code}: {text}")

    data = response.json()
    answer = data.get("response")
    if not isinstance(answer, str):
        raise LLMClientError("Phản hồi từ Ollama không hợp lệ: thiếu trường 'response'")

    return LLMResponse(answer=answer.strip(), model=target_model, raw=data)
```

### 2.3. Cập nhật `src/supabase_client.py`

```python
# Thêm import
from .retry_utils import retry_with_backoff

# Thêm retry cho download_file
@retry_with_backoff(max_retries=3, initial_delay=1.0)
def download_file(file_path: str, destination: Path) -> Path:
    """Tải tệp từ bucket Supabase với retry logic."""
    client = get_supabase_client()
    response = client.storage.from_(settings.supabase_bucket).download(file_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(response)
    return destination

# Thêm retry cho insert_embeddings
@retry_with_backoff(max_retries=3, initial_delay=1.0, exceptions=(APIError,))
def insert_embeddings(rows: list[dict[str, Any]]) -> None:
    """Chèn danh sách embedding với retry logic."""
    if not rows:
        return
    client = get_supabase_client()
    
    # Batch insert nếu quá nhiều rows (tránh timeout)
    BATCH_SIZE = 100
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i:i + BATCH_SIZE]
        client.table("document_embeddings").insert(batch).execute()
        logger.info(f"Inserted batch {i//BATCH_SIZE + 1}, {len(batch)} embeddings")
```

---

## ✅ BƯỚC 3: Thêm Input Validation với Pydantic

### 3.1. Cài đặt Pydantic

```bash
pip install pydantic>=2.0.0
echo "pydantic>=2.0.0" >> requirements.txt
```

### 3.2. File: `src/validators.py` (MỚI)

```python
"""Input validation schemas với Pydantic."""
from pydantic import BaseModel, Field, validator
from typing import Optional
import uuid

class RAGQueryRequest(BaseModel):
    """Validation cho RAG query request."""
    query: str = Field(..., min_length=1, max_length=2000)
    user_id: str = Field(..., description="UUID của user")
    top_k: int = Field(default=5, ge=1, le=20)
    system_prompt: Optional[str] = Field(None, max_length=1000)
    
    @validator('query')
    def query_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Query không được chỉ chứa khoảng trắng')
        return v.strip()
    
    @validator('user_id')
    def validate_uuid(cls, v):
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError('user_id phải là UUID hợp lệ')
        return v

class DocumentIngestRequest(BaseModel):
    """Validation cho document ingestion."""
    document_id: str = Field(..., description="UUID của document")
    
    @validator('document_id')
    def validate_uuid(cls, v):
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError('document_id phải là UUID hợp lệ')
        return v

class ChunkConfig(BaseModel):
    """Validation cho chunking configuration."""
    chunk_size: int = Field(default=900, ge=100, le=2000)
    chunk_overlap: int = Field(default=200, ge=0, le=500)
    
    @validator('chunk_overlap')
    def overlap_less_than_size(cls, v, values):
        if 'chunk_size' in values and v >= values['chunk_size']:
            raise ValueError('chunk_overlap phải nhỏ hơn chunk_size')
        return v
```

### 3.3. Cập nhật `src/rag_service.py`

```python
# Thêm import
from .validators import RAGQueryRequest

# Cập nhật function rag_query
def rag_query(
    query: str,
    user_id: str,
    top_k: int = 5,
    system_prompt: str | None = None,
) -> Dict[str, Any]:
    """RAG query với input validation."""
    
    # Validate input với Pydantic
    try:
        validated = RAGQueryRequest(
            query=query,
            user_id=user_id,
            top_k=top_k,
            system_prompt=system_prompt
        )
    except Exception as e:
        raise ValueError(f"Invalid input: {e}")
    
    start = perf_counter()
    
    # Sử dụng validated data
    retrieved_chunks = retrieve_similar_chunks_by_user(
        query=validated.query,
        user_id=validated.user_id,
        top_k=validated.top_k
    )
    
    prompt = build_rag_prompt(
        query=validated.query,
        chunks=retrieved_chunks,
        system_prompt=validated.system_prompt
    )
    
    llm_response: LLMResponse = generate_answer(prompt=prompt)
    elapsed_ms = (perf_counter() - start) * 1000

    return {
        "answer": llm_response.answer,
        "sources": [_serialize_chunk(chunk) for chunk in retrieved_chunks],
        "metadata": {
            "model": llm_response.model,
            "query_time_ms": round(elapsed_ms, 2),
            "chunk_count": len(retrieved_chunks),
        },
        "prompt": prompt,
        "raw_llm_response": llm_response.raw,
    }
```

---

# 🟡 PHASE 2: HIGH PRIORITY IMPROVEMENTS

## ✅ BƯỚC 4: Performance Monitoring

### 4.1. File: `src/performance_monitor.py` (MỚI)

```python
"""Performance monitoring và metrics tracking."""
import time
import logging
from functools import wraps
from typing import Callable, Dict, Any
from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Lưu trữ performance metrics."""
    total_calls: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    errors: int = 0
    
    def update(self, duration: float, is_error: bool = False):
        """Cập nhật metrics."""
        self.total_calls += 1
        self.total_time += duration
        self.min_time = min(self.min_time, duration)
        self.max_time = max(self.max_time, duration)
        if is_error:
            self.errors += 1
    
    @property
    def avg_time(self) -> float:
        """Tính thời gian trung bình."""
        return self.total_time / self.total_calls if self.total_calls > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert sang dictionary."""
        return {
            "total_calls": self.total_calls,
            "total_time_seconds": round(self.total_time, 3),
            "avg_time_seconds": round(self.avg_time, 3),
            "min_time_seconds": round(self.min_time, 3),
            "max_time_seconds": round(self.max_time, 3),
            "errors": self.errors,
            "success_rate": round((self.total_calls - self.errors) / self.total_calls * 100, 2) if self.total_calls > 0 else 0.0
        }

class PerformanceMonitor:
    """Singleton class quản lý performance metrics."""
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._metrics = defaultdict(PerformanceMetrics)
        return cls._instance
    
    def record(self, function_name: str, duration: float, is_error: bool = False):
        """Ghi nhận metrics cho function."""
        self._metrics[function_name].update(duration, is_error)
    
    def get_metrics(self, function_name: str = None) -> Dict[str, Any]:
        """Lấy metrics của function hoặc tất cả."""
        if function_name:
            return {function_name: self._metrics[function_name].to_dict()}
        return {name: metrics.to_dict() for name, metrics in self._metrics.items()}
    
    def reset(self):
        """Reset tất cả metrics."""
        self._metrics.clear()

# Global monitor instance
monitor = PerformanceMonitor()

def track_performance(func: Callable):
    """Decorator để track performance của function."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        is_error = False
        
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            is_error = True
            raise
        finally:
            duration = time.perf_counter() - start
            monitor.record(func.__name__, duration, is_error)
            logger.debug(f"{func.__name__} took {duration:.3f}s")
    
    return wrapper
```

### 4.2. Cập nhật các modules với performance tracking

```python
# src/embedder.py
from .performance_monitor import track_performance

@track_performance
def embed_chunks(chunks: Iterable[TextChunk]) -> List[EmbeddingResult]:
    """Sinh embedding với performance tracking."""
    # ... existing code ...

# src/retriever.py
@track_performance
def retrieve_similar_chunks_by_user(query: str, user_id: str, top_k: int = 5):
    """Retrieve với performance tracking."""
    # ... existing code ...

# src/llm_client.py
@track_performance
def generate_answer(prompt: str, model: str | None = None, timeout: int = 120):
    """Generate answer với performance tracking."""
    # ... existing code ...
```

### 4.3. File: `scripts/show_metrics.py` (MỚI)

```python
#!/usr/bin/env python
"""Script hiển thị performance metrics."""
import json
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.performance_monitor import monitor

def main():
    """Hiển thị metrics."""
    metrics = monitor.get_metrics()
    
    print("\n" + "="*60)
    print("PERFORMANCE METRICS")
    print("="*60)
    
    for func_name, data in metrics.items():
        print(f"\n📊 {func_name}")
        print(f"   Total calls: {data['total_calls']}")
        print(f"   Avg time: {data['avg_time_seconds']:.3f}s")
        print(f"   Min time: {data['min_time_seconds']:.3f}s")
        print(f"   Max time: {data['max_time_seconds']:.3f}s")
        print(f"   Errors: {data['errors']}")
        print(f"   Success rate: {data['success_rate']:.2f}%")
    
    # Export to JSON
    output_file = Path("performance_metrics.json")
    output_file.write_text(json.dumps(metrics, indent=2, ensure_ascii=False))
    print(f"\n✅ Metrics exported to {output_file}")

if __name__ == "__main__":
    main()
```

---

## ✅ BƯỚC 5: Caching Layer

### 5.1. File: `src/cache_manager.py` (MỚI)

```python
"""Simple in-memory cache cho embeddings và queries."""
import hashlib
import logging
from typing import Any, Optional
from functools import lru_cache
import pickle

logger = logging.getLogger(__name__)

class EmbeddingCache:
    """Cache cho embeddings để tránh encode lại text giống nhau."""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: dict[str, Any] = {}
    
    def _make_key(self, text: str) -> str:
        """Tạo cache key từ text (hash MD5)."""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def get(self, text: str) -> Optional[Any]:
        """Lấy embedding từ cache."""
        key = self._make_key(text)
        return self._cache.get(key)
    
    def set(self, text: str, embedding: Any):
        """Lưu embedding vào cache."""
        if len(self._cache) >= self.max_size:
            # Simple LRU: xóa item đầu tiên
            self._cache.pop(next(iter(self._cache)))
        
        key = self._make_key(text)
        self._cache[key] = embedding
        logger.debug(f"Cached embedding for text (hash: {key[:8]}...)")
    
    def clear(self):
        """Xóa toàn bộ cache."""
        self._cache.clear()
        logger.info("Embedding cache cleared")

# Global cache instance
embedding_cache = EmbeddingCache(max_size=1000)

@lru_cache(maxsize=100)
def get_query_embedding_cached(query: str):
    """
    Cache cho query embeddings với LRU.
    Sử dụng functools.lru_cache cho queries phổ biến.
    """
    from .embedder import _get_model
    import numpy as np
    
    model = _get_model()
    vector = model.encode([query])[0]
    return np.asarray(vector, dtype=np.float32)
```

### 5.2. Cập nhật `src/embedder.py` để sử dụng cache

```python
from .cache_manager import embedding_cache

def embed_chunks(chunks: Iterable[TextChunk]) -> List[EmbeddingResult]:
    """Sinh embedding với caching."""
    chunk_list = list(chunks)
    if not chunk_list:
        return []
    
    model = _get_model()
    results = []
    texts_to_encode = []
    cache_indices = []
    
    # Check cache trước
    for idx, chunk in enumerate(chunk_list):
        cached_vector = embedding_cache.get(chunk.text)
        if cached_vector is not None:
            results.append(EmbeddingResult(chunk=chunk, vector=cached_vector))
        else:
            texts_to_encode.append(chunk.text)
            cache_indices.append(idx)
    
    # Encode các text chưa có trong cache
    if texts_to_encode:
        embeddings = model.encode(texts_to_encode, show_progress_bar=True)
        for idx, (text, vector) in enumerate(zip(texts_to_encode, embeddings)):
            vector_np = np.array(vector, dtype=np.float32)
            # Lưu vào cache
            embedding_cache.set(text, vector_np)
            # Thêm vào results
            chunk_idx = cache_indices[idx]
            results.insert(chunk_idx, EmbeddingResult(
                chunk=chunk_list[chunk_idx],
                vector=vector_np
            ))
    
    return results
```

### 5.3. Cập nhật `src/retriever.py` để sử dụng query cache

```python
from .cache_manager import get_query_embedding_cached

def retrieve_similar_chunks_by_user(query: str, user_id: str, top_k: int = 5):
    """Retrieve với query embedding cache."""
    if not query.strip():
        raise ValueError("Query không được để trống")
    if not user_id.strip():
        raise ValueError("user_id không được để trống")
    
    # Sử dụng cached query embedding
    query_vector = get_query_embedding_cached(query.strip())
    query_embedding_list = query_vector.tolist()
    
    # ... rest of the code ...
```

---

## ✅ BƯỚC 6: Batch Processing

### 6.1. File: `src/batch_processor.py` (MỚI)

```python
"""Batch processing cho multiple documents."""
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
from dataclasses import dataclass

from .pipeline import process_document

logger = logging.getLogger(__name__)

@dataclass
class BatchResult:
    """Kết quả xử lý batch."""
    document_id: str
    success: bool
    error: Optional[str] = None
    duration: float = 0.0

def process_documents_batch(
    document_ids: List[str],
    max_workers: int = 4
) -> List[BatchResult]:
    """
    Xử lý batch documents song song với ThreadPoolExecutor.
    
    Args:
        document_ids: Danh sách document IDs cần xử lý
        max_workers: Số worker threads (mặc định 4)
    
    Returns:
        List[BatchResult]: Kết quả xử lý từng document
    """
    if not document_ids:
        return []
    
    logger.info(f"Starting batch processing for {len(document_ids)} documents")
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit tất cả tasks
        future_to_doc_id = {
            executor.submit(_process_single_document, doc_id): doc_id
            for doc_id in document_ids
        }
        
        # Collect results khi hoàn thành
        for future in as_completed(future_to_doc_id):
            doc_id = future_to_doc_id[future]
            try:
                result = future.result()
                results.append(result)
                logger.info(f"✅ Completed {doc_id}: {result.success}")
            except Exception as e:
                logger.error(f"❌ Failed {doc_id}: {e}")
                results.append(BatchResult(
                    document_id=doc_id,
                    success=False,
                    error=str(e)
                ))
    
    # Summary
    success_count = sum(1 for r in results if r.success)
    logger.info(
        f"Batch processing completed: {success_count}/{len(results)} successful"
    )
    
    return results

def _process_single_document(document_id: str) -> BatchResult:
    """Process một document và trả về BatchResult."""
    import time
    start = time.perf_counter()
    
    try:
        process_document(document_id)
        duration = time.perf_counter() - start
        return BatchResult(
            document_id=document_id,
            success=True,
            duration=duration
        )
    except Exception as e:
        duration = time.perf_counter() - start
        return BatchResult(
            document_id=document_id,
            success=False,
            error=str(e),
            duration=duration
        )
```

### 6.2. File: `scripts/batch_ingest.py` (MỚI)

```python
#!/usr/bin/env python
"""Script chạy batch ingestion cho multiple documents."""
import sys
import json
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.batch_processor import process_documents_batch

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python batch_ingest.py <doc_id1> <doc_id2> ...")
        print("   or: python batch_ingest.py --file document_ids.txt")
        sys.exit(1)
    
    # Parse document IDs
    if sys.argv[1] == "--file":
        # Đọc từ file
        file_path = Path(sys.argv[2])
        document_ids = file_path.read_text().strip().split('\n')
    else:
        # Từ command line args
        document_ids = sys.argv[1:]
    
    print(f"📦 Processing {len(document_ids)} documents in batch...")
    
    # Process batch
    results = process_documents_batch(document_ids, max_workers=4)
    
    # Print summary
    print("\n" + "="*60)
    print("BATCH PROCESSING SUMMARY")
    print("="*60)
    
    for result in results:
        status = "✅ SUCCESS" if result.success else "❌ FAILED"
        print(f"{status} | {result.document_id} | {result.duration:.2f}s")
        if result.error:
            print(f"  Error: {result.error}")
    
    # Export results
    output = {
        "total": len(results),
        "success": sum(1 for r in results if r.success),
        "failed": sum(1 for r in results if not r.success),
        "results": [
            {
                "document_id": r.document_id,
                "success": r.success,
                "error": r.error,
                "duration": round(r.duration, 2)
            }
            for r in results
        ]
    }
    
    output_file = Path("batch_results.json")
    output_file.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\n📊 Results exported to {output_file}")

if __name__ == "__main__":
    main()
```

---

# 🟢 PHASE 3: ADVANCED IMPROVEMENTS

## ✅ BƯỚC 7: Advanced Text Cleaning

### 7.1. Cập nhật `src/text_extractor.py`

```python
import re
from pathlib import Path
from typing import Iterable
from pypdf import PdfReader
import logging

logger = logging.getLogger(__name__)

def clean_text(text: str) -> str:
    """
    Hàm làm sạch văn bản nâng cao hơn.
    """
    if not text:
        return ""
    
    # 1. Loại bỏ Null bytes
    text = text.replace("\x00", "")
    
    # 2. Loại bỏ special characters thừa
    text = re.sub(r'[©®™]', '', text)
    
    # 3. Nối các từ bị ngắt dòng
    text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
    
    # 4. Loại bỏ URLs
    text = re.sub(r'https?://\S+', '', text)
    
    # 5. Loại bỏ emails
    text = re.sub(r'\S+@\S+', '', text)
    
    # 6. Chuẩn hóa khoảng trắng
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 7. Loại bỏ multiple punctuation
    text = re.sub(r'([!?.]){2,}', r'\1', text)
    
    return text
```

---

## ✅ BƯỚC 8: Semantic Chunking (Advanced)

### 8.1. File: `src/semantic_chunker.py` (MỚI)

```python
"""Semantic-aware chunking strategy."""
import re
from typing import List, Iterator
from .text_extractor import DocumentChunk
from .chunker import TextChunk

class SemanticChunker:
    """Chunk text dựa trên semantic boundaries (paragraphs, sections)."""
    
    def __init__(self, max_chunk_size: int = 900, overlap: int = 100):
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap
    
    def split(self, chunks: List[DocumentChunk]) -> Iterator[TextChunk]:
        """Split documents thành semantic chunks."""
        global_chunk_index = 0
        
        for doc_chunk in chunks:
            # Split theo paragraphs trước
            paragraphs = self._split_paragraphs(doc_chunk.text)
            
            current_chunk = []
            current_length = 0
            
            for para in paragraphs:
                para_length = len(para)
                
                if current_length + para_length > self.max_chunk_size:
                    # Flush current chunk
                    if current_chunk:
                        global_chunk_index += 1
                        yield TextChunk(
                            text=" ".join(current_chunk),
                            page_number=doc_chunk.page_number,
                            chunk_index=global_chunk_index,
                            source_file=doc_chunk.source_file
                        )
                    
                    # Start new chunk với overlap
                    if self.overlap > 0 and current_chunk:
                        overlap_text = current_chunk[-1][:self.overlap]
                        current_chunk = [overlap_text, para]
                        current_length = len(overlap_text) + para_length
                    else:
                        current_chunk = [para]
                        current_length = para_length
                else:
                    current_chunk.append(para)
                    current_length += para_length
            
            # Flush remaining
            if current_chunk:
                global_chunk_index += 1
                yield TextChunk(
                    text=" ".join(current_chunk),
                    page_number=doc_chunk.page_number,
                    chunk_index=global_chunk_index,
                    source_file=doc_chunk.source_file
                )
    
    def _split_paragraphs(self, text: str) -> List[str]:
        """Split text thành paragraphs."""
        # Split by double newlines hoặc section headers
        paragraphs = re.split(r'\n\n+', text)
        return [p.strip() for p in paragraphs if p.strip()]
```

---

## ✅ BƯỚC 9: Logging Configuration

### 9.1. File: `src/logging_config.py` (MỚI)

```python
"""Centralized logging configuration."""
import logging
import sys
from pathlib import Path

def setup_logging(level: str = "INFO", log_file: Path = None):
    """
    Setup logging cho toàn bộ application.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional file path để ghi logs
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Format
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    handlers = [console_handler]
    
    # File handler (optional)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    
    # Root logger
    logging.basicConfig(
        level=log_level,
        handlers=handlers
    )
    
    # Suppress noisy libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('sentence_transformers').setLevel(logging.WARNING)
```

### 9.2. Cập nhật `src/config.py`

```python
from .logging_config import setup_logging

# Setup logging khi import config
setup_logging(
    level=os.getenv("LOG_LEVEL", "INFO"),
    log_file=Path("logs/app.log") if os.getenv("LOG_TO_FILE") else None
)
```

---

## ✅ BƯỚC 10: CI/CD với GitHub Actions

### 10.1. File: `.github/workflows/tests.yml` (MỚI)

```yaml
name: Tests

on:
  push:
    branches: [ main, devThien ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        cd Embedding_langchain
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-mock
    
    - name: Run tests
      run: |
        cd Embedding_langchain
        pytest --cov=src --cov-report=xml --cov-report=term
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./Embedding_langchain/coverage.xml
        flags: unittests
        name: codecov-umbrella
```

---

# 📊 CHECKLIST HOÀN THÀNH

## 🔴 CRITICAL (Phải làm)
- [ ] **BƯỚC 1:** Thêm Unit Tests (pytest) ⭐⭐⭐⭐⭐
  - [ ] tests/test_chunker.py
  - [ ] tests/test_embedder.py
  - [ ] tests/test_retriever.py
  - [ ] tests/test_text_extractor.py
  - [ ] tests/test_prompt_builder.py
  - [ ] Đạt coverage ≥70%

- [ ] **BƯỚC 2:** Retry Logic với Exponential Backoff ⭐⭐⭐⭐
  - [ ] src/retry_utils.py
  - [ ] Cập nhật llm_client.py
  - [ ] Cập nhật supabase_client.py

- [ ] **BƯỚC 3:** Input Validation với Pydantic ⭐⭐⭐⭐
  - [ ] src/validators.py
  - [ ] Cập nhật rag_service.py

## 🟡 HIGH PRIORITY (Nên làm)
- [ ] **BƯỚC 4:** Performance Monitoring ⭐⭐⭐
  - [ ] src/performance_monitor.py
  - [ ] scripts/show_metrics.py
  - [ ] Thêm @track_performance decorators

- [ ] **BƯỚC 5:** Caching Layer ⭐⭐⭐
  - [ ] src/cache_manager.py
  - [ ] Cập nhật embedder.py với cache
  - [ ] Cập nhật retriever.py với query cache

- [ ] **BƯỚC 6:** Batch Processing ⭐⭐⭐
  - [ ] src/batch_processor.py
  - [ ] scripts/batch_ingest.py

## 🟢 MEDIUM PRIORITY (Tốt nếu có)
- [ ] **BƯỚC 7:** Advanced Text Cleaning ⭐⭐
- [ ] **BƯỚC 8:** Semantic Chunking ⭐⭐
- [ ] **BƯỚC 9:** Logging Configuration ⭐⭐
- [ ] **BƯỚC 10:** CI/CD Pipeline ⭐⭐

---

# 🎯 TIMELINE DỰ KIẾN

| Giai đoạn | Thời gian | Mục tiêu |
|-----------|-----------|----------|
| **Week 1** | 3-5 ngày | BƯỚC 1-3 (Tests, Retry, Validation) |
| **Week 2** | 2-3 ngày | BƯỚC 4-6 (Monitoring, Cache, Batch) |
| **Week 3** | 2-3 ngày | BƯỚC 7-10 (Advanced features) |
| **Week 4** | 1-2 ngày | Testing, Documentation, Polish |

**Tổng thời gian:** 2-4 tuần (tùy tốc độ)

---

# 📈 EXPECTED IMPROVEMENT

| Tiêu chí | Trước | Sau | Cải thiện |
|----------|-------|-----|-----------|
| Testing | 1/10 | 9/10 | +8 |
| Error Handling | 6.5/10 | 9/10 | +2.5 |
| Performance | 6/10 | 8.5/10 | +2.5 |
| Code Quality | 7/10 | 9/10 | +2 |
| **TỔNG** | **7.5/10** | **9.5/10** | **+2** ✨

---

# 🚀 GETTING STARTED

```bash
# 1. Clone hoặc checkout branch mới
git checkout -b feature/improvements

# 2. Bắt đầu với tests (BƯỚC 1)
cd Embedding_langchain
mkdir tests
pip install pytest pytest-cov pytest-mock

# 3. Tạo file tests đầu tiên
# Copy code từ BƯỚC 1.3 → tests/conftest.py
# Copy code từ BƯỚC 1.4 → tests/test_chunker.py

# 4. Chạy tests
pytest -v

# 5. Commit từng bước
git add tests/
git commit -m "feat: add unit tests for chunker module"

# 6. Tiếp tục với BƯỚC 2, 3...
```

---

# ❓ FAQ

**Q: Phải làm tất cả không?**  
A: Không. Ưu tiên PHASE 1 (BƯỚC 1-3) để đạt 8.5/10. PHASE 2-3 là bonus.

**Q: Mất bao lâu?**  
A: BƯỚC 1 (tests) mất 3-5 ngày. Toàn bộ roadmap 2-4 tuần.

**Q: Làm thế nào để kiểm tra?**  
A: Chạy `pytest --cov=src` sau mỗi bước. Coverage ≥70% là tốt.

**Q: Có thể làm từng phần không?**  
A: Có! Mỗi BƯỚC độc lập. Commit riêng từng feature.

---

**🎓 Chúc các bạn thành công với đồ án!**
