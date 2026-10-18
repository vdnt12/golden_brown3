
"""Latency helpers for the Day-0 gate and the E2B-vs-E4B benchmark (Guide 15.1).

No numbers are produced at import time; these functions only summarise real
measurements recorded by scripts/benchmark_model.py.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LatencySummary:
    count: int
    p50_s: float
    p95_s: float
    min_s: float
    max_s: float


def _percentile(sorted_values: list[float], fraction: float) -> float:
    if not sorted_values:
        raise ValueError("no measurements")
    if len(sorted_values) == 1:
        return sorted_values[0]
    index = round((len(sorted_values) - 1) * fraction)
    return sorted_values[index]


def summarise_latencies(latencies_s: list[float]) -> LatencySummary:
    values = sorted(latencies_s)
    if not values:
        raise ValueError("no measurements")
    return LatencySummary(
        count=len(values),
        p50_s=_percentile(values, 0.50),
        p95_s=_percentile(values, 0.95),
        min_s=values[0],
        max_s=values[-1],
    )
