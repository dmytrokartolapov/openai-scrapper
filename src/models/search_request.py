from pydantic import BaseModel, Field, field_validator


class SearchRequest(BaseModel):
    """
    Model for a request to make semantic search in DB.
    """

    text: str = Field(
        default="",
        description="The query to semantic search for.",
        examples=["Chinese cuisine in the UK"],
    )
    limit: int | str = Field(
        default=5,
        description="The maximum number of results to return.",
        examples=[1, 2, 3, 4, 5],
    )

    @field_validator("limit")
    @classmethod
    def validate_limit(cls, value):
        value = int(value)

        if value < 1:
            raise ValueError("Limit must be greater than 0.")

        return value
