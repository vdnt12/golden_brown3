
import json
from pathlib import Path

from app.core.enums import PointKind
from app.validation.legal_policy import LEGAL_LIMIT_TEXT, scan_text

CORPUS = Path(__file__).resolve().parents[1] / "data" / "scanner_corpus.jsonl"


def load_corpus() -> list[dict]:
    rows = []
    for line in CORPUS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def test_corpus_meets_guide_minimum_size():
    rows = load_corpus()
    block = [r for r in rows if r["expect"] == "block"]
    allow = [r for r in rows if r["expect"] == "pass"]
    assert len(block) >= 40, f"must-block rows: {len(block)}"
    assert len(allow) >= 40, f"must-pass rows: {len(allow)}"


def test_corpus_block_recall_is_total():
    failures = []
    for row in load_corpus():
        if row["expect"] != "block":
            continue
        kind = PointKind(row["kind"]) if row.get("kind") else None
        result = scan_text(row["text"], kind=kind, source_text=row.get("source", ""))
        if not result.blocked:
            failures.append(row["text"])
    assert failures == [], f"missed verdicts: {failures}"


def test_corpus_false_block_rate_is_zero():
    failures = []
    for row in load_corpus():
        if row["expect"] != "pass":
            continue
        kind = PointKind(row["kind"]) if row.get("kind") else None
        result = scan_text(row["text"], kind=kind, source_text=row.get("source", ""))
        if result.blocked:
            failures.append((row["text"], result.rule))
    assert failures == [], f"false blocks: {failures}"


def test_source_quote_text_is_not_scanned_by_this_module():
    # The scanner is only ever called on assistant-authored text. A source
    # quotation containing "void" remains renderable in the SourceQuote panel.
    assert scan_text("This clause is void.").blocked is True


def test_limitation_template_passes_scanner():
    assert scan_text(LEGAL_LIMIT_TEXT).blocked is False
