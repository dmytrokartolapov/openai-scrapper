import hashlib
import json
import re
import time
from datetime import datetime
from json import JSONDecodeError
from typing import Annotated

from fastapi import FastAPI, status, Depends, Request
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph.state import CompiledStateGraph
from newspaper import Article
from pydantic import ValidationError
from qdrant_client import QdrantClient
from starlette.responses import JSONResponse, RedirectResponse

from src.logger import setup_logger
from src.models.search_request import SearchRequest
from src.models.search_response import SearchResponse
from src.models.health_status import HealthStatus
from src.models.scrap_request import ScrapRequest
from src.models.scrap_response import ScrapResponse
from src.settings import SYSTEM_PROMPT, MAX_RETRIES, RETRY_DELAY

logger = setup_logger()
app = FastAPI()
ARTICLE_CACHE = {}  # Variable is enough for testing purposes. In real api needs better solution.


def hash_url(url) -> int:
    """Use SHA256 hash and take the first 8 bytes as an integer"""
    return int(hashlib.sha256(url.encode("utf-8")).hexdigest()[:16], 16)


def extract_news(url: str, chunk_index: int = 0, chunk_size: int = 3000) -> str:
    """
    Fetches and extracts the headline and main body text from a provided news article URL.

    Args:
        url (str): The URL of the news article to be processed.

    Returns:
        str: A formatted string containing the headline and the article's main text content.

    Notes:
    - Only the main headline and article text are returned; metadata, comments, and unrelated sections are excluded.
    - Make sure the URL is valid and points to an accessible news article.
    - The output format is:
    {
        "headline": "Headline",
        "chunk_index": 0,
        "chunk": "Chunk Text",
        "call_again": true,
        "total_chunks": 10
    }
    """
    url_hash = str(hash_url(url))

    if url_hash not in ARTICLE_CACHE:
        # First call: fetch and split
        article = Article(url)
        article.download()
        article.parse()
        text = article.text
        splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=0)
        chunks = splitter.split_text(text)
        ARTICLE_CACHE[url_hash] = {
            "headline": article.title,
            "chunks": chunks,
        }

    else:
        # Subsequent calls: use cached chunks
        chunks = ARTICLE_CACHE[url_hash]["chunks"]

    response = {
        "headline": ARTICLE_CACHE[url_hash]["headline"] if chunk_index == 0 else "",
        "chunk_index": chunk_index,
        "chunk": chunks[chunk_index],
        "call_again": chunk_index < len(chunks) - 1,
        "total_chunks": len(chunks),
    }

    if not response["call_again"]:
        ARTICLE_CACHE.pop(url_hash)

    return json.dumps(response)


def get_agent(
    model: ChatOpenAI = Depends(lambda: ChatOpenAI(model="gpt-5-mini", temperature=0.1, max_tokens=1000, timeout=300)),  # type: ignore
    tools: list = Depends(lambda: [extract_news]),
    system_prompt: str = Depends(lambda: SYSTEM_PROMPT),
) -> CompiledStateGraph:
    return create_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
    )


def get_db(
    client: QdrantClient = Depends(lambda: QdrantClient(location="localhost", port=6333)),
) -> QdrantClient:
    collection_name = "news_articles"

    if not client.collection_exists(collection_name):
        client.create_collection(collection_name=collection_name, vectors_config=client.get_fastembed_vector_params())

    return client


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    logger.error(f"Validation error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "detail": "Validation Error",
            "errors": str(exc.errors()),
            "request_url": str(request.url),
            "timestamp": datetime.now().isoformat() + "Z",
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal Server Error. Please try again later.",
            "error_type": type(exc).__name__,
            "request_url": str(request.url),
            "timestamp": datetime.now().isoformat() + "Z",
        },
    )


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


@app.get(
    "/health",
    tags=["health"],
    status_code=status.HTTP_200_OK,
    response_model=HealthStatus,
    summary="Health status",
)
async def health() -> HealthStatus:
    """Basic health status."""
    return HealthStatus(status="ok")


@app.get(
    "/v1/db/scrape_url",
    status_code=status.HTTP_200_OK,
    tags=["scrape_url"],
    summary="Scrape news article in chunks and store in database.",
)
def db_scrape_url(
    query: Annotated[ScrapRequest, Depends()],
    agent: Annotated[CompiledStateGraph, Depends(get_agent)],
    db: Annotated[QdrantClient, Depends(get_db)],
) -> ScrapResponse:
    url = query.url
    hashed_url = hash_url(url)
    logger.info(f"Scraping URL: {url}. Hashed: {hashed_url}")

    messages = []
    chunk_index = 0
    chunk_summaries = []
    keywords_set = set()
    headline = ""
    full_chunks = []
    call_again = True
    logger.info("Get chunks and their summaries")

    while call_again:
        # Single agent call: get chunk and summarize
        for retry in range(MAX_RETRIES):
            try:
                chunk_result = agent.invoke(
                    {
                        "messages": [
                            {
                                "role": "user",
                                "content": f"""
                                Use the extract_news tool with url='{url}' and chunk_index={chunk_index}.
                                Then, summarize the returned chunk and extract keywords into json.
                                Response must contain: 'headline', 'summary', 'keywords', 'call_again' from extract_news tool.
                                """,
                            }
                        ]
                    }
                )
                messages.extend(
                    re.sub(r"\s+", " ", message.content).strip()
                    for message in chunk_result["messages"]
                    if message.content
                )
                tool_json = json.loads(chunk_result["messages"][-2].content)
                result_json = json.loads(chunk_result["messages"][-1].content)
                logger.info(f"Chunk: {chunk_index}. Result: {tool_json}")
                logger.info(f"Result: {result_json}")
                break

            except JSONDecodeError as error:
                if retry < MAX_RETRIES - 1:
                    logger.warning(f"Failed to extract news article: {error}")

                else:
                    logger.error(f"Failed to extract news article: {error}")
                    raise error

        if not headline:
            headline = result_json["headline"]

        chunk_summaries.append(result_json["summary"])
        full_chunks.append(tool_json["chunk"])
        keywords_set.update(result_json.get("keywords", []))
        call_again = result_json["call_again"]
        chunk_index += 1

    logger.info("Make final summary from chunks")

    for retry in range(MAX_RETRIES):
        try:
            combine_result = agent.invoke(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": f"""
                            Combine the following summaries into a single, concise 2-4 sentence summary of the entire article,
                            and extract 3-7 keywords that best represent the main topics in Output Format (JSON).
                            Response must contain: 'headline', 'summary', 'keywords'.
                            Summaries:
                            {" ".join(chunk_summaries)}
                            """,
                        }
                    ]
                }
            )
            messages.extend(
                re.sub(r"\s+", " ", message.content).strip()
                for message in combine_result["messages"]
                if message.content
            )
            result_json = json.loads(combine_result["messages"][-1].content)
            logger.info(f"Result: {result_json}")
            break

        except JSONDecodeError as error:
            if retry < MAX_RETRIES - 1:
                logger.warning(f"Failed to extract news article: {error}")
                time.sleep(RETRY_DELAY)

            else:
                logger.error(f"Failed to extract news article: {error}")
                raise error

    final_summary = result_json["summary"]
    keywords = result_json["keywords"]

    # Store in database
    joined_chunks = "\n".join(full_chunks)
    db.add(
        collection_name="news_articles",
        documents=[joined_chunks],
        metadata=[
            {
                "headline": headline,
                "text": joined_chunks,
                "summary": final_summary,
                "keywords": ", ".join(keywords),
            }
        ],
        ids=[hashed_url],
    )
    logger.info("Article stored in Qdrant.")
    return ScrapResponse(url=url, messages=messages, job="saved_to_db")


@app.get(
    "/v1/db/semantic_search",
    status_code=status.HTTP_200_OK,
    tags=["semantic_search"],
    summary="Runs semantic search in database.",
)
async def db_semantic_search(
    query: Annotated[SearchRequest, Depends()],
    db: Annotated[QdrantClient, Depends(get_db)],
) -> SearchResponse:
    query_text = query.text
    limit = int(query.limit)
    logger.info(f"Semantic search for: {query_text}. Limit: {limit}")
    response = db.query(collection_name="news_articles", query_text=query_text, limit=limit)
    payload = [str(result.metadata) for result in response]
    logger.info(f"Results: {payload}")
    return SearchResponse(text=query_text, payload=payload, job="read_from_db")
