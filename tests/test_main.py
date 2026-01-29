import pytest
import json
from httpx import AsyncClient, ASGITransport
from fastapi import status
from unittest.mock import MagicMock

from starlette.testclient import TestClient

from src.main import app, extract_news, hash_url, get_db, get_agent


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


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
    # Dummy Article class to mock newspaper3k's Article
    class DummyArticle:
        def __init__(self, url):
            self.title = "Test Headline"
            self.text = "Test article body.\n\nSecond paragraph."

        def download(self):
            pass

        def parse(self):
            pass

    # Dummy splitter to mock RecursiveCharacterTextSplitter
    class DummySplitter:
        def __init__(self, chunk_size, chunk_overlap):
            self.chunk_size = chunk_size
            self.chunk_overlap = chunk_overlap

        def split_text(self, text):
            # Just split by paragraphs for testing
            return text.split('\n')

    # Patch Article and RecursiveCharacterTextSplitter
    monkeypatch.setattr("src.main.Article", DummyArticle)
    monkeypatch.setattr("src.main.RecursiveCharacterTextSplitter", DummySplitter)

    url = "http://example.com/news"
    result = extract_news(url)
    data = json.loads(result)

    assert data["headline"] == "Test Headline"
    assert data["chunk_index"] == 0
    assert "Test article body." in data["chunk"]
    assert data["call_again"] is True
    assert data["total_chunks"] == 2

    # Test second chunk (simulate next call)
    result2 = extract_news(url, chunk_index=1)
    data2 = json.loads(result2)
    assert data2["headline"] == ""  # Only first chunk returns headline
    assert data2["chunk_index"] == 1
    assert "Second paragraph." in data2["chunk"]
    assert data2["call_again"] is False
    assert data2["total_chunks"] == 2


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


def test_db_scrape_url(client):
    # Dummy agent to simulate chunking and combining
    class DummyMessage:
        def __init__(self, content):
            self.content = content

    class DummyAgent:
        def __init__(self):
            self.call_count = 0

        def invoke(self, payload):
            # First two calls: chunking (simulate two chunks)
            if self.call_count == 0:
                self.call_count += 1
                return {
                    "messages": [
                        DummyMessage(json.dumps({"chunk": "Chunk 1"})),
                        DummyMessage(json.dumps({
                            "headline": "Test Headline",
                            "summary": "Summary 1",
                            "keywords": ["news", "test"],
                            "call_again": True
                        }))
                    ]
                }
            elif self.call_count == 1:
                self.call_count += 1
                return {
                    "messages": [
                        DummyMessage(json.dumps({"chunk": "Chunk 2"})),
                        DummyMessage(json.dumps({
                            "headline": "Test Headline",
                            "summary": "Summary 2",
                            "keywords": ["news", "test2"],
                            "call_again": False
                        }))
                    ]
                }
            # Third call: combine summaries
            else:
                return {
                    "messages": [
                        DummyMessage(json.dumps({
                            "headline": "Test Headline",
                            "summary": "Final Summary",
                            "keywords": ["news", "test", "final"]
                        }))
                    ]
                }

    # Dummy DB with call tracking
    dummy_db = MagicMock()
    dummy_db.collection_exists.return_value = True

    app.dependency_overrides[get_agent] = lambda: DummyAgent()
    app.dependency_overrides[get_db] = lambda: dummy_db

    resp = client.get("/v1/db/scrape_url?url=http://example.com/news")
    assert resp.status_code == 200
    data = resp.json()
    assert data["url"] == "http://example.com/news"
    assert "messages" in data
    assert data["job"] == "saved_to_db"

    # Check DB add call
    dummy_db.add.assert_called_once()
    _, kwargs = dummy_db.add.call_args
    assert kwargs["collection_name"] == "news_articles"
    assert "Chunk 1" in kwargs["documents"][0]
    assert "Chunk 2" in kwargs["documents"][0]
    metadata = kwargs["metadata"][0]
    assert metadata["headline"] == "Test Headline"
    assert metadata["summary"] == "Final Summary"
    assert "news" in metadata["keywords"]

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
