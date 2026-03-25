import pytest
import respx


@pytest.fixture(autouse=True)
def set_api_key(monkeypatch):
    monkeypatch.setenv("REDASH_API_KEY", "test_key_abc123")  # gitleaks:allow
    monkeypatch.setenv("REDASH_URL", "https://redash.example.com")


@pytest.fixture(autouse=True)
def reset_client():
    from redash_mcp import auth, client

    auth.reset_api_key_provider()
    client._client = None
    yield
    auth.reset_api_key_provider()
    client._client = None


@pytest.fixture
def mock_api():
    with respx.mock(base_url="https://redash.example.com") as respx_mock:
        yield respx_mock
