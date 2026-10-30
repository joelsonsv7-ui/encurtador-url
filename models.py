"""Models for the URL shortener API."""

from pydantic import BaseModel, HttpUrl


class URLCreate(BaseModel):
    """Input model for creating a short URL."""
    url: HttpUrl


class URLResponse(BaseModel):
    """Output model for successful URL creation."""
    codigo: str
    url_curta: str


class URLInDB(BaseModel):
    """Internal model for stored URL mapping."""
    codigo: str
    url_original: str