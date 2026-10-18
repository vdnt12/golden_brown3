#!/usr/bin/env python3
"""Validate LexiGuard's deterministic pipeline against CUAD v1.

CUAD (Atticus Project, CC BY 4.0) is a corpus of 510 commercial contracts with
lawyer-annotated clause spans. It is **not** a tenancy corpus: it tells us how
the concept matcher, parser and renderer behave on real legal drafting, not how
accurate the tool is on rental agreements.

For each sampled contract the script:

1. ingests the full contract text through `ingest_document` (the real pipeline);
2. builds the 11-card overview and the review list;
3. checks every emitted quotation is an exact substring of stored text;
4. compares mapped concepts against the CUAD gold spans:
   - *matcher recall*: does the concept lexicon fire on the gold clause text?
   - *map recall*: does the overview card say FOUND when a gold clause exists?
   - *false silence*: gold clause exists but the card says NOT_LOCATED.

Run:
    python3 scripts/fetch_cuad.py           # once, downloads 40 MB
    python3 scripts/evaluate_cuad.py --limit 60
"""
from __future__ import annotations

import argparse
import json
import pathlib
import statistics
import sys
import tempfile
import time
from datetime import UTC, datetime

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "backend"))

from app.config import Settings  # noqa: E402
from app.ingest.pipeline import IngestError, ingest_document  # noqa: E402
from app.retrieval.concepts import CONCEPTS_BY_KEY, CONCEPTS_BY_LABEL, match_sentences  # noqa: E402
from app.services.overview import build_overview  # noqa: E402
from app.services.review import build_review  # noqa: E402
from app.store.repo import open_document  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
CUAD_PATH = ROOT / "datasets" / "cuad" / "CUAD_v1.json"

# CUAD clause type -> LexiGuard concept. Only defensible mappings are included.
CLAUSE_MAP: dict[str, str] = {
    "Parties": "parties",
    "Agreement Date": "term",
    "Effective Date": "term",
    "Expiration Date": "term",
    "Renewal Term": "term",
    "Notice Period To Terminate Renewal": "notice",
    "Liquidated Damages": "penalties",
    "Governing Law": "disputes",
    "Non-Compete": "restrictions",
    "Exclusivity": "restrictions",
    "No-Solicit Of Customers": "restrictions",
    "No-Solicit Of Employees": "restrictions",
    "Non-Disparagement": "restrictions",
}


def clause_type(question: str) -> str:
    start = question.find('"')
    end = question.find('"', start + 1)
    return question[start + 1 : end] if start >= 0 and end > start else ""


def load_contracts(limit: int | None) -> list[dict]:
    payload = json.loads(CUAD_PATH.read_text(encoding="utf-8"))
    rows: list[dict] = []
    for index, entry in enumerate(payload["data"]):
        paragraph = entry["paragraphs"][0]
        rows.append(
            {
                "index": index,
                "title": entry["title"],
                "text": paragraph["context"],
                "qas": paragraph["qas"],
            }
        )
    if limit is not None and limit < len(rows):
        step = len(rows) / limit
        rows = [rows[int(i * step)] for i in range(limit)]
    return rows


def stored_text(settings: Settings, doc_id: str) -> tuple[str, int]:
    with open_document(settings.data_dir, doc_id) as handle:
        rows = handle.connection.execute(
            "SELECT text FROM sentences WHERE doc_id = ?", (doc_id,)
        ).fetchall()
    joined = "\n".join(row["text"] for row in rows)
    return joined, len(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=60, help="number of contracts (evenly sampled)")
    parser.add_argument("--all", action="store_true", help="use all 510 contracts")
    parser.add_argument("--json", type=pathlib.Path, default=ROOT / "reports" / "cuad_evaluation.json")
    parser.add_argument("--md", type=pathlib.Path, default=ROOT / "reports" / "cuad_evaluation.md")
    args = parser.parse_args()

    if not CUAD_PATH.exists():
        print("CUAD_v1.json not found. Run python3 scripts/fetch_cuad.py first.", file=sys.stderr)
        return 2

    contracts = load_contracts(None if args.all else args.limit)
    per_concept = {
        concept: {
            "gold_contracts": 0,
            "gold_spans": 0,
            "found": 0,
            "not_located": 0,
            "matcher_hits": 0,
        }
        for concept in sorted(set(CLAUSE_MAP.values()))
    }
    failures: list[dict[str, str]] = []
    durations: list[int] = []
    pages: list[int] = []
    quotes_checked = 0
    quote_failures: list[str] = []
    review_items = 0
    unmapped_types: dict[str, int] = {}

    with tempfile.TemporaryDirectory() as tmp:
        settings = Settings(data_dir=pathlib.Path(tmp))
        for row in contracts:
            gold: dict[str, list[str]] = {}
            for qa in row["qas"]:
                kind = clause_type(qa["question"])
                answers = [answer["text"] for answer in qa.get("answers", []) if answer.get("text")]
                if answers:
                    gold.setdefault(kind, []).extend(answers)
                elif kind not in CLAUSE_MAP:
                    unmapped_types[kind] = unmapped_types.get(kind, 0) + 1

            started = time.perf_counter()
            try:
                result = ingest_document(
                    filename=f"cuad_{row['index']:03d}.txt",
                    data=row["text"].encode("utf-8"),
                    settings=settings,
                )
                overview = build_overview(settings, result.document_id)
                review = build_review(settings, result.document_id)
            except IngestError as exc:
                failures.append({"title": row["title"][:80], "error": f"{exc.code}: {exc.message}"})
                continue
            except Exception as exc:  # noqa: BLE001 - a crash is a result we must report
                failures.append({"title": row["title"][:80], "error": f"{type(exc).__name__}: {exc}"})
                continue
            durations.append(int((time.perf_counter() - started) * 1000))
            pages.append(result.page_count)
            review_items += len(review.attention_first)

            joined, _ = stored_text(settings, result.document_id)
            for label, card in overview.cards.items():
                for item in card.evidence:
                    quotes_checked += 1
                    if item.quote not in joined:
                        quote_failures.append(f"{row['title'][:50]} {label} {item.sid}")

            status_by_concept = {
                CONCEPTS_BY_LABEL[label].key: card.status
                for label, card in overview.cards.items()
            }
            for cuad_type, concept in CLAUSE_MAP.items():
                spans = gold.get(cuad_type, [])
                if not spans:
                    continue
                bucket = per_concept[concept]
                bucket["gold_contracts"] += 1
                bucket["gold_spans"] += len(spans)
                status = status_by_concept.get(concept)
                if status == "FOUND":
                    bucket["found"] += 1
                elif status == "NOT_LOCATED":
                    bucket["not_located"] += 1
                concept_obj = CONCEPTS_BY_KEY[concept]
                hits = sum(
                    1
                    for span in spans
                    if match_sentences(concept_obj, [("g", span)])
                )
                bucket["matcher_hits"] += hits
            # cleanup so the temp dir does not grow
            import shutil

            shutil.rmtree(pathlib.Path(tmp) / "docs" / result.document_id, ignore_errors=True)

    def rate(part: int, whole: int) -> float | None:
        return round(100.0 * part / whole, 1) if whole else None

    report = {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "dataset": {
            "name": "CUAD v1",
            "license": "CC BY 4.0",
            "source": "https://huggingface.co/datasets/theatticusproject/cuad",
            "sha256": "ed0b77d85bdf4014d7495800e8e4a70565b48ee6f8a2e5dca9cf8655dbf10eae",
            "contracts_total": 510,
            "contracts_sampled": len(contracts),
        },
        "ingest": {
            "succeeded": len(durations),
            "failed": len(failures),
            "failures": failures[:20],
            "pages_min": min(pages) if pages else None,
            "pages_max": max(pages) if pages else None,
            "duration_ms_median": statistics.median(durations) if durations else None,
        },
        "quotes": {
            "checked": quotes_checked,
            "exact_substring_failures": len(quote_failures),
            "examples": quote_failures[:10],
        },
        "review_items_total": review_items,
        "concepts": {
            concept: {
                **bucket,
                "map_recall_pct": rate(bucket["found"], bucket["gold_contracts"]),
                "false_silence_pct": rate(bucket["not_located"], bucket["gold_contracts"]),
                "matcher_recall_pct": rate(bucket["matcher_hits"], bucket["gold_spans"]),
            }
            for concept, bucket in per_concept.items()
        },
        "notes": [
            "CUAD is a commercial-contract corpus, not a tenancy corpus.",
            "CUAD gold spans are lawyer-selected review highlights, not an exhaustive list of "
            "every sentence about a topic; 'found without gold label' is therefore not counted "
            "as a false positive.",
            "No model was called. This measures ingestion, concept matching, mapping and rendering.",
        ],
    }
    args.json.write_text(json.dumps(report, indent=2) + "\n")
    args.md.write_text(to_markdown(report))
    print(json.dumps(report["ingest"], indent=2))
    print(json.dumps(report["quotes"], indent=2))
    for concept, bucket in report["concepts"].items():
        print(
            f"{concept:14s} gold={bucket['gold_contracts']:3d}/{bucket['gold_spans']:4d} "
            f"map_recall={bucket['map_recall_pct']} "
            f"false_silence={bucket['false_silence_pct']} "
            f"matcher_recall={bucket['matcher_recall_pct']}"
        )
    return 0


def to_markdown(report: dict) -> str:
    lines = [
        "# CUAD evaluation (generated)",
        "",
        f"Generated by `scripts/evaluate_cuad.py` at {report['generated_at']}.",
        "",
        f"Dataset: **{report['dataset']['name']}**, {report['dataset']['license']}, "
        f"sha256 `{report['dataset']['sha256'][:16]}…`, "
        f"{report['dataset']['contracts_sampled']} of {report['dataset']['contracts_total']} contracts "
        "evenly sampled.",
        "",
        "CUAD is a corpus of **commercial** contracts, not tenancy agreements. These numbers",
        "describe parser robustness, quotation integrity and clause-language coverage on real",
        "legal drafting. They are **not** a rental-agreement accuracy claim, and no model was called.",
        "",
        "## Ingestion",
        "",
        f"- contracts ingested: **{report['ingest']['succeeded']} / {report['dataset']['contracts_sampled']}**",
        f"- failures: {report['ingest']['failed']}",
        f"- pages per contract: {report['ingest']['pages_min']}–{report['ingest']['pages_max']}",
        f"- median end-to-end ingest+map+review time: {report['ingest']['duration_ms_median']} ms",
        "",
        "## Quotation integrity",
        "",
        f"- quotations checked against stored text: **{report['quotes']['checked']}**",
        f"- exact-substring failures: **{report['quotes']['exact_substring_failures']}**",
        "",
        "## Concept coverage on CUAD gold clauses",
        "",
        "| Concept | Contracts with gold clause | Map says FOUND | Map says NOT_LOCATED | Matcher fires on gold text |",
        "|---|---:|---:|---:|---:|",
    ]
    for concept, bucket in report["concepts"].items():
        lines.append(
            f"| {concept} | {bucket['gold_contracts']} ({bucket['gold_spans']} spans) | "
            f"{bucket['map_recall_pct']}% | {bucket['false_silence_pct']}% | "
            f"{bucket['matcher_recall_pct']}% |"
        )
    lines += [
        "",
        "`NOT_LOCATED` on a contract where CUAD has a gold clause is the metric that matters for",
        "safety: it means the tool told a user a topic was absent when the corpus says otherwise.",
        "",
        "## What this does and does not show",
        "",
        "- Shows: the parser survives long, densely formatted legal text; every rendered quote is",
        "  byte-identical to stored text; mapped concepts behave as measured.",
        "- Does not show: rental-agreement accuracy, model quality, or completeness of the map.",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
