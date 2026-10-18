
import pytest

from app.core.limits import BudgetExceeded, BudgetKind, RunBudget
from app.core.textmetrics import estimate_tokens, fits_context
from app.services.benchmark import summarise_latencies


def test_tool_call_ceiling():
    budget = RunBudget(max_tool_calls=2)
    budget.spend_tool_call()
    budget.spend_tool_call()
    with pytest.raises(BudgetExceeded) as excinfo:
        budget.spend_tool_call()
    assert excinfo.value.kind is BudgetKind.TOOL


def test_model_call_ceiling_is_four():
    budget = RunBudget(max_model_calls=4)
    for _ in range(4):
        budget.spend_model_call()
    with pytest.raises(BudgetExceeded):
        budget.spend_model_call()


def test_token_estimate_is_conservative():
    assert estimate_tokens("abcd") == 2
    assert fits_context(prompt_tokens=3000, output_tokens=300, num_ctx=8192)
    assert not fits_context(prompt_tokens=8000, output_tokens=300, num_ctx=8192)


def test_latency_summary():
    summary = summarise_latencies([1.0, 2.0, 3.0, 4.0])
    assert summary.count == 4
    assert summary.min_s == 1.0 and summary.max_s == 4.0
