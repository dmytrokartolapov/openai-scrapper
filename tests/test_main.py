import pytest
import json
from httpx import AsyncClient, ASGITransport
from fastapi import status
from unittest.mock import MagicMock

from src.main import app, extract_news, hash_url, get_db, get_agent


@app.get("/raise-exception")
async def raise_exception():
    raise Exception("Test error")


@pytest.mark.asyncio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_validation_error_handler():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/v1/db/scrape_url?url=error")
        assert resp.status_code == 422
        assert "code" in resp.json() or "detail" in resp.json()


@pytest.mark.asyncio
async def test_unhandled_exception_handler():
    # Set raise_app_exceptions=False to let FastAPI handle the exception
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/raise-exception")
        assert resp.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = resp.json()
        assert data["detail"].startswith("Internal Server Error")
        assert data["error_type"] == "Exception"
        assert "request_url" in data
        assert "timestamp" in data


def test_extract_news(monkeypatch):
    class DummyArticle:
        def __init__(self, url):
            self.title = "Test Headline"
            self.text = "Test article body.\n\nSecond paragraph."

        def download(self):
            pass

        def parse(self):
            pass

    monkeypatch.setattr("src.main.Article", DummyArticle)
    url = "http://example.com/news"
    result = extract_news(url)
    data = json.loads(result)
    assert data["headline"] == "Test Headline"
    assert "Test article body." in data["article"]


def test_hash_url_consistency():
    url = "http://example.com/news"
    h1 = hash_url(url)
    h2 = hash_url(url)
    assert isinstance(h1, int)
    assert h1 == h2
    # Different URL should produce different hash
    assert h1 != hash_url("http://example.com/other")


def test_get_db_creates_collection(monkeypatch):
    mock_client = MagicMock()
    mock_client.collection_exists.return_value = False
    mock_client.get_fastembed_vector_params.return_value = {"size": 10}
    mock_client.create_collection.return_value = None

    db = get_db(client=mock_client)
    mock_client.collection_exists.assert_called_once_with("news_articles")
    mock_client.create_collection.assert_called_once()
    assert db == mock_client


def test_get_db_existing_collection(monkeypatch):
    mock_client = MagicMock()
    mock_client.collection_exists.return_value = True
    db = get_db(client=mock_client)
    mock_client.create_collection.assert_not_called()
    assert db == mock_client


def test_get_agent_returns_agent(monkeypatch):
    mock_model = MagicMock()
    mock_tools = [lambda x: x]
    mock_system_prompt = "Prompt"
    mock_agent = MagicMock()
    monkeypatch.setattr("src.main.create_agent", lambda model, tools, system_prompt: mock_agent)
    agent = get_agent(model=mock_model, tools=mock_tools, system_prompt=mock_system_prompt)
    assert agent == mock_agent


@pytest.mark.asyncio
async def test_db_scrape_url():
    class DummyDB:
        def collection_exists(self, name):
            return True

        def add(self, collection_name, documents, metadata, ids):
            pass

    class DummyMessage:
        def __init__(self, content):
            self.content = content

    class DummyAgent:
        def invoke(self, payload):
            return {
                "messages": [
                    DummyMessage(json.dumps({"headline": "Test Headline", "article": "Test Article"})),
                    DummyMessage(
                        json.dumps(
                            {"headline": "Test Headline", "summary": "Test Summary", "keywords": ["news", "test"]}
                        )
                    ),
                ]
            }

    app.dependency_overrides[get_agent] = lambda: DummyAgent()
    app.dependency_overrides[get_db] = lambda: DummyDB()

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/v1/db/scrape_url?url=http://example.com/news")
        assert resp.status_code == 200
        data = resp.json()
        assert data["url"] == "http://example.com/news"
        assert "messages" in data
        assert data["job"] == "saved_to_db"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_db_semantic_search():
    # Dummy DB and result
    class DummyResult:
        def __init__(self, metadata):
            self.metadata = metadata

    class DummyDB:
        def query(self, collection_name, query_text, limit):
            return [DummyResult(metadata={"headline": "Test", "summary": "Summary"})]

    # Override get_db dependency
    app.dependency_overrides[get_db] = lambda: DummyDB()

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/v1/db/semantic_search?text=economy&limit=1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["text"] == "economy"
        assert isinstance(data["payload"], list)
        assert data["job"] == "read_from_db"

    app.dependency_overrides.clear()
