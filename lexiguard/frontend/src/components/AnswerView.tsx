import type { Claim, RenderedAnswer } from "../types/api";
import { SourceQuote, toQuoteRef } from "./SourceQuote";
import type { QuoteRef } from "./SourceQuote";
import { StatusBadge } from "./StatusBadge";

function ClaimBlock({
  claim,
  onOpenQuote,
}: {
  claim: Claim;
  onOpenQuote: (ref: QuoteRef) => void;
}) {
  return (
    <li className="claim">
      <p className="claim-text">{claim.text}</p>
      <p className="claim-kind">
        {claim.classification === "DIRECT"
          ? "Direct statement of the document"
          : claim.classification === "SUPPORTED"
            ? "Supported by the quoted text"
            : claim.classification.charAt(0) + claim.classification.slice(1).toLowerCase()}
      </p>
      {claim.evidence.map((item) => (
        <SourceQuote key={item.sid} quote={toQuoteRef(item)} onOpen={onOpenQuote} />
      ))}
    </li>
  );
}

function ClaimSection({
  title,
  description,
  claims,
  onOpenQuote,
}: {
  title: string;
  description?: string;
  claims: Claim[];
  onOpenQuote: (ref: QuoteRef) => void;
}) {
  if (!claims.length) return null;
  return (
    <section className="answer-section">
      <h3>{title}</h3>
      {description ? <p className="hint">{description}</p> : null}
      <ul className="claim-list">
        {claims.map((claim) => (
          <ClaimBlock key={claim.claim_id} claim={claim} onOpenQuote={onOpenQuote} />
        ))}
      </ul>
    </section>
  );
}

const EXPLAINER: Record<string, string> = {
  ANSWERED: "Answer built only from sentences in your document.",
  LIMITED: "Something in the wording limits how far this can be answered from the text.",
  NOT_LOCATED: "This was not found in the readable text. It may be absent, or unreadable.",
  AMBIGUOUS: "The document says something, but the wording does not settle it.",
  CONFLICTING: "Two passages disagree. Both are shown; the tool does not pick a winner.",
  INSUFFICIENT_EVIDENCE: "Not enough readable, checkable text to answer this.",
  LEGAL_LIMIT: "This asks for legal judgment, which GBDoc does not give.",
  OUT_OF_SCOPE: "This is outside what a rental agreement review can answer.",
  UNSUPPORTED_LANGUAGE: "The readable text is not in a language this build supports.",
  ERROR_LOCAL_MODEL_UNAVAILABLE: "The local model is not running. Nothing was guessed.",
  ERROR_PROCESSING: "The request could not be completed. Nothing was guessed.",
};

export function AnswerView({
  answer,
  onOpenQuote,
}: {
  answer: RenderedAnswer;
  onOpenQuote: (ref: QuoteRef) => void;
}) {
  return (
    <article className="answer" aria-live="polite">
      <header className="answer-head">
        <StatusBadge status={answer.status} />
        <p className="hint">{EXPLAINER[answer.status] ?? ""}</p>
      </header>

      {answer.answer ? <p className="answer-lead">{answer.answer}</p> : null}

      <ClaimSection title="From the document" claims={answer.claims} onOpenQuote={onOpenQuote} />
      <ClaimSection
        title="Interpretation"
        description="A reading of the text, clearly separated from what it says."
        claims={answer.interpretations}
        onOpenQuote={onOpenQuote}
      />
      <ClaimSection
        title="Worth checking"
        claims={answer.concerns}
        onOpenQuote={onOpenQuote}
      />
      <ClaimSection
        title="Ambiguous wording"
        claims={answer.ambiguities}
        onOpenQuote={onOpenQuote}
      />
      <ClaimSection
        title="Conflicting passages"
        description="Both readings are shown. GBDoc does not decide between them."
        claims={answer.conflicts}
        onOpenQuote={onOpenQuote}
      />

      {answer.general_explanations.length ? (
        <section className="answer-section">
          <h3>Term explained (not from your document)</h3>
          {answer.general_explanations.map((entry) => (
            <div className="glossary-entry" key={entry.entry_id}>
              <h4>{entry.term}</h4>
              <p>{entry.definition}</p>
              <p className="hint">{entry.disclaimer}</p>
            </div>
          ))}
        </section>
      ) : null}

      {answer.missing_information.length ? (
        <section className="answer-section">
          <h3>What is missing, and where I looked</h3>
          {answer.missing_information.map((missing, index) => (
            <div key={`${missing.code}-${index}`}>
              <p>{missing.message}</p>
              {missing.searches.length ? (
                <p className="hint">Searches: {missing.searches.join("; ")}</p>
              ) : null}
              {missing.evidence.map((item) => (
                <SourceQuote key={item.sid} quote={toQuoteRef(item)} onOpen={onOpenQuote} />
              ))}
            </div>
          ))}
        </section>
      ) : null}

      {answer.jurisdiction_flags.length ? (
        <section className="answer-section">
          <h3>May depend on local law</h3>
          {answer.jurisdiction_flags.map((flag) => (
            <div key={flag.topic}>
              <p>
                <strong>{flag.topic}</strong> - {flag.label}
              </p>
              {flag.evidence.map((item) => (
                <SourceQuote key={item.sid} quote={toQuoteRef(item)} onOpen={onOpenQuote} />
              ))}
            </div>
          ))}
        </section>
      ) : null}

      {answer.escalation.length ? (
        <section className="answer-section escalation">
          <h3>Questions to ask a qualified lawyer</h3>
          <ol>
            {answer.escalation.map((question, index) => (
              <li key={index}>{question.question}</li>
            ))}
          </ol>
        </section>
      ) : null}

      {answer.extraction_warnings.length ? (
        <section className="answer-section">
          <h3>Extraction warnings</h3>
          <ul className="warnings">
            {answer.extraction_warnings.map((warning, index) => (
              <li key={`${warning.code}-${index}`}>
                {warning.page ? `Page ${warning.page}: ` : ""}
                {warning.message}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {answer.run_meta ? (
        <details className="run-meta">
          <summary>How this answer was produced</summary>
          <dl>
            <dt>Model</dt>
            <dd>{answer.run_meta.model_tag ?? "unknown"}</dd>
            <dt>Route</dt>
            <dd>{answer.run_meta.route}</dd>
            <dt>Path</dt>
            <dd>{answer.run_meta.path === "FAST" ? "single pass, no retrieval loop" : "refined once"}</dd>
            <dt>Tool calls</dt>
            <dd>{answer.run_meta.tool_calls}</dd>
            <dt>Model calls</dt>
            <dd>{answer.run_meta.model_calls}</dd>
            <dt>Passages considered</dt>
            <dd>{answer.run_meta.chunks_considered}</dd>
            <dt>Citations exposed</dt>
            <dd>{answer.run_meta.sids_exposed.length}</dd>
            <dt>Time</dt>
            <dd>{answer.run_meta.duration_ms} ms</dd>
            {answer.run_meta.validation_codes.length ? (
              <>
                <dt>Checks applied</dt>
                <dd>{answer.run_meta.validation_codes.join(", ")}</dd>
              </>
            ) : null}
          </dl>
          <p className="hint">
            This is a record of what the tool did, not the model's reasoning. Prompts and
            model deliberation are never shown or stored.
          </p>
        </details>
      ) : null}
    </article>
  );
}
