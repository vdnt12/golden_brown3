
from app.core.enums import ResponseStatus, resolve_status


def test_status_precedence_legal_beats_conflict():
    assert (
        resolve_status([ResponseStatus.CONFLICTING, ResponseStatus.LEGAL_LIMIT])
        is ResponseStatus.LEGAL_LIMIT
    )


def test_status_precedence_insufficient_beats_not_located():
    assert (
        resolve_status([ResponseStatus.NOT_LOCATED, ResponseStatus.INSUFFICIENT_EVIDENCE])
        is ResponseStatus.INSUFFICIENT_EVIDENCE
    )


def test_status_precedence_out_of_scope_above_answered():
    assert (
        resolve_status([ResponseStatus.OUT_OF_SCOPE, ResponseStatus.ANSWERED])
        is ResponseStatus.OUT_OF_SCOPE
    )


def test_error_beats_everything():
    assert (
        resolve_status(
            [ResponseStatus.LEGAL_LIMIT, ResponseStatus.ERROR_LOCAL_MODEL_UNAVAILABLE]
        )
        is ResponseStatus.ERROR_LOCAL_MODEL_UNAVAILABLE
    )


def test_empty_status_set_is_a_caller_error():
    import pytest

    with pytest.raises(ValueError):
        resolve_status([])
