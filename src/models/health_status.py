from pydantic import BaseModel


class HealthStatus(BaseModel):
    """Model for health check."""

    status: str
