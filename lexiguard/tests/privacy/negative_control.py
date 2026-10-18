
#!/usr/bin/env python3
"""Negative control for the isolated-network audit (Guide 11.4).

Run INSIDE the isolated environment. It deliberately attempts a connection to a
documentation-range address. The audit instrument must record this attempt. If
the control is not detected, the report is invalid: an empty capture proves
nothing on its own.
"""
from __future__ import annotations

import socket

TARGET = ("192.0.2.1", 443)  # TEST-NET-1, non-routable documentation range


def main() -> int:
    print(f"Negative control: attempting TCP connect to {TARGET[0]}:{TARGET[1]}")
    try:
        with socket.create_connection(TARGET, timeout=3):
            print("UNEXPECTED: connection succeeded (environment is not isolated)")
            return 1
    except OSError as exc:
        print(f"Control attempt made and failed as expected: {exc}")
        print("Verify the audit capture recorded this attempt. If it did not, the capture is invalid.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
