from pydantic import BaseModel, Field


class DBResponse(BaseModel):
    """
    Model for a response with scraped data from a given URL.
    """

    url: str | None = Field(
        default=None,
        description="The URL from which data were be scraped.",
        examples=["https://example.com"],
    )
    text: str | None = Field(
        default=None,
        description="Data scraped from url",
        examples=["Some text"],
    )
    job: str | None = Field(
        default=None,
        description="The job that was done.",
        examples=["saved_to_db", "read_from_db"],
    )
