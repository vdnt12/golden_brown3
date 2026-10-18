
import pytest

from app.core.enums import PointKind
from app.schemas.model_io import ModelAnswer, ModelPoint
from app.validation.pipeline import validate_model_answer
from app.validation.provenance import Evidence, ProvenanceRegistry, UnknownSidError


def registry() -> ProvenanceRegistry:
    reg = ProvenanceRegistry("doc-1", "a" * 64)
    reg.register(
        [
            Evidence(
                sid="s_0001",
                page=3,
                section="4",
                quote="The Tenant shall give sixty (60) days' written notice before termination.",
            ),
            Evidence(
                sid="s_0002",
                page=5,
                section="9",
                quote="The Tenant shall give thirty (30) days' notice for early exit.",
            ),
        ]
    )
    return reg


def make_point(**overrides) -> ModelPoint:
    payload = {
        "point_id": "p1",
        "kind": "RESTATEMENT",
        "text": "The tenant must give sixty (60) days' written notice before termination.",
        "sids": ["s_0001"],
    }
    payload.update(overrides)
    return ModelPoint(**payload)


def test_valid_restatement_is_accepted():
    outcome = validate_model_answer(ModelAnswer(points=[make_point()]), registry())
    assert [p.point_id for p in outcome.accepted] == ["p1"]


def test_forged_sid_is_rejected():
    outcome = validate_model_answer(
        ModelAnswer(points=[make_point(sids=["s_9999"])]), registry()
    )
    assert outcome.accepted == []
    assert "SID_NOT_EXPOSED_IN_RUN" in outcome.codes


def test_role_swap_is_rejected():
    point = make_point(text="The landlord must give sixty (60) days' written notice before termination.")
    outcome = validate_model_answer(ModelAnswer(points=[point]), registry())
    assert outcome.accepted == []
    assert any(code.startswith("ROLE_") for code in outcome.codes)


def test_invented_amount_is_rejected():
    point = make_point(text="The tenant must give sixty (60) days' notice and pay Rs. 30,000.")
    outcome = validate_model_answer(ModelAnswer(points=[point]), registry())
    assert outcome.accepted == []
    assert "LITERAL_NOT_IN_SOURCE" in outcome.codes


def test_conflict_point_needs_two_sections():
    reg = registry()
    point = ModelPoint(
        point_id="p1",
        kind=PointKind.CONFLICT,
        text="Notice periods differ across sections.",
        sids=["s_0001"],
    )
    outcome = validate_model_answer(ModelAnswer(points=[point]), reg)
    assert outcome.accepted == []
    assert "CONFLICT_NEEDS_TWO_SECTIONS" in outcome.codes


def test_unknown_sid_raises_in_registry():
    with pytest.raises(UnknownSidError):
        registry().evidence_for(["s_0007"])
