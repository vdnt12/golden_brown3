import { useState } from "react";
import type { CUADAnalysisResponse, CUADFinding, DocumentSummary } from "../types/api";
import type { QuoteRef } from "./SourceQuote";

interface CUADReviewBannerProps {
  document: DocumentSummary;
  cuadData: CUADAnalysisResponse | null;
  loading: boolean;
  selectedModel: string;
  onModelChange: (model: string) => void;
  onOpenQuote: (ref: QuoteRef) => void;
  onAskClick?: (prefill?: string) => void;
}

export function CUADReviewBanner({
  document,
  cuadData,
  loading,
  selectedModel,
  onModelChange,
  onOpenQuote,
  onAskClick,
}: CUADReviewBannerProps) {
  const [showAllCategories, setShowAllCategories] = useState(false);

  // Extract key highlighted categories matching the CUAD reference design
  const findings = cuadData?.findings ?? [];
  const governingLaw = findings.find(
    (f) => f.category === "governing_law" || f.label === "Governing Law" || f.category === "Governing Law",
  );
  const covenantNotToSue = findings.find(
    (f) =>
      f.category === "covenant_not_to_sue" ||
      f.label === "Covenant Not to Sue" ||
      f.category === "Covenant Not to Sue",
  );
  const perpetualLicense = findings.find(
    (f) =>
      f.category === "perpetual_license" ||
      f.category === "license_grant" ||
      f.label.includes("License") ||
      f.label.includes("Perpetual") ||
      f.category.includes("license"),
  );

  const otherFindings = findings.filter(
    (f) =>
      f !== governingLaw &&
      f !== covenantNotToSue &&
      f !== perpetualLicense &&
      Boolean(f.quote),
  );

  function handleFindingClick(finding: CUADFinding) {
    if (!finding.quote) return;
    onOpenQuote({
      sid: finding.sid || `cuad-${finding.category}-${finding.page}`,
      page: finding.page,
      section: finding.section,
      quote: finding.quote,
      ocr_derived: false,
    });
  }

  return (
    <section className="cuad-banner" aria-label="CUAD Contract Analysis Pipeline">
      <div className="cuad-banner-header">
        <div className="cuad-brand">
          <span className="cuad-tag">CUAD 41-Category Model</span>
          <h3>Contract Understanding &amp; Analysis Architecture</h3>
        </div>
        <div className="cuad-actions">
          {onAskClick ? (
            <button
              type="button"
              className="chat-prompt-btn"
              onClick={() => onAskClick("Analyze the core risks and key clauses in this contract.")}
            >
              💬 Ask Chatbot
            </button>
          ) : null}
        </div>
      </div>

      <div className="cuad-pipeline">
        {/* Stage 1: Contract Input */}
        <div className="pipeline-card contract-card">
          <div className="card-badge">Input</div>
          <div className="contract-visual">
            <svg
              className="contract-icon-3d"
              viewBox="0 0 64 64"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              aria-hidden="true"
            >
              <rect
                x="8"
                y="14"
                width="40"
                height="46"
                rx="4"
                fill="#CBD5E1"
                transform="rotate(-5 8 14)"
              />
              <rect
                x="14"
                y="10"
                width="40"
                height="46"
                rx="4"
                fill="#94A3B8"
                transform="rotate(-2 14 10)"
              />
              <rect x="18" y="6" width="40" height="48" rx="4" fill="#FFFFFF" stroke="#0F172A" strokeWidth="2" />
              <line x1="24" y1="16" x2="48" y2="16" stroke="#0284C7" strokeWidth="2.5" strokeLinecap="round" />
              <line x1="24" y1="23" x2="52" y2="23" stroke="#64748B" strokeWidth="2" strokeLinecap="round" />
              <line x1="24" y1="29" x2="46" y2="29" stroke="#64748B" strokeWidth="2" strokeLinecap="round" />
              <line x1="24" y1="35" x2="50" y2="35" stroke="#64748B" strokeWidth="2" strokeLinecap="round" />
              <line x1="24" y1="41" x2="40" y2="41" stroke="#E11D48" strokeWidth="2" strokeLinecap="round" />
            </svg>
            <div className="contract-title-area">
              <span className="contract-label">Contract</span>
              <strong className="contract-filename" title={document.display_name}>
                {document.display_name}
              </strong>
            </div>
          </div>
          <div className="contract-meta">
            <span className="meta-pill">{document.source_kind.toUpperCase()}</span>
            <span className="meta-pill">{document.page_count} {document.page_count === 1 ? "page" : "pages"}</span>
            {document.ocr_used ? <span className="meta-pill ocr">OCR</span> : null}
          </div>
        </div>

        {/* Arrow 1 */}
        <div className="pipeline-connector" aria-hidden="true">
          <svg className="connector-arrow" viewBox="0 0 40 24" fill="none">
            <path
              d="M4 12H34M34 12L24 4M34 12L24 20"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>

        {/* Stage 2: Model Architecture */}
        <div className="pipeline-card model-card">
          <div className="card-badge">Neural Architecture</div>
          <div className="model-visual">
            <svg
              className="nn-diagram"
              viewBox="0 0 100 50"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              aria-label="Neural Network Diagram"
            >
              {/* Connections */}
              <line x1="15" y1="12" x2="50" y2="10" stroke="#38BDF8" strokeWidth="1" strokeOpacity="0.7" />
              <line x1="15" y1="12" x2="50" y2="25" stroke="#38BDF8" strokeWidth="1" strokeOpacity="0.7" />
              <line x1="15" y1="25" x2="50" y2="10" stroke="#38BDF8" strokeWidth="1" strokeOpacity="0.7" />
              <line x1="15" y1="25" x2="50" y2="25" stroke="#38BDF8" strokeWidth="1.5" strokeOpacity="0.9" />
              <line x1="15" y1="25" x2="50" y2="40" stroke="#38BDF8" strokeWidth="1" strokeOpacity="0.7" />
              <line x1="15" y1="38" x2="50" y2="25" stroke="#38BDF8" strokeWidth="1" strokeOpacity="0.7" />
              <line x1="15" y1="38" x2="50" y2="40" stroke="#38BDF8" strokeWidth="1" strokeOpacity="0.7" />

              <line x1="50" y1="10" x2="85" y2="18" stroke="#818CF8" strokeWidth="1.5" strokeOpacity="0.9" />
              <line x1="50" y1="10" x2="85" y2="32" stroke="#818CF8" strokeWidth="1" strokeOpacity="0.7" />
              <line x1="50" y1="25" x2="85" y2="18" stroke="#818CF8" strokeWidth="1.5" strokeOpacity="0.9" />
              <line x1="50" y1="25" x2="85" y2="32" stroke="#818CF8" strokeWidth="1.5" strokeOpacity="0.9" />
              <line x1="50" y1="40" x2="85" y2="18" stroke="#818CF8" strokeWidth="1" strokeOpacity="0.7" />
              <line x1="50" y1="40" x2="85" y2="32" stroke="#818CF8" strokeWidth="1.5" strokeOpacity="0.9" />

              {/* Layer 1 Nodes (Input) */}
              <circle cx="15" cy="12" r="4.5" fill="#0284C7" stroke="#BAE6FD" strokeWidth="1.5" />
              <circle cx="15" cy="25" r="4.5" fill="#0284C7" stroke="#BAE6FD" strokeWidth="1.5" />
              <circle cx="15" cy="38" r="4.5" fill="#0284C7" stroke="#BAE6FD" strokeWidth="1.5" />

              {/* Layer 2 Nodes (Hidden Dense) */}
              <circle cx="50" cy="10" r="4.5" fill="#6366F1" stroke="#C7D2FE" strokeWidth="1.5" />
              <circle cx="50" cy="25" r="5.5" fill="#4F46E5" stroke="#A5B4FC" strokeWidth="1.5" />
              <circle cx="50" cy="40" r="4.5" fill="#6366F1" stroke="#C7D2FE" strokeWidth="1.5" />

              {/* Layer 3 Nodes (Output Clauses) */}
              <circle cx="85" cy="18" r="4.5" fill="#10B981" stroke="#A7F3D0" strokeWidth="1.5" />
              <circle cx="85" cy="32" r="4.5" fill="#F59E0B" stroke="#FDE68A" strokeWidth="1.5" />
            </svg>
            <span className="model-label">Model</span>
          </div>

          <div className="model-selector-group">
            <button
              type="button"
              className={`model-pill ${selectedModel === "gemma" ? "active" : ""}`}
              onClick={() => onModelChange("gemma")}
              title="Google Gemma 4 E4B (Instruct 4-bit quantized)"
            >
              Gemma 4 E4B
            </button>
            <button
              type="button"
              className={`model-pill ${selectedModel === "gemma-e2b" ? "active" : ""}`}
              onClick={() => onModelChange("gemma-e2b")}
              title="Google Gemma 4 E2B (Compact)"
            >
              Gemma 4 E2B
            </button>
            <button
              type="button"
              className={`model-pill ${selectedModel === "hermes" ? "active" : ""}`}
              onClick={() => onModelChange("hermes")}
              title="Nous Research Hermes 3 8B (Llama-3.1)"
            >
              Hermes 3 8B
            </button>
          </div>
          <span className="model-subhint">Atticus CUAD 41 Categories</span>
        </div>

        {/* Arrow 2 */}
        <div className="pipeline-connector" aria-hidden="true">
          <svg className="connector-arrow" viewBox="0 0 40 24" fill="none">
            <path
              d="M4 12H34M34 12L24 4M34 12L24 20"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>

        {/* Stage 3: Output - Matches the reference image */}
        <div className="pipeline-card output-card">
          <div className="card-badge output-badge">Output</div>
          <h4 className="output-heading">Output</h4>

          {loading ? (
            <div className="output-loading">
              <span className="spinner" /> Analyzing 41 CUAD categories...
            </div>
          ) : (
            <div className="output-clauses">
              {/* 1. Governing Law */}
              <div className="clause-item">
                <div className="clause-title">
                  <strong>Governing Law</strong>
                </div>
                <div className="clause-body">
                  {governingLaw && governingLaw.quote ? (
                    <button
                      type="button"
                      className="clause-quote-btn"
                      onClick={() => handleFindingClick(governingLaw)}
                      title="Click to view on document page"
                    >
                      &ldquo;{governingLaw.quote}&rdquo;{" "}
                      <span className="page-tag">(Page {governingLaw.page ?? 1})</span>
                    </button>
                  ) : (
                    <span className="clause-none">Not specified in identified clauses</span>
                  )}
                </div>
              </div>

              {/* 2. Covenant Not to Sue */}
              <div className="clause-item">
                <div className="clause-title">
                  <span className="badge-icon" aria-hidden="true">⚠️</span>
                  <strong>Covenant Not to Sue</strong>
                </div>
                <div className="clause-body">
                  {covenantNotToSue && covenantNotToSue.quote ? (
                    <button
                      type="button"
                      className="clause-quote-btn warning"
                      onClick={() => handleFindingClick(covenantNotToSue)}
                      title="Click to view on document page"
                    >
                      &ldquo;{covenantNotToSue.quote}&rdquo;{" "}
                      <span className="page-tag warning">(Page {covenantNotToSue.page ?? 1})</span>
                    </button>
                  ) : (
                    <span className="clause-none">None detected in agreement text</span>
                  )}
                </div>
              </div>

              {/* 3. Perpetual / Irrevocable License */}
              <div className="clause-item">
                <div className="clause-title">
                  <span className="badge-icon" aria-hidden="true">🚩</span>
                  <strong>Perpetual / Irrevocable License</strong>
                </div>
                <div className="clause-body">
                  {perpetualLicense && perpetualLicense.quote ? (
                    <button
                      type="button"
                      className="clause-quote-btn danger"
                      onClick={() => handleFindingClick(perpetualLicense)}
                      title="Click to view on document page"
                    >
                      &ldquo;{perpetualLicense.quote}&rdquo;{" "}
                      <span className="page-tag danger">(Page {perpetualLicense.page ?? 1})</span>
                    </button>
                  ) : (
                    <span className="clause-none">None detected in agreement text</span>
                  )}
                </div>
              </div>
            </div>
          )}

          {otherFindings.length > 0 ? (
            <div className="cuad-extra-toggle">
              <button
                type="button"
                className="toggle-all-btn"
                onClick={() => setShowAllCategories((prev) => !prev)}
              >
                {showAllCategories
                  ? "Hide additional categories"
                  : `+ View ${otherFindings.length} more detected CUAD categories`}
              </button>
            </div>
          ) : null}
        </div>
      </div>

      {/* Expanded Categories Drawer */}
      {showAllCategories && otherFindings.length > 0 ? (
        <div className="cuad-expanded-grid">
          {otherFindings.map((finding) => (
            <div key={finding.category} className="expanded-clause-card">
              <header className="expanded-clause-header">
                <strong>{finding.category}</strong>
                {finding.page ? (
                  <span className="page-pill">Page {finding.page}</span>
                ) : null}
              </header>
              <p className="clause-desc">{finding.description}</p>
              <button
                type="button"
                className="clause-quote-btn"
                onClick={() => handleFindingClick(finding)}
              >
                &ldquo;{finding.quote}&rdquo;
              </button>
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}
