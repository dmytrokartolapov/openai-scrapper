from datetime import datetime
from typing import Annotated

from fastapi import FastAPI, status, Depends, Request
from pydantic import ValidationError
from starlette.responses import JSONResponse


from src.logger import setup_logger
from src.models.health_status import HealthStatus
from src.models.scrap_request import ScrapRequest
from src.models.scrap_response import ScrapResponse

logger = setup_logger()
app = FastAPI()


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
    tags=["scrapping"],
    summary="Will scraped data to database.",
)
async def db_scrape_url(
    request: Request,
    query: Annotated[ScrapRequest, Depends()],
) -> ScrapResponse:
    url = query.url
    return ScrapResponse(
        url=url,
        text="test value",
        job="saved_to_db"
    )


@app.get(
    "/v1/db/read_db",
    status_code=status.HTTP_200_OK,
    tags=["scrapping"],
    summary="Reads scraped data from database.",
)
async def db_scrape_url(
    request: Request,
    query: Annotated[ScrapRequest, Depends()],
) -> ScrapResponse:
    url = query.url
    return ScrapResponse(
        url=url,
        text="test value",
        job="read_from_db"
    )