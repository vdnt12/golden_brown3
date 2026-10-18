
"""ModelAnswer -> deterministic validation -> accepted points (Guide 9.1).

Runs inside the backend after every model answer. Rejected points are dropped
(fail closed); they are never repaired by the model in the same validation
attempt except through the single format-retry path owned by the provider.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.schemas.model_io import ModelAnswer, ModelPoint
from app.validation.claim_support import Violation, check_point
from app.validation.provenance import Evidence, ProvenanceRegistry, UnknownSidError


@dataclass
class ValidationOutcome:
    accepted: list[ModelPoint] = field(default_factory=list)
    rejected: list[tuple[ModelPoint, list[Violation]]] = field(default_factory=list)
    evidence: dict[str, list[Evidence]] = field(default_factory=dict)
    codes: list[str] = field(default_factory=list)
    # How many points the model returned, accepted or not. Zero is a valid
    # "nothing supported" reply and must not be confused with rejected content.
    returned: int = 0

    @property
    def all_rejected(self) -> bool:
        return not self.accepted


def validate_model_answer(
    answer: ModelAnswer,
    registry: ProvenanceRegistry,
) -> ValidationOutcome:
    outcome = ValidationOutcome(returned=len(answer.points))
    exposed = set(registry.all_sids())

    for point in answer.points:
        try:
            evidence = registry.evidence_for(point.sids) if point.sids else []
        except UnknownSidError as exc:
            outcome.rejected.append(
                (
                    point,
                    [Violation("SID_NOT_EXPOSED_IN_RUN", point.point_id, str(exc))],
                )
            )
            outcome.codes.append("SID_NOT_EXPOSED_IN_RUN")
            continue

        violations = check_point(point, evidence, exposed)
        if violations:
            outcome.rejected.append((point, violations))
            outcome.codes.extend(v.code for v in violations)
        else:
            outcome.accepted.append(point)
            outcome.evidence[point.point_id] = evidence

    return outcome
