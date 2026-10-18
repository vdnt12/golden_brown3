
import pytest

from app.agent.router import RouteDecision, merge_route, pre_route
from app.core.enums import Route
from app.schemas.model_io import RouterProposal

LEGAL_PARAPHRASES = [
    "Is this enforceable?",
    "Will this hold up in court?",
    "Can they throw me out legally?",
    "Can I sue?",
    "Is this allowed by law?",
    "Is this agreement valid?",
    "What does the law say about deposits?",
]


@pytest.mark.parametrize("question", LEGAL_PARAPHRASES)
def test_legal_paraphrases_route_to_limitation(question: str):
    assert pre_route(question).route is Route.LEGAL_CONCLUSION


def test_term_question_routes_to_glossary():
    assert pre_route("What does lock-in mean?").route is Route.TERM_EXPLANATION


def test_long_question_is_out_of_scope():
    assert pre_route("x" * 501).route is Route.OUT_OF_SCOPE


def test_merge_never_downgrades_a_legal_limitation():
    decision = pre_route("Is this enforceable?")
    proposal = RouterProposal(proposed_route="FACT_LOOKUP", topics=["notice"])
    merged = merge_route(decision, proposal)
    assert merged.route is Route.LEGAL_CONCLUSION


def test_merge_accepts_a_stricter_model_proposal():
    decision = RouteDecision(Route.FACT_LOOKUP, "default", confident=False)
    proposal = RouterProposal(proposed_route="LEGAL_CONCLUSION", topics=[])
    merged = merge_route(decision, proposal)
    assert merged.route is Route.LEGAL_CONCLUSION
