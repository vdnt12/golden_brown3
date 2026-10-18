import type { OverviewResponse } from "../types/api";
import type { QuoteRef } from "./SourceQuote";
import { SourceQuote, toQuoteRef } from "./SourceQuote";
import { StatusBadge } from "./StatusBadge";

const STATUS_ORDER: Record<string, number> = {
  FOUND: 0,
  NOT_ASSESSED: 1,
  INSUFFICIENT_EVIDENCE: 2,
  NOT_LOCATED: 3,
};

/**
 * The document map. Every card states what was found, or plainly that it was
 * not located / not assessed. A card never implies a missing clause is safe.
 */
export function DocumentMap({
  overview,
  onOpenQuote,
}: {
  overview: OverviewResponse;
  onOpenQuote: (ref: QuoteRef) => void;
}) {
  // `cards` is an object keyed by the contract's display labels; the keys are
  // the labels, so insertion order is the PRD's concept order.
  const cards = Object.entries(overview.cards).sort(
    ([, a], [, b]) => (STATUS_ORDER[a.status] ?? 9) - (STATUS_ORDER[b.status] ?? 9),
  );
  const found = cards.filter(([, card]) => card.status === "FOUND").length;

  return (
    <section aria-labelledby="map-heading">
      <div className="section-head">
        <h2 id="map-heading">Document map</h2>
        <p className="hint">
          {found} of {cards.length} concepts located in this document.
        </p>
      </div>

      {overview.warnings.length ? (
        <ul className="warnings">
          {overview.warnings.map((warning) => (
            <li key={`${warning.code}-${warning.page ?? "doc"}`}>
              <span className="warning-code">{warning.code.split("_").join(" ").toLowerCase()}</span>{" "}
              {warning.message}
            </li>
          ))}
        </ul>
      ) : null}

      <div className="card-grid">
        {cards.map(([label, card]) => (
          <article className="map-card" key={label} data-status={card.status}>
            <header>
              <h3>{label}</h3>
              <StatusBadge status={card.status} kind="card" />
            </header>
            {card.summary ? <p className="card-summary">{card.summary}</p> : null}
            {card.note ? <p className="hint">{card.note}</p> : null}
            {card.evidence.map((item) => (
              <SourceQuote key={item.sid} quote={toQuoteRef(item)} onOpen={onOpenQuote} />
            ))}
          </article>
        ))}
      </div>
    </section>
  );
}
