import { useEffect, useState } from "react";
import { api } from "../api/client";
import type {
  ComplianceAuditResponse,
  DocumentSummary,
  StatutoryAuditFinding,
} from "../types/api";
import type { QuoteRef } from "./SourceQuote";

interface ComplianceAuditPanelProps {
  document: DocumentSummary;
  onOpenQuote: (ref: QuoteRef) => void;
  onAskClick?: (prompt: string) => void;
}

export function ComplianceAuditPanel({
  document,
  onOpenQuote,
  onAskClick,
}: ComplianceAuditPanelProps) {
  const [auditData, setAuditData] = useState<ComplianceAuditResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"ALL" | "HIGH" | "MEDIUM" | "LOW">("ALL");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);

    api
      .complianceAudit(document.document_id)
      .then((data) => {
        if (!cancelled) setAuditData(data);
      })
      .catch((err) => {
        console.error("Compliance audit failed:", err);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [document.document_id]);

  const findings = auditData?.audit_findings ?? [];
  const filteredFindings = findings.filter((f) => {
    if (filter === "ALL") return true;
    return f.risk_level === filter;
  });

  function handleFindingQuoteClick(finding: StatutoryAuditFinding) {
    if (!finding.contract_quote) return;
    onOpenQuote({
      sid: `audit-${finding.section}-${finding.contract_page}`,
      page: finding.contract_page,
      section: finding.section,
      quote: finding.contract_quote,
      ocr_derived: false,
    });
  }

  return (
    <section className="compliance-audit-panel" aria-labelledby="audit-heading">
      <div className="audit-header">
        <div>
          <span className="dataset-source-badge">
            ⚖️ Indian Statutory Compliance Engine
          </span>
          <h2 id="audit-heading">Statutory Compliance &amp; Risk Matrix</h2>
          <p className="hint">
            Cross-references clauses in <strong>{document.display_name}</strong> against the Indian
            Contract Act 1872, Transfer of Property Act 1882, Registration Act 1908, and Supreme
            Court precedents.
          </p>
        </div>

        {auditData ? (
          <div className="audit-metrics-row">
            <div className="metric-badge high">
              <span className="metric-count">{auditData.high_risk_count}</span>
              <span className="metric-label">High Risk / Void</span>
            </div>
            <div className="metric-badge medium">
              <span className="metric-count">{auditData.medium_risk_count}</span>
              <span className="metric-label">Caution / Limits</span>
            </div>
            <div className="metric-badge low">
              <span className="metric-count">{auditData.compliant_count}</span>
              <span className="metric-label">Compliant</span>
            </div>
          </div>
        ) : null}
      </div>

      {loading ? (
        <div className="audit-loading">
          <span className="spinner" /> Auditing agreement against Indian primary statutes...
        </div>
      ) : findings.length === 0 ? (
        <div className="audit-empty">
          <p>No statutory violations or high-risk clauses were detected in this agreement.</p>
        </div>
      ) : (
        <>
          <div className="audit-filters-bar">
            <span className="filter-label">Filter by risk:</span>
            <button
              type="button"
              className={`filter-pill ${filter === "ALL" ? "active" : ""}`}
              onClick={() => setFilter("ALL")}
            >
              All Clauses ({findings.length})
            </button>
            <button
              type="button"
              className={`filter-pill high ${filter === "HIGH" ? "active" : ""}`}
              onClick={() => setFilter("HIGH")}
            >
              🚩 High Risk ({auditData?.high_risk_count ?? 0})
            </button>
            <button
              type="button"
              className={`filter-pill medium ${filter === "MEDIUM" ? "active" : ""}`}
              onClick={() => setFilter("MEDIUM")}
            >
              ⚠️ Caution ({auditData?.medium_risk_count ?? 0})
            </button>
            <button
              type="button"
              className={`filter-pill low ${filter === "LOW" ? "active" : ""}`}
              onClick={() => setFilter("LOW")}
            >
              ✅ Compliant ({auditData?.compliant_count ?? 0})
            </button>
          </div>

          <div className="audit-findings-list">
            {filteredFindings.map((finding) => (
              <article
                key={`${finding.clause_category}-${finding.section}`}
                className={`audit-finding-card ${finding.risk_level.toLowerCase()}`}
              >
                <header className="finding-card-header">
                  <div className="finding-title-group">
                    <span
                      className={`status-pill ${finding.compliance_status.toLowerCase()}`}
                    >
                      {finding.compliance_status === "VOID_UNENFORCEABLE"
                        ? "🚩 Void Under Indian Law"
                        : finding.compliance_status === "CAUTION"
                          ? "⚠️ Caution / Subject to Legal Limits"
                          : "✅ Compliant Structure"}
                    </span>
                    <h3>{finding.clause_category}</h3>
                  </div>
                  <span className="statute-tag">{finding.statute}</span>
                </header>

                <div className="finding-body">
                  <div className="quote-container">
                    <span className="field-label">Detected Contract Passage:</span>
                    <button
                      type="button"
                      className="finding-quote-btn"
                      onClick={() => handleFindingQuoteClick(finding)}
                      title="Click to view on document page"
                    >
                      &ldquo;{finding.contract_quote}&rdquo;{" "}
                      <span className="page-indicator">(Page {finding.contract_page})</span>
                    </button>
                  </div>

                  <div className="legal-rule-box">
                    <div className="rule-header">
                      <strong>Statutory Rule ({finding.section}):</strong>
                      <span className="citation-text">{finding.statutory_citation}</span>
                    </div>
                    <p className="rule-text">{finding.legal_rule}</p>
                  </div>

                  {finding.relevant_precedent ? (
                    <div className="precedent-box">
                      <strong>Authoritative Precedent:</strong>{" "}
                      <span>{finding.relevant_precedent}</span>
                    </div>
                  ) : null}

                  <div className="explanation-box">
                    <p>{finding.explanation}</p>
                  </div>
                </div>

                {onAskClick ? (
                  <footer className="finding-footer">
                    <button
                      type="button"
                      className="ask-compliance-btn"
                      onClick={() =>
                        onAskClick(
                          `Does this clause comply with Indian law: "${finding.contract_quote}"? What does ${finding.section} say?`,
                        )
                      }
                    >
                      💬 Ask Chatbot about this finding
                    </button>
                  </footer>
                ) : null}
              </article>
            ))}
          </div>
        </>
      )}
    </section>
  );
}
