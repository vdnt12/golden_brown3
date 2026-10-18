
#!/usr/bin/env python3
"""Retrieval benchmark seam (Phase 3/6).

Runs the committed question set against a parsed document and reports lexical
hit/baseline statistics. Not implemented in this build; exits non-zero rather
than printing invented metrics.
"""
from __future__ import annotations

import sys


def main() -> int:
    print(
        "Retrieval benchmarking is not implemented in this build.\n"
        "Phase 3 builds app/retrieval; Phase 6 wires this script to the question set "
        "and writes real results to docs/EVALUATION.md.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
