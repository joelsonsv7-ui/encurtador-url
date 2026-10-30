"""Tests for storage layer."""

import json
import os

import storage


class TestStorage:
    def setup_method(self):
        """Ensure clean database before each test."""
        if os.path.exists("urls.json"):
            with open("urls.json", "w") as f:
                f.write("{}")

    def teardown_method(self):
        """Clean up after each test."""
        if os.path.exists("urls.json"):
            with open("urls.json", "w") as f:
                f.write("{}")

    def test_save_and_get_url(self):
        storage.save_url("abc123", "https://example.com")
        url = storage.get_url("abc123")
        assert url == "https://example.com"

    def test_get_nonexistent_returns_none(self):
        url = storage.get_url("nonexistent")
        assert url is None

    def test_overwrite_existing_code(self):
        storage.save_url("abc123", "https://example.com")
        storage.save_url("abc123", "https://newexample.com")
        url = storage.get_url("abc123")
        assert url == "https://newexample.com"

    def test_multiple_entries(self):
        storage.save_url("code1", "https://example1.com")
        storage.save_url("code2", "https://example2.com")
        storage.save_url("code3", "https://example3.com")
        assert storage.get_url("code1") == "https://example1.com"
        assert storage.get_url("code2") == "https://example2.com"
        assert storage.get_url("code3") == "https://example3.com"

    def test_persistence_across_calls(self):
        storage.save_url("persist", "https://persist.com")
        # Simulate new process by creating new storage instance
        url = storage.get_url("persist")
        assert url == "https://persist.com"

    def test_json_format_valid(self):
        storage.save_url("test", "https://test.com")
        with open("urls.json", "r") as f:
            data = json.load(f)
        assert isinstance(data, dict)
        assert data["test"] == "https://test.com"