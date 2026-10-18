
"""Role canonicalisation and the T-CITE-ROLE-01 check (Guide 9.1 stage 4).

tenant / lessee / licensee / occupant -> TENANT
landlord / lessor / licensor / owner     -> LANDLORD

A role named in a restatement must occur in the cited sentences. Swapped or
invented parties drop the point. This is a lexical check, not semantic proof.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

ROLE_CANON: dict[str, str] = {
    "tenant": "TENANT",
    "tenants": "TENANT",
    "lessee": "TENANT",
    "lessees": "TENANT",
    "licensee": "TENANT",
    "licensees": "TENANT",
    "licencee": "TENANT",
    "licencees": "TENANT",
    "occupant": "TENANT",
    "occupants": "TENANT",
    "renter": "TENANT",
    "renters": "TENANT",
    "landlord": "LANDLORD",
    "landlords": "LANDLORD",
    "landlady": "LANDLORD",
    "lessor": "LANDLORD",
    "lessors": "LANDLORD",
    "licensor": "LANDLORD",
    "licensors": "LANDLORD",
    "owner": "LANDLORD",
    "owners": "LANDLORD",
}

CODE_ROLE_NOT_IN_SOURCE = "ROLE_NOT_IN_SOURCE"


@dataclass(frozen=True)
class RoleViolation:
    code: str
    role: str


_WORD_RE = re.compile(r"[A-Za-z]+")


def roles_in(text: str) -> set[str]:
    found: set[str] = set()
    for word in _WORD_RE.findall(text.lower()):
        role = ROLE_CANON.get(word)
        if role:
            found.add(role)
    return found


def check_roles(claim_text: str, source_texts: list[str]) -> list[RoleViolation]:
    claim_roles = roles_in(claim_text)
    source_roles = set()
    for source in source_texts:
        source_roles |= roles_in(source)
    return [
        RoleViolation(code=CODE_ROLE_NOT_IN_SOURCE, role=role)
        for role in sorted(claim_roles - source_roles)
    ]
