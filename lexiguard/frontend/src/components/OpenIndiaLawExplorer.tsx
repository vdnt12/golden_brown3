import { useEffect, useState } from "react";
import { api } from "../api/client";
import type {
  EnactmentMetadata,
  PrecedentJudgment,
  StatutorySection,
} from "../types/api";

interface OpenIndiaLawExplorerProps {
  initialSearchQuery?: string;
  onAskQuestion?: (question: string) => void;
}

type FilterTab = "sections" | "judgments" | "enactments";

export function OpenIndiaLawExplorer({
  initialSearchQuery = "",
  onAskQuestion,
}: OpenIndiaLawExplorerProps) {
  const [activeTab, setActiveTab] = useState<FilterTab>("sections");
  const [searchTerm, setSearchTerm] = useState(initialSearchQuery);
  const [enactments, setEnactments] = useState<EnactmentMetadata[]>([]);
  const [sections, setSections] = useState<StatutorySection[]>([]);
  const [judgments, setJudgments] = useState<PrecedentJudgment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (initialSearchQuery) {
      setSearchTerm(initialSearchQuery);
    }
  }, [initialSearchQuery]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);

    Promise.all([api.enactments(), api.sections(), api.judgments()])
      .then(([acts, secs, juds]) => {
        if (!cancelled) {
          setEnactments(acts);
          setSections(secs);
          setJudgments(juds);
        }
      })
      .catch((err) => {
        console.error("Failed to load Open India Law data:", err);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const normalized = searchTerm.trim().toLowerCase();

  const filteredSections = sections.filter((s) => {
    if (!normalized) return true;
    return (
      s.section_number.toLowerCase().includes(normalized) ||
      s.title.toLowerCase().includes(normalized) ||
      s.act_name.toLowerCase().includes(normalized) ||
      s.text.toLowerCase().includes(normalized) ||
      s.keywords.some((k) => k.toLowerCase().includes(normalized))
    );
  });

  const filteredJudgments = judgments.filter((j) => {
    if (!normalized) return true;
    return (
      j.case_name.toLowerCase().includes(normalized) ||
      j.citation.toLowerCase().includes(normalized) ||
      j.issue.toLowerCase().includes(normalized) ||
      j.holding.toLowerCase().includes(normalized) ||
      j.sections_interpreted.some((s) => s.toLowerCase().includes(normalized))
    );
  });

  const filteredEnactments = enactments.filter((e) => {
    if (!normalized) return true;
    return (
      e.title.toLowerCase().includes(normalized) ||
      e.act_number.toLowerCase().includes(normalized) ||
      e.summary.toLowerCase().includes(normalized) ||
      e.jurisdiction.toLowerCase().includes(normalized)
    );
  });

  return (
    <section className="india-law-explorer" aria-labelledby="explorer-heading">
      <div className="explorer-header">
        <div>
          <span className="dataset-source-badge">
            🏛️ GBDoc / Open India Law Dataset
          </span>
          <h2 id="explorer-heading">Open India Law Primary Database</h2>
          <p className="hint">
            Official Indian primary law normalized from Ministry gazettes and Supreme Court records.
            Zero-hallucination statutory research and precedent citations.
          </p>
        </div>

        <div className="search-filter-box">
          <input
            type="search"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Filter sections, acts, or cases (e.g. S. 27, S. 74, Zaheer Khan)..."
            aria-label="Filter primary law database"
          />
        </div>
      </div>

      <nav className="explorer-tabs" role="tablist">
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === "sections"}
          className={`explorer-tab ${activeTab === "sections" ? "active" : ""}`}
          onClick={() => setActiveTab("sections")}
        >
          📜 Statutory Sections ({filteredSections.length})
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === "judgments"}
          className={`explorer-tab ${activeTab === "judgments" ? "active" : ""}`}
          onClick={() => setActiveTab("judgments")}
        >
          ⚖️ Supreme Court Precedents ({filteredJudgments.length})
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === "enactments"}
          className={`explorer-tab ${activeTab === "enactments" ? "active" : ""}`}
          onClick={() => setActiveTab("enactments")}
        >
          🏛️ Central &amp; State Acts ({filteredEnactments.length})
        </button>
      </nav>

      {loading ? (
        <div className="explorer-loading">
          <span className="spinner" /> Loading Open India Law primary dataset...
        </div>
      ) : (
        <div className="explorer-content">
          {/* Statutory Sections Tab */}
          {activeTab === "sections" ? (
            <div className="section-cards-grid">
              {filteredSections.map((sec) => (
                <article key={sec.section_id} className="statutory-card">
                  <header className="statutory-card-header">
                    <span className="act-pill">{sec.act_name}</span>
                    <strong className="sec-number">{sec.section_number}</strong>
                  </header>
                  <h3 className="sec-title">{sec.title}</h3>
                  <p className="sec-verbatim-text">&ldquo;{sec.text}&rdquo;</p>
                  <div className="sec-keywords">
                    {sec.keywords.map((kw) => (
                      <span key={kw} className="kw-pill">
                        #{kw}
                      </span>
                    ))}
                  </div>
                  <footer className="statutory-card-footer">
                    <span className="gazette-ref" title={sec.gazette_ref}>
                      Gazette: {sec.gazette_ref}
                    </span>
                    <div className="footer-actions">
                      <a
                        href={sec.source_url}
                        target="_blank"
                        rel="noreferrer"
                        className="official-link"
                      >
                        Official Source ↗
                      </a>
                      {onAskQuestion ? (
                        <button
                          type="button"
                          className="ask-law-btn"
                          onClick={() =>
                            onAskQuestion(
                              `Explain ${sec.section_number} of ${sec.act_name} (${sec.title}) and how it affects contracts.`,
                            )
                          }
                        >
                          Ask Chatbot
                        </button>
                      ) : null}
                    </div>
                  </footer>
                </article>
              ))}
            </div>
          ) : null}

          {/* Precedent Judgments Tab */}
          {activeTab === "judgments" ? (
            <div className="judgment-cards-grid">
              {filteredJudgments.map((j) => (
                <article key={j.judgment_id} className="precedent-card">
                  <header className="precedent-card-header">
                    <div className="court-badge">{j.court}</div>
                    <span className="judgment-date">{j.date}</span>
                  </header>
                  <h3 className="case-title">{j.case_name}</h3>
                  <div className="citation-badge">
                    <strong>Citation:</strong> {j.citation}
                  </div>
                  <div className="bench-info">
                    <strong>Bench:</strong> {j.bench}
                  </div>
                  <div className="interpreted-sections">
                    <strong>Sections Interpreted:</strong>{" "}
                    {j.sections_interpreted.join(", ")}
                  </div>
                  <div className="case-field">
                    <strong>Legal Issue:</strong>
                    <p>{j.issue}</p>
                  </div>
                  <div className="case-field holding-box">
                    <strong>Holding &amp; Ratio:</strong>
                    <p>{j.holding}</p>
                  </div>
                  <blockquote className="verbatim-quote">
                    &ldquo;{j.quote}&rdquo;
                  </blockquote>
                  <footer className="precedent-footer">
                    <a
                      href={j.source_url}
                      target="_blank"
                      rel="noreferrer"
                      className="official-link"
                    >
                      Supreme Court Record ↗
                    </a>
                    {onAskQuestion ? (
                      <button
                        type="button"
                        className="ask-law-btn"
                        onClick={() =>
                          onAskQuestion(
                            `How does the Supreme Court ruling in ${j.case_name} (${j.citation}) apply to contracts?`,
                          )
                        }
                      >
                        Ask Chatbot
                      </button>
                    ) : null}
                  </footer>
                </article>
              ))}
            </div>
          ) : null}

          {/* Enactments Tab */}
          {activeTab === "enactments" ? (
            <div className="enactment-cards-grid">
              {filteredEnactments.map((act) => (
                <article key={act.act_id} className="enactment-card">
                  <header className="enactment-card-header">
                    <span className="jurisdiction-pill">{act.jurisdiction}</span>
                    <span className="act-year">{act.year}</span>
                  </header>
                  <h3 className="act-title">{act.title}</h3>
                  <p className="act-number-txt">{act.act_number}</p>
                  <p className="act-summary">{act.summary}</p>
                  <div className="act-details">
                    <span>Ministry: {act.ministry}</span>
                    <span>Total Sections: {act.total_sections}</span>
                  </div>
                  <footer className="enactment-footer">
                    <a
                      href={act.source_url}
                      target="_blank"
                      rel="noreferrer"
                      className="official-link"
                    >
                      India Code / Official Text ↗
                    </a>
                  </footer>
                </article>
              ))}
            </div>
          ) : null}
        </div>
      )}
    </section>
  );
}
