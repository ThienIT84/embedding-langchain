"""Pytest fixtures và configuration dùng chung."""
import pytest
from pathlib import Path
import tempfile
import shutil
from unittest.mock import MagicMock
import numpy as np

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
    Retrieval-Augmented Generation (RAG) kết hợp retrieval với generation.
    """

@pytest.fixture
def sample_long_text():
    """Text dài để test chunking."""
    return " ".join(["This is sentence number {}.".format(i) for i in range(200)])

@pytest.fixture
def mock_supabase_client(mocker):
    """Mock Supabase client."""
    mock_client = MagicMock()
    
    # Mock table operations
    mock_table = MagicMock()
    mock_table.select.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.limit.return_value = mock_table
    mock_table.insert.return_value = mock_table
    mock_table.delete.return_value = mock_table
    mock_table.update.return_value = mock_table
    mock_table.upsert.return_value = mock_table
    mock_table.execute.return_value = MagicMock(data=[])
    
    mock_client.table.return_value = mock_table
    
    # Mock RPC
    mock_rpc = MagicMock()
    mock_rpc.execute.return_value = MagicMock(data=[])
    mock_client.rpc.return_value = mock_rpc
    
    mocker.patch('src.supabase_client.get_supabase_client', return_value=mock_client)
    return mock_client

@pytest.fixture
def mock_sentence_transformer(mocker):
    """Mock SentenceTransformer model."""
    mock_model = MagicMock()
    
    # Fake 768-dim vectors
    def mock_encode(texts, **kwargs):
        if isinstance(texts, str):
            texts = [texts]
        return np.array([[0.1] * 768 for _ in texts], dtype=np.float32)
    
    mock_model.encode.side_effect = mock_encode
    mocker.patch('sentence_transformers.SentenceTransformer', return_value=mock_model)
    
    return mock_model

@pytest.fixture
def mock_ollama(mocker):
    """Mock Ollama API calls."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "response": "This is a test answer from LLM.",
        "model": "llama3"
    }
    
    mocker.patch('requests.post', return_value=mock_response)
    return mock_response
