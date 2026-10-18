
from app.validation.roles import check_roles, roles_in


def test_role_words_canonicalise():
    assert roles_in("The lessee and the licensor") == {"TENANT", "LANDLORD"}
    assert roles_in("The owner and the occupant") == {"TENANT", "LANDLORD"}


def test_swapped_party_is_detected():
    violations = check_roles(
        "The landlord must give sixty days notice.",
        ["The Tenant shall give sixty (60) days' written notice."],
    )
    assert [v.role for v in violations] == ["LANDLORD"]


def test_same_party_passes():
    assert check_roles(
        "The tenant must give sixty days notice.",
        ["The Tenant shall give sixty (60) days' written notice."],
    ) == []
