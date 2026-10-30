"""Storage layer for URL shortener - JSON file with atomic writes."""

import json
import os
import tempfile
import threading
from pathlib import Path
from typing import Any

# Simple thread lock for cross-platform safety
_lock = threading.Lock()

DB_PATH = Path("urls.json")


def _read_db() -> dict[str, Any]:
    """Read the JSON database."""
    if not DB_PATH.exists():
        return {}
    with _lock, open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)  # type: ignore[no-any-return]


def _write_db_atomic(data: dict[str, Any]) -> None:
    """Write database atomically using temp file + rename."""
    with _lock:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=DB_PATH.parent,
            delete=False,
            suffix=".tmp"
        ) as tmp:
            json.dump(data, tmp, ensure_ascii=False, indent=2)
            tmp_path = Path(tmp.name)
        os.replace(tmp_path, DB_PATH)


def save_url(code: str, url: str) -> None:
    """Save a URL mapping to the database."""
    data = _read_db()
    data[code] = url
    _write_db_atomic(data)


def get_url(code: str) -> str | None:
    """Retrieve a URL by its short code."""
    data = _read_db()
    return data.get(code)