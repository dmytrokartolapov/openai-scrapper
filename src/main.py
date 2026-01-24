import hashlib
import json
from datetime import datetime
from typing import Annotated

from fastapi import FastAPI, status, Depends, Request
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langgraph.graph.state import CompiledStateGraph
from newspaper import Article
from pydantic import ValidationError
from qdrant_client import QdrantClient
from starlette.responses import JSONResponse


from src.logger import setup_logger
from src.models.search_request import SearchRequest
from src.models.search_response import SearchResponse
from src.models.health_status import HealthStatus
from src.models.scrap_request import ScrapRequest
from src.models.scrap_response import ScrapResponse

logger = setup_logger()

SYSTEM_PROMPT = """
**Instructions:**  
You are a news analyst. Your tasks are to:
1. Summarize the news article provided.
2. Identify and list the main topics as concise keywords.

**Steps to Follow:**
- Read the provided headline and article content.
- Write a brief summary (2-4 sentences) capturing the key points.
- List 3-7 relevant keywords that reflect the main topics.

**Constraints:**
- The summary must be factual and objective.
- Do not include opinions or interpretations.
- Keywords should be single words or short phrases.
- Do not repeat the headline verbatim in the summary.

**Input:**  
- Headline: {headline}  
- Article: {full_text}  

**Output Format (JSON):**  
Return your response in the following JSON structure:
{
  "headline": "{headline}",
  "summary": "[Provide your summary here]",
  "keywords": [
    "[keyword 1]",
    "[keyword 2]",
    "[keyword 3]"
    // Add more keywords if needed
  ]
}

**Example:**  
{
  "headline": "Federal Reserve Holds Interest Rates Steady Amid Stable Growth",
  "summary": "The Federal Reserve decided to keep interest rates unchanged, referencing stable inflation and ongoing economic growth as key factors. Most analysts expect the central bank's monetary policy to remain steady in the near future.",
  "keywords": [
    "Federal Reserve",
    "interest rates",
    "inflation",
    "economic growth",
    "monetary policy"
  ]
}
"""


app = FastAPI()


def extract_news(url: str) -> str:
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
        Headline: <headline>
        Article: <main text>
    """
    article = Article(url)
    article.download()
    article.parse()
    return json.dumps({"headline": article.title, "article": article.text.replace("\n\n", "\n")})


def get_agent(
    model: ChatOpenAI = Depends(lambda: ChatOpenAI(model="gpt-5-mini", temperature=0.1, max_tokens=1000, timeout=300)), # type: ignore
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


def hash_url(url) -> int:
    """Use SHA256 hash and take the first 8 bytes as an integer"""
    return int(hashlib.sha256(url.encode("utf-8")).hexdigest()[:16], 16)


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
    summary="Will scraped data to database.",
)
def db_scrape_url(
    query: Annotated[ScrapRequest, Depends()],
    agent: Annotated[CompiledStateGraph, Depends(get_agent)],
    db: Annotated[QdrantClient, Depends(get_db)],
) -> ScrapResponse:
    url = query.url
    hashed_url = hash_url(url)
    logger.info(f"Scraping URL: {url}. Hashed: {hashed_url}")

    # Run the agent
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": f"""
    Analyze the news article at {url} and return the result in the following JSON format:

    {{
      "headline": "[Extract the headline here]",
      "summary": "[Write a concise 2-4 sentence summary here]",
      "keywords": [
        "[keyword 1]",
        "[keyword 2]",
        "[keyword 3]"
        // Add more keywords as needed
      ]
    }}

    Instructions:
    - Ensure all fields are present in the JSON, even if information is missing or must be left blank.
    - The summary must be objective and factual.
    - Provide 3-7 keywords reflecting the main topics.
    """.strip(),
                }
            ]
        }
    )
    messages = [message.content for message in result["messages"] if message.content]
    article = json.loads(result["messages"][-2].content)
    summary = json.loads(result["messages"][-1].content)
    logger.info(f"Article: {article}")
    logger.info(f"Summary: {summary}")
    db.add(
        collection_name="news_articles",
        documents=[summary["summary"]],
        metadata=[
            {
                "headline": article["headline"],
                "text": article["article"],
                "summary": summary["summary"],
                "keywords": ", ".join(summary["keywords"]),
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
