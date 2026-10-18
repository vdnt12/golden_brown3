import type { ReviewResponse } from "../types/api";
import type { QuoteRef } from "./SourceQuote";
import { SourceQuote, toQuoteRef } from "./SourceQuote";

const CATEGORY_LABEL: Record<string, string> = {
  CONFLICT: "Conflicting clauses",
  AMBIGUITY: "Ambiguous wording",
  FINANCIAL: "Money and amounts",
  JURISDICTION: "May depend on local law",
  OTHER: "Coverage",
};

const STATUS_NOTE: Record<ReviewResponse["review_status"], string> = {
  CLEAR: "No conflict, ambiguity, money or jurisdiction finding fired. That is not a statement that the agreement is complete or safe.",
  ATTENTION: "Items are ordered for reading convenience only. Nothing here is scored or ranked by risk.",
  NOT_ASSESSED: "Some pages could not be read, so this review is incomplete by construction.",
};

export function ReviewPanel({
  review,
  onOpenQuote,
}: {
  review: ReviewResponse;
  onOpenQuote: (ref: QuoteRef) => void;
}) {
  const items = review.attention_first;
  return (
    <section aria-labelledby="review-heading">
      <div className="section-head">
        <h2 id="review-heading">Review, in reading order</h2>
        <p className="hint" data-status={review.review_status}>
          {review.review_status.replace("_", " ").toLowerCase()} · {items.length} item
          {items.length === 1 ? "" : "s"}
        </p>
      </div>
      <p className="disclaimer">{review.disclaimer}</p>
      <p className="hint">{STATUS_NOTE[review.review_status]}</p>

      {items.length === 0 ? null : (
        <ol className="review-list">
          {items.map((item) => (
            <li className="review-item" key={`${item.category}-${item.title}`} data-category={item.category}>
              <header>
                <p className="eyebrow">
                  {CATEGORY_LABEL[item.category] ?? item.category} · priority {item.priority}
                </p>
                <h3>{item.title}</h3>
              </header>
              <p>{item.reason}</p>
              {item.order_reason ? <p className="hint">Order: {item.order_reason}</p> : null}
              {item.citations.map((citation) => (
                <SourceQuote
                  key={`${citation.sid}-${citation.quote.slice(0, 24)}`}
                  quote={toQuoteRef(citation)}
                  onOpen={onOpenQuote}
                />
              ))}
            </li>
          ))}
        </ol>
      )}

      {review.questions_for_professional.length ? (
        <section className="escalation" aria-labelledby="escalation-heading">
          <h3 id="escalation-heading">Questions to ask a qualified lawyer</h3>
          <p className="hint">
            These are neutral questions, not advice. GBDoc does not answer them.
          </p>
          <ol>
            {review.questions_for_professional.map((question) => (
              <li key={`${question.topic}-${question.prompt.slice(0, 40)}`}>
                <span className="eyebrow">{question.topic}</span>
                <br />
                {question.prompt}
              </li>
            ))}
          </ol>
        </section>
      ) : null}
    </section>
  );
}
