
"""Security headers and the CSP baseline (Guide 11.2).

All fonts, icons and scripts are bundled; no CDN, no inline script or style.
"""
from __future__ import annotations

CSP_BASELINE = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self'; "
    "connect-src 'self'; "
    "img-src 'self' blob: data:; "
    "font-src 'self'; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "frame-ancestors 'none'"
)


def security_headers() -> dict[str, str]:
    return {
        "Content-Security-Policy": CSP_BASELINE,
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer",
        "X-Frame-Options": "DENY",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=(), interest-cohort=()",
    }


def no_store_headers() -> dict[str, str]:
    return {
        "Cache-Control": "no-store",
        "Pragma": "no-cache",
        "Expires": "0",
    }
