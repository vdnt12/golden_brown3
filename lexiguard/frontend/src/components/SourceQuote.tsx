import type { CardEvidence, EvidenceItem } from "../types/api";

export interface QuoteRef {
  sid: string;
  page: number;
  section: string | null;
  quote: string;
  ocr_derived: boolean;
}

export function toQuoteRef(item: EvidenceItem | CardEvidence): QuoteRef {
  return {
    sid: item.sid,
    page: item.page,
    section: item.section,
    quote: item.quote,
    ocr_derived: item.ocr_derived,
  };
}

/**
 * A quotation is rendered verbatim, in quotation marks, with its page number.
 * Clicking it opens the page viewer on that page. Nothing is paraphrased here.
 */
export function SourceQuote({
  quote,
  onOpen,
}: {
  quote: QuoteRef;
  onOpen: (ref: QuoteRef) => void;
}) {
  return (
    <figure className="source-quote">
      <blockquote>
        <button
          type="button"
          className="quote-link"
          onClick={() => onOpen(quote)}
          title="Open this passage on its page"
        >
          &ldquo;{quote.quote}&rdquo;
        </button>
      </blockquote>
      <figcaption>
        <span>p. {quote.page}</span>
        {quote.section ? <span> · section {quote.section}</span> : null}
        {quote.ocr_derived ? <span className="ocr-tag"> · OCR text, check the scan</span> : null}
      </figcaption>
    </figure>
  );
}
