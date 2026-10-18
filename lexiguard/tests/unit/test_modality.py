
from app.validation.modality import check_modality


def test_must_and_shall_are_treated_as_the_same_obligation():
    assert check_modality(
        "The tenant must give sixty days notice.",
        ["The Tenant shall give sixty (60) days notice."],
    ) == []


def test_permission_cannot_weaken_an_obligation():
    codes = [v.code for v in check_modality(
        "The tenant may terminate with thirty days notice.",
        ["The Tenant shall provide sixty (60) days' written notice before termination."],
    )]
    assert "MODALITY_WEAKENED" in codes


def test_negation_cannot_be_dropped():
    codes = [v.code for v in check_modality(
        "The tenant shall sublet the premises.",
        ["The Tenant shall not sublet the premises."],
    )]
    assert "NEGATION_DROPPED" in codes


def test_negation_cannot_be_added():
    codes = [v.code for v in check_modality(
        "The tenant may not keep pets.",
        ["The Tenant may keep pets with consent."],
    )]
    assert "NEGATION_ADDED" in codes
