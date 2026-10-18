import { useEffect, useState } from "react";
import { api, fetchPageImage } from "../api/client";
import type { EvidenceResponse, PageResponse } from "../types/api";
import type { QuoteRef } from "./SourceQuote";

/**
 * Shows the stored text of one page, the exact sentence that was cited, and
 * (for PDFs) the page image. Text comes from the database, not the model.
 */
export function PageViewer({
  documentId,
  quote,
  page,
  onClose,
}: {
  documentId: string;
  quote: QuoteRef | null;
  page: number;
  onClose: () => void;
}) {
  const [payload, setPayload] = useState<PageResponse | null>(null);
  const [evidence, setEvidence] = useState<EvidenceResponse | null>(null);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setPayload(null);
    setEvidence(null);
    setError("");
    api
      .page(documentId, page)
      .then((body) => {
        if (!cancelled) setPayload(body);
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Page unavailable.");
      });
    fetchPageImage(documentId, page).then((url) => {
      if (!cancelled) setImageUrl(url);
    });
    return () => {
      cancelled = true;
    };
  }, [documentId, page]);

  useEffect(() => {
    if (!quote) {
      setEvidence(null);
      return;
    }
    let cancelled = false;
    api
      .evidence(documentId, quote.sid)
      .then((body) => {
        if (!cancelled) setEvidence(body);
      })
      .catch(() => {
        if (!cancelled) setEvidence(null);
      });
    return () => {
      cancelled = true;
    };
  }, [documentId, quote]);

  return (
    <aside className="page-viewer" aria-label={`Page ${page}`}>
      <header className="page-viewer-head">
        <div>
          <p className="eyebrow">Source page</p>
          <h3>Page {page}</h3>
        </div>
        <button type="button" onClick={onClose} aria-label="Close page viewer">
          Close
        </button>
      </header>

      {error ? <p role="alert">{error}</p> : null}

      {quote ? (
        <section className="cited-passage">
          <p className="eyebrow">Cited sentence {quote.sid} · p. {evidence?.page ?? page}</p>
          <p className="cited-text">{quote.quote}</p>
          {evidence && evidence.verbatim_text !== quote.quote ? (
            <p className="hint">Stored text differs slightly from the quote shown; the page text below is authoritative.</p>
          ) : null}
        </section>
      ) : null}

      <section>
        <p className="eyebrow">Stored page text</p>
        {payload ? (
          payload.text.trim() ? (
            <div className="page-text">
              {payload.sentences.map((sentence) => (
                <span
                  key={sentence.sid}
                  className={
                    quote && sentence.sid === quote.sid ? "sentence sentence-highlight" : "sentence"
                  }
                  title={`${sentence.sid} · chars ${sentence.start_offset}-${sentence.end_offset}${
                    sentence.ocr_derived ? " (OCR)" : ""
                  }`}
                >
                  {sentence.text}{" "}
                </span>
              ))}
            </div>
          ) : (
            <p className="hint">No machine-readable text was stored for this page.</p>
          )
        ) : (
          <p className="hint" role="status">Loading page text...</p>
        )}
        {payload ? (
          <p className="hint">
            Page {payload.page_number}
            {payload.is_virtual_page ? " (virtual page: this file has no physical pages)" : ""}
            {payload.ocr_used ? " · text from OCR" : ""}
            {payload.flags.length ? ` · flags: ${payload.flags.join(", ")}` : ""}
          </p>
        ) : null}
      </section>

      {imageUrl ? (
        <section>
          <p className="eyebrow">Rendered page</p>
          <img className="page-image" src={imageUrl} alt={`Rendered page ${page}`} />
          <p className="hint">
            The image is rendered locally from your file. Text above is extracted; if the
            scan is unclear, compare with this image.
          </p>
        </section>
      ) : (
        <p className="hint">
          No page image is available for this document type. The stored text is the source
          of every quotation.
        </p>
      )}
    </aside>
  );
}
