"""The ask use case: open the document, run the bounded runtime, write the ledger.

Routes stay thin; everything that decides what the user sees lives in
`agent.runtime` and `validation`. The ledger stores identifiers and counts only
-- never the question, the answer, or any evidence text.
"""
from __future__ import annotations

from app.agent.runtime import AskContext, BoundedAgentRuntime
from app.config import Settings
from app.model.provider import LLMProvider
from app.schemas.response import RenderedAnswer
from app.store.ledger import record_run
from app.store.repo import open_document


def answer_question(
    settings: Settings,
    doc_id: str,
    question: str,
    *,
    provider: LLMProvider | None,
    model_tag: str | None = None,
    allow_fallback: bool = False,
) -> RenderedAnswer:
    with open_document(settings.data_dir, doc_id) as handle:
        row = handle.connection.execute(
            "SELECT * FROM document WHERE doc_id = ?", (doc_id,)
        ).fetchone()
        if row is None:
            raise LookupError(doc_id)

        import re

        unread = [int(value) for value in re.findall(r"\d+", str(row["language_flags"] or "[]"))]
        ocr_pages = [
            int(item["page_no"])
            for item in handle.connection.execute(
                "SELECT DISTINCT page_no FROM sentences WHERE doc_id = ? AND ocr_derived = 1",
                (doc_id,),
            )
        ]
        context = AskContext(
            doc_id=doc_id,
            sha256=row["sha256"],
            page_count=int(row["page_count"]),
            display_name=row["source_filename"] or "document",
            connection=handle.connection,
            settings=settings,
            provider=provider,
            model_tag=model_tag or settings.model_tag,
            unread_pages=unread,
            ocr_pages=ocr_pages,
            allow_fallback=allow_fallback,
        )
        runtime = BoundedAgentRuntime(context)
        rendered = runtime.answer(question)

        meta = rendered.run_meta
        if meta is not None:
            record_run(
                handle.connection,
                doc_id=doc_id,
                route=meta.route.value,
                status=rendered.status.value,
                path=meta.path.value,
                tool_names=[],
                tool_calls=meta.tool_calls,
                model_calls=meta.model_calls,
                sids_exposed=meta.sids_exposed,
                validation_codes=meta.validation_codes,
                duration_ms=meta.duration_ms,
            )
        return rendered
