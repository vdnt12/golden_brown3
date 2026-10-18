
"""Launcher: prints the one-time launch URL and runs the API on loopback.

Usage:
    python -m app            # from backend/
    lexiguard                # after `pip install -e .`

The URL fragment (#k=...) carries the one-time code. It is never sent in an
HTTP request and never logged; the SPA strips it immediately.
"""
from __future__ import annotations

import uvicorn

from app.config import get_settings
from app.main import create_app


def main() -> None:
    settings = get_settings()
    app = create_app(settings)
    url = f"http://127.0.0.1:{settings.port}/#k={app.state.launch_code}"
    print("GBDoc starting on loopback only (127.0.0.1).", flush=True)
    print(f"Open this one-time URL in your browser: {url}", flush=True)
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level="info",
        access_log=False,  # request paths can carry document IDs; keep logs content-free
    )


if __name__ == "__main__":
    main()
