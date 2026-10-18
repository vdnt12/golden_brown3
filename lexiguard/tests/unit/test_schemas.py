
import pytest
from pydantic import ValidationError

from app.schemas.model_io import ModelAnswer, ModelPoint, NextAction, RouterProposal
from app.schemas.response import Claim, EvidenceItem, RenderedAnswer


def test_model_answer_rejects_unknown_policy_fields():
    payload = {
        "points": [
            {
                "point_id": "p1",
                "kind": "RESTATEMENT",
                "text": "The tenant must give sixty days' notice.",
                "sids": ["s_0001"],
                "page": 7,
            }
        ]
    }
    with pytest.raises(ValidationError):
        ModelAnswer.model_validate(payload)


def test_model_answer_rejects_duplicate_point_ids():
    point = {"point_id": "p1", "kind": "STATED", "text": "x", "sids": ["s_0001"]}
    with pytest.raises(ValidationError):
        ModelAnswer.model_validate({"points": [point, point]})


def test_general_explanation_must_not_cite_sids():
    with pytest.raises(ValidationError):
        ModelPoint(point_id="p1", kind="GENERAL_EXPLANATION", text="A deposit is money.", sids=["s_0001"])


def test_next_action_requires_action_specific_fields():
    with pytest.raises(ValidationError):
        NextAction(action="GET_PAGE")
    with pytest.raises(ValidationError):
        NextAction(action="SEARCH", query="x" * 121)
    action = NextAction(action="SEARCH", query="notice period", topic="notice")
    assert action.action == "SEARCH"


def test_router_proposal_rejects_unknown_route():
    with pytest.raises(ValidationError):
        RouterProposal(proposed_route="MAKE_IT_UP", topics=[], needs_clarification=False)


def test_rendered_answer_legal_verdict_is_always_null():
    evidence = EvidenceItem(sid="s_0001", page=1, quote="The Tenant shall pay rent.")
    claim = Claim(claim_id="claim_001", text="Rent is payable.", classification="SUPPORTED", evidence=[evidence])
    answer = RenderedAnswer(status="ANSWERED", answer="Rent is payable.", claims=[claim])
    assert answer.legal_verdict is None
    with pytest.raises(ValidationError):
        RenderedAnswer(status="ANSWERED", answer="x", legal_verdict="valid")
