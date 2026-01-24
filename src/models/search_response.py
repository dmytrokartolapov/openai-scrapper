from pydantic import BaseModel, Field


class SearchResponse(BaseModel):
    """
    Model for a response with scraped data from a given URL.
    """

    text: str | None = Field(
        default=None,
        description="The query to semantic search for.",
        examples=["Chinese cuisine in the UK"],
    )
    payload: list  = Field(
        default=[],
        description="Result of semantic search",
        examples=[["Headline: *** \n Summary: *** \n Keywords: ***"]],
    )
    job: str | None = Field(
        default=None,
        description="The job that was done.",
        examples=["saved_to_db", "read_from_db"],
    )
