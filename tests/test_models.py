"""Tests for models."""

import pytest
from pydantic import ValidationError

from models import URLCreate, URLInDB, URLResponse


class TestURLCreate:
    def test_valid_url(self):
        url = "https://example.com/path?query=value"
        model = URLCreate(url=url)
        assert str(model.url) == url

    def test_valid_url_without_scheme_raises(self):
        with pytest.raises(ValidationError):
            URLCreate(url="example.com")

    def test_invalid_url_raises(self):
        with pytest.raises(ValidationError):
            URLCreate(url="not-a-url")

    def test_ftp_url_raises(self):
        with pytest.raises(ValidationError):
            URLCreate(url="ftp://example.com")


class TestURLResponse:
    def test_creation(self):
        resp = URLResponse(codigo="abc123", url_curta="http://localhost:8000/abc123")
        assert resp.codigo == "abc123"
        assert resp.url_curta == "http://localhost:8000/abc123"


class TestURLInDB:
    def test_creation(self):
        db = URLInDB(codigo="abc123", url_original="https://example.com")
        assert db.codigo == "abc123"
        assert db.url_original == "https://example.com"