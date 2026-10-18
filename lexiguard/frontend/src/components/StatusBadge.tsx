import type { CardStatus, ResponseStatus } from "../types/api";

const LABELS: Record<string, string> = {
  ANSWERED: "Answered from your document",
  LIMITED: "Answered with limits",
  NOT_LOCATED: "Not located in the document",
  AMBIGUOUS: "Ambiguous wording",
  CONFLICTING: "Conflicting clauses",
  INSUFFICIENT_EVIDENCE: "Not enough readable evidence",
  LEGAL_LIMIT: "Outside what this tool can answer",
  OUT_OF_SCOPE: "Out of scope",
  UNSUPPORTED_LANGUAGE: "Unsupported language",
  ERROR_LOCAL_MODEL_UNAVAILABLE: "Local model unavailable",
  ERROR_PROCESSING: "Could not process the question",
  FOUND: "Found",
  NOT_ASSESSED: "Not assessed",
  NOT_LOCATED_CARD: "Not located",
};

const TONE: Record<string, string> = {
  ANSWERED: "ok",
  FOUND: "ok",
  LIMITED: "warn",
  AMBIGUOUS: "warn",
  CONFLICTING: "warn",
  NOT_LOCATED: "muted",
  NOT_LOCATED_CARD: "muted",
  NOT_ASSESSED: "muted",
  INSUFFICIENT_EVIDENCE: "warn",
  LEGAL_LIMIT: "warn",
  OUT_OF_SCOPE: "muted",
  UNSUPPORTED_LANGUAGE: "warn",
  ERROR_LOCAL_MODEL_UNAVAILABLE: "bad",
  ERROR_PROCESSING: "bad",
};

export function StatusBadge({
  status,
  kind = "response",
}: {
  status: ResponseStatus | CardStatus | string;
  kind?: "response" | "card";
}) {
  const key = kind === "card" && status === "NOT_LOCATED" ? "NOT_LOCATED_CARD" : status;
  const tone = TONE[key] ?? "muted";
  return (
    <span className={`status-badge status-${tone}`} data-status={status}>
      {LABELS[key] ?? status}
    </span>
  );
}
