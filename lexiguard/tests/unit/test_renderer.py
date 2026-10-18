
from app.core.enums import PointKind, ResponseStatus
from app.schemas.model_io import ModelPoint
from app.validation.provenance import Evidence
from app.validation.renderer import build_rendered_answer, render_claim

EVIDENCE = Evidence(sid="s_0001", page=2, section="3", quote="The Tenant shall pay the rent.", document_sha256="b" * 64)


def test_render_claim_attaches_backend_owned_quote():
    point = ModelPoint(point_id="p1", kind=PointKind.RESTATEMENT, text="The tenant pays rent.", sids=["s_0001"])
    claim = render_claim(point, [EVIDENCE], 1, document_sha256="b" * 64)
    assert claim.evidence[0].quote == "The Tenant shall pay the rent."
    assert claim.evidence[0].page == 2
    assert claim.evidence[0].document_sha256 == "b" * 64


def test_rendered_answer_replaces_verdict_text_and_sets_legal_limit():
    answer = build_rendered_answer(
        statuses=[ResponseStatus.ANSWERED],
        answer="This clause is unenforceable.",
    )
    assert answer.status is ResponseStatus.LEGAL_LIMIT
    assert "qualified lawyer" in answer.answer
    assert answer.legal_verdict is None


def test_status_precedence_applies_in_renderer():
    answer = build_rendered_answer(
        statuses=[ResponseStatus.ANSWERED, ResponseStatus.CONFLICTING],
        answer="Two clauses differ.",
    )
    assert answer.status is ResponseStatus.CONFLICTING
