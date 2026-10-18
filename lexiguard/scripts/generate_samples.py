#!/usr/bin/env python3
"""Regenerate reports/samples/*.json from the real service layer.

The payloads are produced by the same functions the HTTP API calls, so they
show the wire contract rather than a hand-written illustration. A scripted
provider supplies the model output; it is not a language model.

    python3 scripts/generate_samples.py
"""
from __future__ import annotations

import json
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "backend"))

from app.config import Settings  # noqa: E402
from app.ingest.pipeline import ingest_document  # noqa: E402
from app.schemas.model_io import ModelAnswer  # noqa: E402
from app.services.answer import answer_question  # noqa: E402
from app.services.overview import build_overview  # noqa: E402
from app.services.review import build_review  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "synthetic_rental_conflict.txt"
OUT = ROOT / "reports" / "samples"


class SilentProvider:
    """A model that answers with no points at all. Not a language model."""

    name = "scripted-silent"
    model_tag = "scripted"

    def answer_from_evidence(self, *, messages):
        return ModelAnswer(points=[])

    def unload(self):
        return True


def dump(name: str, payload) -> None:
    data = payload.model_dump(mode="json") if hasattr(payload, "model_dump") else payload
    (OUT / name).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        settings = Settings(data_dir=pathlib.Path(tmp))
        result = ingest_document(
            filename=FIXTURE.name, data=FIXTURE.read_bytes(), settings=settings
        )
        overview = build_overview(settings, result.document_id)
        review = build_review(settings, result.document_id)
        answer = answer_question(
            settings,
            result.document_id,
            "What is the monthly rent?",
            provider=SilentProvider(),
            model_tag="scripted",
        )
        dump("overview_conflict.json", overview)
        dump("review_conflict.json", review)
        dump("ask_conflict_silent_model.json", answer)
        print("overview cards:", len(overview.cards))
        print("review items:", len(review.attention_first), review.review_status)
        print("answer:", answer.status.value, len(answer.claims), "claims")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
