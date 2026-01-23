from urllib.parse import urlparse
from pydantic import BaseModel, Field, field_validator


class ScrapRequest(BaseModel):
    """
    Model for a request to scrape data from a given URL.
    """

    url: str | None = Field(
        default=None,
        description="The URL from which data will be scraped.",
        examples=["https://example.com"],
    )

    @field_validator("url")
    @classmethod
    def validate_url(cls, value):
        if value is None:
            return value

        result = urlparse(value)

        if not all([result.scheme, result.netloc]):
            raise ValueError("Invalid URL format.")

        return value
