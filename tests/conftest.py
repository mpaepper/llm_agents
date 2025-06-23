import os
import sys
import tempfile
from pathlib import Path
from typing import Generator, Dict, Any
from unittest.mock import Mock, MagicMock

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_config() -> Dict[str, Any]:
    """Provide a mock configuration dictionary."""
    return {
        "api_key": "test-api-key",
        "model": "test-model",
        "temperature": 0.7,
        "max_tokens": 1000,
        "tools": ["search", "python_repl"],
        "debug": True
    }


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    client = MagicMock()
    
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content="Test response",
                tool_calls=None
            )
        )
    ]
    
    client.chat.completions.create.return_value = mock_response
    
    return client


@pytest.fixture
def mock_tool():
    """Create a mock tool for testing."""
    tool = Mock()
    tool.name = "mock_tool"
    tool.description = "A mock tool for testing"
    tool.run = Mock(return_value="Mock tool result")
    return tool


@pytest.fixture
def sample_messages():
    """Provide sample messages for testing."""
    return [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, how are you?"},
        {"role": "assistant", "content": "I'm doing well, thank you!"}
    ]


@pytest.fixture
def mock_requests(monkeypatch):
    """Mock requests module for testing HTTP calls."""
    mock_get = Mock()
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": "success"}
    mock_response.text = '{"result": "success"}'
    mock_get.return_value = mock_response
    
    monkeypatch.setattr("requests.get", mock_get)
    monkeypatch.setattr("requests.post", mock_get)
    
    return mock_get


@pytest.fixture(autouse=True)
def reset_environment(monkeypatch):
    """Reset environment variables for each test."""
    test_env = {
        "OPENAI_API_KEY": "test-key",
        "GOOGLE_API_KEY": "test-google-key",
        "GOOGLE_CSE_ID": "test-cse-id"
    }
    
    for key, value in test_env.items():
        monkeypatch.setenv(key, value)
    
    yield
    
    for key in test_env:
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def capture_logs(caplog):
    """Fixture to capture log messages during tests."""
    with caplog.at_level("DEBUG"):
        yield caplog


@pytest.fixture
def isolated_filesystem(tmp_path):
    """Create an isolated filesystem for testing file operations."""
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    yield tmp_path
    
    os.chdir(original_cwd)