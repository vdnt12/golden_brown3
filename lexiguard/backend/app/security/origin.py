
"""Origin checking for state-changing requests (Guide 11.3)."""
from __future__ import annotations

from app.config import Settings


def is_allowed_origin(origin: str | None, settings: Settings) -> bool:
    """Absent Origin is allowed (same-origin navigations / non-browser tools).

    When an Origin header is present it must match exactly. There is no wildcard
    CORS on the app at all.
    """
    if origin is None:
        return True
    return origin.strip().lower() in {o.lower() for o in settings.allowed_origins()}
