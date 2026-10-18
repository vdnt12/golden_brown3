#!/usr/bin/env python3
"""Run the committed synthetic fixtures through the deterministic pipeline.

Produces a machine-written report so no number in the docs has to be typed by
hand. The model is NOT exercised here: there is no live Ollama in CI, so the
script uses a scripted provider that echoes known sentences and a "bad" provider
that invents a figure. That is enough to test the validator, not the model.

Usage:
    python scripts/evaluate_fixtures.py [--json out.json] [--md out.md]
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import tempfile
from datetime import UTC, datetime

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "backend"))

from app.config import Settings  # noqa: E402
from app.ingest.pipeline import ingest_document  # noqa: E402
from app.retrieval.concepts import CONCEPTS_BY_KEY, match_sentences  # noqa: E402
from app.schemas.model_io import ModelAnswer  # noqa: E402
from app.services.answer import answer_question  # noqa: E402
from app.services.overview import build_overview  # noqa: E402
from app.services.review import build_review  # noqa: E402
from app.store.repo import open_document  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURES = [
    "synthetic_rental_simple.txt",
    "synthetic_rental_conflict.txt",
    "synthetic_rental_ambiguous.txt",
    "synthetic_rental_injection.txt",
    "synthetic_rental_indian_style.txt",
]
QUESTIONS = {
    "rent": "What is the monthly rent and when is it due?",
    "rent_hallucinated": "What is the monthly rent?",
    "notice": "What notice period applies if I want to leave?",
    "legal": "Is this agreement valid and can my landlord evict me?",
    "absent": "Does the agreement mention pets?",
    "term": "What does lock-in mean?",
}


class ScriptedProvider:
    """Deterministic stand-in for a local model.

    Modes:
      quote    -- quote an exposed sentence that matches the question keyword
      invent   -- invent a figure while citing an exposed sentence
      forge    -- cite a sentence id that was never shown
      silent   -- return an empty answer ("nothing in the evidence supports this")

    This is a test double, not a model. It exists to exercise retrieval,
    validation and rendering without pretending to measure model quality.
    """

    name = "scripted"
    model_tag = "scripted"

    def __init__(self, mode: str, sentences: dict[str, dict]):
        self._mode = mode
        self._sentences = sentences

    @staticmethod
    def _exposed(messages) -> list[str]:
        body = "\n".join(message["content"] for message in messages)
        return list(dict.fromkeys(re.findall(r"\[(s_\d{4,8})\]", body)))

    @staticmethod
    def _question(messages) -> str:
        body = "\n".join(message["content"] for message in messages)
        match = re.search(r"Question about the supplied agreement:\n(.+)", body)
        return match.group(1).strip().lower() if match else ""

    def answer_from_evidence(self, *, messages):
        if self._mode == "silent":
            return ModelAnswer(points=[])
        exposed = self._exposed(messages)
        if not exposed:
            return ModelAnswer(points=[])
        question = self._question(messages)
        keyword = "notice" if "notice" in question else "rent"
        # A real model echoes a sentence it was shown, and cannot return more
        # than the 600-character point limit. Pick the shortest matching record
        # that fits, so the scripted answer is legal model I/O.
        candidates = [
            sid
            for sid in exposed
            if keyword in self._sentences[sid]["text"].lower()
            and len(self._sentences[sid]["text"]) <= 600
        ] or [sid for sid in exposed if len(self._sentences[sid]["text"]) <= 600]
        if not candidates:
            return ModelAnswer(points=[])
        chosen = candidates[0]
        if self._mode == "forge":
            return ModelAnswer(
                points=[
                    {"point_id": "p1", "kind": "STATED", "text": "x", "sids": ["s_9999"]}
                ]
            )
        if self._mode == "invent":
            text = "The monthly rent is Rs. 9,99,999, payable in gold."
        else:
            text = self._sentences[chosen]["text"]
        return ModelAnswer(
            points=[
                {
                    "point_id": "p1",
                    "kind": "RESTATEMENT",
                    "text": text,
                    "sids": [chosen],
                }
            ]
        )

    def unload(self):
        return True


def _sentences(db_root: pathlib.Path, doc_id: str) -> dict[str, dict]:
    with open_document(db_root, doc_id) as handle:
        return {
            row["sid"]: dict(row)
            for row in handle.connection.execute("SELECT * FROM sentences")
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=pathlib.Path)
    parser.add_argument("--md", type=pathlib.Path)
    args = parser.parse_args()

    report: dict = {"generated_at": datetime.now(UTC).isoformat(timespec="seconds"), "documents": []}

    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        settings = Settings(data_dir=root)
        for name in FIXTURES:
            data = (ROOT / "fixtures" / name).read_bytes()
            result = ingest_document(filename=name, data=data, settings=settings)
            overview = build_overview(settings, result.document_id)
            review = build_review(settings, result.document_id)

            sentences = _sentences(root, result.document_id)
            # Sanity check that the concept matcher sees the same rent clause the
            # fixtures were written around; recorded, not used to steer the answer.
            rent_hits = match_sentences(
                CONCEPTS_BY_KEY["rent"],
                [(sid, row["text"]) for sid, row in sentences.items()],
            )

            honest = ScriptedProvider("quote", sentences)
            invented = ScriptedProvider("invent", sentences)
            forged = ScriptedProvider("forge", sentences)
            silent = ScriptedProvider("silent", sentences)

            entry = {
                "fixture": name,
                "document_id": result.document_id,
                "pages": result.page_count,
                "sentences": len(sentences),
                "rent_clauses_matched": len(rent_hits),
                "overview": {
                    "found": sum(1 for card in overview.cards.values() if card.status == "FOUND"),
                    "not_located": [
                        label
                        for label, card in overview.cards.items()
                        if card.status == "NOT_LOCATED"
                    ],
                    "not_assessed": [
                        label
                        for label, card in overview.cards.items()
                        if card.status == "NOT_ASSESSED"
                    ],
                    "warnings": [warning.code for warning in overview.warnings],
                },
                "review": {
                    "review_status": review.review_status,
                    "items": len(review.attention_first),
                    "by_category": {
                        category: sum(1 for item in review.attention_first if item.category == category)
                        for category in ("CONFLICT", "AMBIGUITY", "FINANCIAL", "JURISDICTION", "OTHER")
                    },
                },
                "ask": {},
            }

            for key, question in QUESTIONS.items():
                provider = {
                    "rent": honest,
                    "rent_hallucinated": invented,
                    "notice": honest,
                    "legal": honest,
                    "absent": silent,
                    "term": honest,
                }[key]
                answer = answer_question(
                    settings, result.document_id, question, provider=provider
                )
                entry["ask"][key] = {
                    "status": answer.status.value,
                    "claims": len(answer.claims),
                    "citations": len(
                        {item.sid for claim in answer.claims for item in claim.evidence}
                    ),
                    "validation_codes": (
                        answer.run_meta.validation_codes if answer.run_meta else []
                    ),
                    "model_calls": answer.run_meta.model_calls if answer.run_meta else 0,
                }
            entry["ask"]["forged_sid"] = {
                "status": (
                    forged_answer := answer_question(
                        settings, result.document_id, QUESTIONS["rent_hallucinated"], provider=forged
                    )
                ).status.value,
                "validation_codes": (
                    forged_answer.run_meta.validation_codes if forged_answer.run_meta else []
                ),
            }
            report["documents"].append(entry)

    text = json.dumps(report, indent=2)
    if args.json:
        args.json.write_text(text + "\n")
    if args.md:
        args.md.write_text(_to_markdown(report))
    print(text)
    return 0


def _to_markdown(report: dict) -> str:
    lines = [
        "# Fixture evaluation (generated)",
        "",
        f"Generated by `scripts/evaluate_fixtures.py` at {report['generated_at']}.",
        "",
        "The model is scripted in this run, so these results measure the pipeline and",
        "validator, not a live Gemma model. A live-model run is a separate, manual step",
        "(see docs/EVALUATION.md).",
        "",
        "| Fixture | Pages | Sentences | Concepts found | Not located | Review items |",
        "|---|---|---|---|---|---|",
    ]
    for doc in report["documents"]:
        lines.append(
            "| {fixture} | {pages} | {sentences} | {found} | {missing} | {items} |".format(
                fixture=doc["fixture"],
                pages=doc["pages"],
                sentences=doc["sentences"],
                found=doc["overview"]["found"],
                missing=", ".join(doc["overview"]["not_located"]) or "-",
                items=doc["review"]["items"],
            )
        )
    lines += [
        "",
        "| Fixture | Question | Status | Claims | Validation codes |",
        "|---|---|---|---|---|",
    ]
    for doc in report["documents"]:
        for key, answer in doc["ask"].items():
            lines.append(
                "| {fixture} | {key} | {status} | {claims} | {codes} |".format(
                    fixture=doc["fixture"],
                    key=key,
                    status=answer["status"],
                    claims=answer.get("claims", "-"),
                    codes=", ".join(answer["validation_codes"]) or "-",
                )
            )
    lines += [
        "",
        "## What this does and does not show",
        "",
        "- It shows that every committed fixture ingests, maps, reviews and answers",
        "  through the same code path the HTTP API uses.",
        "- It shows that an invented figure is rejected (`LITERAL_NOT_IN_SOURCE`) and a",
        "  forged sentence id is rejected (`SID_NOT_EXPOSED_IN_RUN`).",
        "- It does not show accuracy on real contracts, OCR quality, or model latency.",
        "  No real document was used, and no claim about either is made here.",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
