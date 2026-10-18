
"""Shared test configuration.

Every test runs under a socket guard: non-loopback connections raise. This is
the Guide 11.4 requirement for non-setup tests. It does not replace an isolated
network capture; it makes an accidental external call fail loudly in CI.
"""
from __future__ import annotations

import ipaddress
import socket
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND = REPO_ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

ALLOWED_HOSTS = {"127.0.0.1", "::1", "localhost"}


@pytest.fixture(autouse=True)
def block_external_network(monkeypatch: pytest.MonkeyPatch):
    real_connect = socket.socket.connect

    def guarded(self, address):  # type: ignore[no-untyped-def]
        if self.family in (socket.AF_INET, socket.AF_INET6):
            host = address[0]
            if host not in ALLOWED_HOSTS:
                try:
                    is_loopback = ipaddress.ip_address(host).is_loopback
                except ValueError:
                    is_loopback = False
                if not is_loopback:
                    raise RuntimeError(f"non-loopback connection blocked in tests: {host}")
        return real_connect(self, address)

    monkeypatch.setattr(socket.socket, "connect", guarded)


@pytest.fixture
def repo_root() -> Path:
    return REPO_ROOT


SAMPLE_PAGE = (
    "1. Parties\n"
    "This Agreement is made between the Lessor and the Lessee. "
    "The Lessor owns the flat.\n"
    "2. Rent\n"
    "Rs. 25,000/- is payable by the 5th of each month.\n"
    "3. Notice\n"
    "The Tenant shall give sixty (60) days' written notice before termination.\n"
)


@pytest.fixture
def sample_page() -> str:
    return SAMPLE_PAGE
