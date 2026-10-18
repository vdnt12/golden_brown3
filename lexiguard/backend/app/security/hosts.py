
"""Exact Host allow-listing (DNS-rebinding defence, Guide 11.3).

Only 127.0.0.1:<port> and localhost:<port> for the configured port are valid.
No wildcard, no suffix matching, no X-Forwarded-Host trust.
"""
from __future__ import annotations

from app.config import Settings


def allowed_hosts(settings: Settings) -> set[str]:
    return settings.allowed_hosts()


def is_allowed_host(host_header: str | None, settings: Settings) -> bool:
    if not host_header:
        return False
    host = host_header.strip().lower()
    # Strip a trailing dot on the hostname part ("localhost.:8765").
    if ":" in host:
        name, _, port = host.rpartition(":")
        host = f"{name.rstrip('.')}:{port}"
    else:
        host = host.rstrip(".")
    return host in settings.allowed_hosts()
