"""Command-line interface: `python -m app.cli ask FILE "question"`.

The same service layer as the HTTP API, without a browser. Useful for scripted
runs, CI smoke tests and reviewers who want to see the rendered JSON.

Exit codes:
    0  an answer was rendered (any status, including a refusal)
    1  the document could not be ingested
    2  the local model could not answer (fail-closed status)
    3  bad usage (unknown model, missing file)
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import textwrap

from app.config import Settings
from app.ingest.pipeline import IngestError, ingest_document
from app.model.factory import build_provider, model_inventory
from app.model.registry import UnknownModel, resolve_model
from app.schemas.response import RenderedAnswer
from app.services.answer import answer_question
from app.services.documents import delete_document, list_documents


def _settings(args: argparse.Namespace) -> Settings:
    return Settings(data_dir=pathlib.Path(args.data_dir))


def _print_answer(answer: RenderedAnswer, *, model_tag: str) -> None:
    width = 88
    print(f"status: {answer.status.value}")
    print(f"model:  {model_tag}")
    if answer.run_meta:
        print(
            f"meta:   route={answer.run_meta.route.value} path={answer.run_meta.path.value} "
            f"tool_calls={answer.run_meta.tool_calls} model_calls={answer.run_meta.model_calls} "
            f"{answer.run_meta.duration_ms} ms"
        )
        if answer.run_meta.validation_codes:
            print(f"checks: {', '.join(answer.run_meta.validation_codes)}")
    print()
    for line in textwrap.wrap(answer.answer, width=width) or [""]:
        print(line)

    def section(title: str, claims) -> None:
        if not claims:
            return
        print(f"\n{title}")
        for claim in claims:
            for line in textwrap.wrap(claim.text, width=width - 2):
                print(f"  {line}")
            for item in claim.evidence:
                print(f'  > "{item.quote}"')
                print(f"    p.{item.page}" + (f" section {item.section}" if item.section else ""))

    section("From the document", answer.claims)
    section("Interpretation", answer.interpretations)
    section("Worth checking", answer.concerns)
    section("Ambiguous wording", answer.ambiguities)
    section("Conflicting passages", answer.conflicts)

    for entry in answer.general_explanations:
        print(f"\nTerm: {entry.term}\n  {entry.definition}\n  ({entry.disclaimer})")
    for missing in answer.missing_information:
        print(f"\nMissing: {missing.message}")
        if missing.searches:
            print(f"  searches: {', '.join(missing.searches)}")
    for flag in answer.jurisdiction_flags:
        print(f"\nLocal law: {flag.topic} - {flag.label}")
    if answer.escalation:
        print("\nQuestions for a qualified lawyer")
        for question in answer.escalation:
            for line in textwrap.wrap(question.question, width=width - 4, initial_indent="  - ", subsequent_indent="    "):
                print(line)
    print("\nNot legal advice. Not a verdict.")


def cmd_ask(args: argparse.Namespace) -> int:
    settings = _settings(args)
    try:
        model_tag = resolve_model(settings, args.model)
    except UnknownModel as exc:
        print(str(exc), file=sys.stderr)
        return 3

    path = pathlib.Path(args.file)
    if not path.is_file():
        print(f"file not found: {path}", file=sys.stderr)
        return 3

    try:
        result = ingest_document(filename=path.name, data=path.read_bytes(), settings=settings)
    except IngestError as exc:
        print(f"ingest failed: {exc.code}: {exc.message}", file=sys.stderr)
        return 1

    print(f"document: {result.document_id} ({result.page_count} pages, {path.name})")
    provider = build_provider(settings, model_tag)
    answer = answer_question(
        settings,
        result.document_id,
        args.question,
        provider=provider,
        model_tag=model_tag,
    )
    if args.json:
        print(answer.model_dump_json(indent=2))
    else:
        _print_answer(answer, model_tag=model_tag)

    if args.delete_after:
        delete_document(settings, result.document_id, provider=provider)
        print(f"\ndeleted: {result.document_id}")
    if answer.status.value in {"ERROR_LOCAL_MODEL_UNAVAILABLE", "ERROR_PROCESSING"}:
        return 2
    return 0


def cmd_documents(args: argparse.Namespace) -> int:
    settings = _settings(args)
    documents = list_documents(settings)
    if not documents:
        print("no documents stored")
        return 0
    for document in documents:
        print(
            f"{document.document_id}  {document.display_name}  "
            f"{document.page_count}p  {document.source_kind}  {document.created_at}"
        )
    return 0


def cmd_delete(args: argparse.Namespace) -> int:
    settings = _settings(args)
    report = delete_document(settings, args.document_id)
    print(json.dumps(report.model_dump(), indent=2))
    return 0


def cmd_models(args: argparse.Namespace) -> int:
    settings = _settings(args)
    for row in model_inventory(settings):
        state = "installed" if row["available"] else "not installed"
        default = " (default)" if row["default"] else ""
        print(f"{row['alias']:10s} {row['tag']:26s} {state}{default}")
    if not any(row["available"] for row in model_inventory(settings)):
        print("\nNo supported local model is installed. Start Ollama and pull one:")
        print("  OLLAMA_NO_CLOUD=1 ollama serve")
        print(f"  ollama pull {settings.model_tag}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lexiguard", description="Local document triage")
    parser.add_argument("--data-dir", default="data", help="where documents are stored (default: ./data)")
    sub = parser.add_subparsers(dest="command", required=True)

    ask = sub.add_parser("ask", help="ingest a PDF/TXT and answer one question")
    ask.add_argument("file")
    ask.add_argument("question")
    ask.add_argument("--model", default=None, help="gemma | gemma-e2b | hermes | exact tag")
    ask.add_argument("--json", action="store_true", help="print the full RenderedAnswer JSON")
    ask.add_argument("--delete-after", action="store_true", help="delete the document after answering")
    ask.set_defaults(func=cmd_ask)

    documents = sub.add_parser("documents", help="list stored documents")
    documents.set_defaults(func=cmd_documents)

    delete = sub.add_parser("delete", help="delete a stored document")
    delete.add_argument("document_id")
    delete.set_defaults(func=cmd_delete)

    models = sub.add_parser("models", help="list supported local models and whether they are installed")
    models.set_defaults(func=cmd_models)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
