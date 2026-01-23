from datetime import datetime
from typing import Annotated

from fastapi import FastAPI, status, Depends, Request
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from newspaper import Article
from pydantic import ValidationError
from starlette.responses import JSONResponse


from src.logger import setup_logger
from src.models.db_response import DBResponse
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

**Output Format:**  
- **Summary:**  
  [Provide your summary here]

- **Keywords:**  
  - [keyword 1]  
  - [keyword 2]  
  - [keyword 3]  
  - ...  

**Example:**  
- **Summary:**  
  The Federal Reserve announced it will keep interest rates unchanged, citing stable inflation and economic growth. Market reactions were muted, with analysts anticipating no major changes in policy soon.

- **Keywords:**  
  - Federal Reserve  
  - interest rates  
  - economic growth  
  - inflation  
  - monetary policy
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
    return f"Headline: {article.title}\nArticle: {article.text}".replace("\n\n", "\n")


def get_agent(
    model: ChatOpenAI = Depends(lambda: ChatOpenAI(model="gpt-5", temperature=0.1, max_tokens=1000, timeout=300)),
    tools: list = Depends(lambda: [extract_news]),
    system_prompt: str = Depends(lambda: SYSTEM_PROMPT),
):
    return create_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
    )


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
    request: Request,
    query: Annotated[ScrapRequest, Depends()],
    agent=Depends(get_agent),
) -> ScrapResponse:
    url = query.url
    logger.info(f"Scraping URL: {url}")

    # Run the agent
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": f"Make the summary for {url}",
                }
            ]
        }
    )
    messages = [message.content for message in result["messages"] if message.content]
    return ScrapResponse(url=url, messages=messages, job="saved_to_db")


@app.get(
    "/v1/db/read_db",
    status_code=status.HTTP_200_OK,
    tags=["read_db"],
    summary="Reads scraped data from database.",
)
async def db_read(
    request: Request,
    query: Annotated[ScrapRequest, Depends()],
) -> DBResponse:
    url = query.url
    return DBResponse(url=url, text="test value", job="read_from_db")
