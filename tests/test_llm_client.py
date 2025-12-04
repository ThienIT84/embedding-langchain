"""Tests cho LLM client (Ollama integration)."""
import pytest
from src.llm_client import generate_answer, LLMResponse, LLMClientError

def test_generate_answer_empty_prompt():
    """Test prompt rỗng → raise ValueError."""
    with pytest.raises(ValueError, match="Prompt không được để trống"):
        generate_answer(prompt="")

def test_generate_answer_prompt_only_spaces():
    """Test prompt chỉ có spaces → raise ValueError."""
    with pytest.raises(ValueError, match="Prompt không được để trống"):
        generate_answer(prompt="   ")

def test_generate_answer_success(mock_ollama):
    """Test generate answer thành công."""
    result = generate_answer(prompt="What is Python?")
    
    assert isinstance(result, LLMResponse)
    assert isinstance(result.answer, str)
    assert len(result.answer) > 0
    assert result.model == "llama3"

def test_generate_answer_returns_llm_response_type(mock_ollama):
    """Test trả về đúng type LLMResponse."""
    result = generate_answer(prompt="Test")
    
    assert hasattr(result, 'answer')
    assert hasattr(result, 'model')
    assert hasattr(result, 'raw')

def test_generate_answer_strips_answer(mock_ollama):
    """Test answer được strip whitespace."""
    # Mock response với leading/trailing spaces
    mock_ollama.json.return_value = {
        "response": "  Answer with spaces  ",
        "model": "llama3"
    }
    
    result = generate_answer(prompt="Test")
    assert result.answer == "Answer with spaces"

def test_generate_answer_custom_model(mock_ollama):
    """Test với custom model name."""
    result = generate_answer(prompt="Test", model="custom-model")
    
    # Kiểm tra request được gửi đi có đúng model không
    import requests
    call_args = requests.post.call_args
    payload = call_args[1]['json']
    assert payload['model'] == "custom-model"

def test_llm_response_dataclass():
    """Test LLMResponse dataclass."""
    response = LLMResponse(
        answer="Test answer",
        model="llama3",
        raw={"response": "Test answer", "model": "llama3"}
    )
    
    assert response.answer == "Test answer"
    assert response.model == "llama3"
    assert isinstance(response.raw, dict)

def test_generate_answer_http_error(mocker):
    """Test xử lý HTTP error."""
    # Mock requests.post raise exception
    mocker.patch('requests.post', side_effect=Exception("Connection error"))
    
    with pytest.raises(LLMClientError):
        generate_answer(prompt="Test")

def test_generate_answer_non_200_status(mocker):
    """Test xử lý non-200 status code."""
    mock_response = mocker.MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal server error"
    
    mocker.patch('requests.post', return_value=mock_response)
    
    with pytest.raises(LLMClientError, match="500"):
        generate_answer(prompt="Test")

def test_generate_answer_invalid_response_format(mocker):
    """Test xử lý response không có field 'response'."""
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"model": "llama3"}  # Missing 'response' field
    
    mocker.patch('requests.post', return_value=mock_response)
    
    with pytest.raises(LLMClientError, match="không hợp lệ"):
        generate_answer(prompt="Test")
