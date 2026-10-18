
"""One-time launch codes and in-memory session tokens (Guide 11.3).

The served HTML never contains a secret. The launcher prints a URL with a
fragment (#k=<code>); the SPA exchanges the single-use code for a bearer token
held in JS memory only. Codes expire quickly (default 60 s) and cannot be
replayed. Tokens die with the process.
"""
from __future__ import annotations

import hmac
import secrets
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class Session:
    token: str
    expires_at: float


class LaunchSessionStore:
    def __init__(
        self,
        *,
        clock: Callable[[], float] = time.time,
        code_ttl_s: float = 60.0,
        session_ttl_s: float = 8 * 60 * 60,
    ) -> None:
        self._clock = clock
        self._code_ttl_s = code_ttl_s
        self._session_ttl_s = session_ttl_s
        self._codes: dict[str, float] = {}
        self._sessions: dict[str, float] = {}
        self._lock = threading.Lock()

    # -- launch codes -------------------------------------------------------
    def issue_code(self) -> str:
        code = secrets.token_urlsafe(32)
        with self._lock:
            self._purge()
            self._codes[code] = self._clock() + self._code_ttl_s
        return code

    def redeem_code(self, code: str) -> Session | None:
        """Consume a code exactly once. Returns a session or None."""
        now = self._clock()
        with self._lock:
            self._purge()
            expiry = self._codes.pop(code, None)
            if expiry is None or expiry < now:
                return None
            token = secrets.token_urlsafe(32)
            session_expiry = now + self._session_ttl_s
            self._sessions[token] = session_expiry
            return Session(token=token, expires_at=session_expiry)

    def create_direct_session(self) -> Session:
        """Create a direct session for local developer dashboard access."""
        now = self._clock()
        token = secrets.token_urlsafe(32)
        session_expiry = now + self._session_ttl_s
        with self._lock:
            self._purge()
            self._sessions[token] = session_expiry
        return Session(token=token, expires_at=session_expiry)

    # -- bearer tokens ------------------------------------------------------
    def validate(self, token: str) -> bool:
        if not token:
            return False
        now = self._clock()
        with self._lock:
            self._purge()
            for candidate, expiry in self._sessions.items():
                if expiry >= now and hmac.compare_digest(candidate, token):
                    return True
        return False

    def revoke_all(self) -> None:
        with self._lock:
            self._sessions.clear()
            self._codes.clear()

    def _purge(self) -> None:
        now = self._clock()
        self._codes = {c: e for c, e in self._codes.items() if e >= now}
        self._sessions = {t: e for t, e in self._sessions.items() if e >= now}

    @property
    def active_sessions(self) -> int:
        with self._lock:
            self._purge()
            return len(self._sessions)
