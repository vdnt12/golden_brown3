
"""Run budget: counters that make the hard ceilings executable (Guide 8.3/8.3a).

The runtime must call these methods before every tool or model action; exceeding
a cap raises BudgetExceeded and the caller fails closed.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import StrEnum


class BudgetKind(StrEnum):
    TOOL = "TOOL_CALL"
    MODEL = "MODEL_CALL"
    RETRIEVAL_LOOP = "RETRIEVAL_LOOP"


class BudgetExceeded(RuntimeError):
    def __init__(self, kind: BudgetKind, limit: int) -> None:
        super().__init__(f"{kind} budget exceeded (limit={limit})")
        self.kind = kind
        self.limit = limit


@dataclass
class RunBudget:
    max_tool_calls: int = 8
    max_model_calls: int = 4
    max_retrieval_loops: int = 2
    wall_clock_s: float | None = None
    started_at: float = field(default_factory=time.monotonic)
    tool_calls: int = 0
    model_calls: int = 0
    retrieval_loops: int = 0

    def _bump(self, kind: BudgetKind) -> None:
        if kind is BudgetKind.TOOL:
            if self.tool_calls + 1 > self.max_tool_calls:
                raise BudgetExceeded(kind, self.max_tool_calls)
            self.tool_calls += 1
        elif kind is BudgetKind.MODEL:
            if self.model_calls + 1 > self.max_model_calls:
                raise BudgetExceeded(kind, self.max_model_calls)
            self.model_calls += 1
        else:
            if self.retrieval_loops + 1 > self.max_retrieval_loops:
                raise BudgetExceeded(kind, self.max_retrieval_loops)
            self.retrieval_loops += 1

    def spend_tool_call(self) -> None:
        self._bump(BudgetKind.TOOL)

    def spend_model_call(self) -> None:
        self._bump(BudgetKind.MODEL)

    def spend_retrieval_loop(self) -> None:
        self._bump(BudgetKind.RETRIEVAL_LOOP)

    def elapsed_s(self) -> float:
        return time.monotonic() - self.started_at

    def deadline_exceeded(self) -> bool:
        return self.wall_clock_s is not None and self.elapsed_s() > self.wall_clock_s

    def assert_deadline(self) -> None:
        if self.deadline_exceeded():
            raise TimeoutError("per-question wall-clock budget exhausted")

    def half_budget_spent(self) -> bool:
        """Used to skip the optional refinement call (Guide 8.3a)."""
        return self.wall_clock_s is not None and self.elapsed_s() > (self.wall_clock_s / 2)
