import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import { AskPanel } from "../components/AskPanel";
import { ComplianceAuditPanel } from "../components/ComplianceAuditPanel";
import { CUADReviewBanner } from "../components/CUADReviewBanner";
import { DeleteDialog } from "../components/DeleteDialog";
import { DocumentMap } from "../components/DocumentMap";
import { OpenIndiaLawExplorer } from "../components/OpenIndiaLawExplorer";
import { PageViewer } from "../components/PageViewer";
import { PrivacyBanner } from "../components/PrivacyBanner";
import { ReviewPanel } from "../components/ReviewPanel";
import type { QuoteRef } from "../components/SourceQuote";
import { UploadPanel } from "../components/UploadPanel";
import { VaquillHeader } from "../components/VaquillHeader";
import type {
  CUADAnalysisResponse,
  DocumentSummary,
  OverviewResponse,
  ReviewResponse,
} from "../types/api";

type Tab = "ask" | "contract_review" | "compliance" | "open_india_law" | "overview";

export function HomePage() {
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("ask");
  const [overview, setOverview] = useState<OverviewResponse | null>(null);
  const [review, setReview] = useState<ReviewResponse | null>(null);
  const [cuadData, setCuadData] = useState<CUADAnalysisResponse | null>(null);
  const [cuadLoading, setCuadLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState("gemma");
  const [chatPrompt, setChatPrompt] = useState<string | undefined>(undefined);
  const [lawSearchQuery, setLawSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [quote, setQuote] = useState<QuoteRef | null>(null);
  const [viewerPage, setViewerPage] = useState(1);
  const [viewerOpen, setViewerOpen] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const list = await api.listDocuments();
      setDocuments(list);
      setActiveId((current) => {
        if (current && list.some((doc) => doc.document_id === current)) return current;
        return list[0]?.document_id ?? null;
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not read the document list.");
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const active = documents.find((doc) => doc.document_id === activeId) ?? null;

  useEffect(() => {
    setOverview(null);
    setReview(null);
    setCuadData(null);
    if (!activeId) return;

    let cancelled = false;
    setLoading(true);
    setCuadLoading(true);
    setError("");

    api
      .overview(activeId)
      .then((body) => {
        if (!cancelled) setOverview(body);
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Overview failed.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    api
      .cuad(activeId)
      .then((data) => {
        if (!cancelled) setCuadData(data);
      })
      .catch((err: unknown) => {
        console.warn("CUAD analysis request failed:", err);
      })
      .finally(() => {
        if (!cancelled) setCuadLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [activeId]);

  useEffect(() => {
    if (tab !== "contract_review" || !activeId || review) return;
    let cancelled = false;
    api
      .review(activeId)
      .then((body) => {
        if (!cancelled) setReview(body);
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Review failed.");
      });
    return () => {
      cancelled = true;
    };
  }, [tab, activeId, review]);

  const openQuote = useCallback((ref: QuoteRef) => {
    setQuote(ref);
    setViewerPage(ref.page);
    setViewerOpen(true);
  }, []);

  const handleAskPrefill = (prefill?: string) => {
    setTab("ask");
    setChatPrompt(prefill);
  };

  const handleGlobalLawSearch = (query: string) => {
    setLawSearchQuery(query);
    setTab("open_india_law");
  };

  return (
    <main className="page vaquill-dashboard">
      <VaquillHeader
        onSearch={handleGlobalLawSearch}
        activeDocumentName={active?.display_name}
      />

      <PrivacyBanner />

      <UploadPanel
        disabled={false}
        onUploaded={(uploaded) => {
          setActiveId(uploaded.document_id);
          setTab("ask");
          setQuote(null);
          void refresh();
        }}
      />

      {error ? <p className="error" role="alert">{error}</p> : null}

      {documents.length === 0 ? (
        <>
          <section className="feature-showcase-grid" aria-label="GBDoc capabilities">
            <div className="showcase-card">
              <div className="showcase-icon">📜</div>
              <h3 className="showcase-title">Atticus CUAD 41 Categories</h3>
              <p className="showcase-desc">
                Automated contract clause extraction based on The Atticus Project benchmark. Flags covenants not to sue, perpetual licenses, and non-competes.
              </p>
            </div>
            <div className="showcase-card">
              <div className="showcase-icon">⚖️</div>
              <h3 className="showcase-title">Statutory Compliance Audit</h3>
              <p className="showcase-desc">
                Cross-references clauses against Indian Contract Act (S. 27, 28, 74), Registration Act (S. 17), and Easements Act (S. 60) with Supreme Court rulings.
              </p>
            </div>
            <div className="showcase-card">
              <div className="showcase-icon">💬</div>
              <h3 className="showcase-title">GBDoc Grounded Chatbot</h3>
              <p className="showcase-desc">
                Query contract obligations, breach consequences, and statutory rights. Every answer cites exact sentences or gazette provisions.
              </p>
            </div>
            <div className="showcase-card">
              <div className="showcase-icon">🏛️</div>
              <h3 className="showcase-title">Open India Law Library</h3>
              <p className="showcase-desc">
                Direct access to Central &amp; State Acts from indiacode.gov.in, verbatim sections, and landmark Supreme Court ratios.
              </p>
            </div>
          </section>

          <section className="standalone-explorer-section" style={{ marginTop: "1.5rem" }}>
            <OpenIndiaLawExplorer initialSearchQuery={lawSearchQuery} />
          </section>
        </>
      ) : (
        <>
          <section className="panel matter-docs-panel" aria-labelledby="docs-heading">
            <div className="section-head-row">
              <h2 id="docs-heading">Active Matters &amp; Documents ({documents.length})</h2>
              <span className="source-tag">Input Agreements</span>
            </div>
            <ul className="doc-list">
              {documents.map((doc) => (
                <li key={doc.document_id}>
                  <button
                    type="button"
                    className={doc.document_id === activeId ? "doc-item active" : "doc-item"}
                    onClick={() => {
                      setActiveId(doc.document_id);
                      setQuote(null);
                    }}
                  >
                    <span className="doc-name">{doc.display_name}</span>
                    <span className="hint">
                      {doc.page_count} page{doc.page_count === 1 ? "" : "s"} · {doc.source_kind.toUpperCase()}
                      {doc.ocr_used ? " · OCR used" : ""}
                      {doc.unread_pages ? ` · ${doc.unread_pages} unread page(s)` : ""}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </section>

          {active ? (
            <section className="workspace" aria-label="Document workspace">
              {/* CUAD Visual Banner matching the reference diagram */}
              <CUADReviewBanner
                document={active}
                cuadData={cuadData}
                loading={cuadLoading}
                selectedModel={selectedModel}
                onModelChange={setSelectedModel}
                onOpenQuote={openQuote}
                onAskClick={handleAskPrefill}
              />

              {/* Dashboard Tabs */}
              <nav className="tabs vaquill-nav-tabs" role="tablist" aria-label="Dashboard views">
                <button
                  type="button"
                  role="tab"
                  aria-selected={tab === "ask"}
                  className={`tab ${tab === "ask" ? "active" : ""}`}
                  onClick={() => setTab("ask")}
                >
                  💬 GBDoc AI Chatbot
                </button>
                <button
                  type="button"
                  role="tab"
                  aria-selected={tab === "compliance"}
                  className={`tab ${tab === "compliance" ? "active" : ""}`}
                  onClick={() => setTab("compliance")}
                >
                  ⚖️ Statutory Compliance Audit
                </button>
                <button
                  type="button"
                  role="tab"
                  aria-selected={tab === "contract_review"}
                  className={`tab ${tab === "contract_review" ? "active" : ""}`}
                  onClick={() => setTab("contract_review")}
                >
                  📄 Reading Order Review
                </button>
                <button
                  type="button"
                  role="tab"
                  aria-selected={tab === "open_india_law"}
                  className={`tab ${tab === "open_india_law" ? "active" : ""}`}
                  onClick={() => setTab("open_india_law")}
                >
                  🏛️ Open India Law Library
                </button>
                <button
                  type="button"
                  role="tab"
                  aria-selected={tab === "overview"}
                  className={`tab ${tab === "overview" ? "active" : ""}`}
                  onClick={() => setTab("overview")}
                >
                  📑 Document Map
                </button>
              </nav>

              <div className="workspace-body">
                <div className="workspace-main">
                  {loading && !overview ? <p role="status">Reading the document...</p> : null}

                  {/* 1. Chatbot Assistant */}
                  {tab === "ask" ? (
                    <AskPanel
                      documentId={active.document_id}
                      disabled={false}
                      onOpenQuote={openQuote}
                      initialQuestion={chatPrompt}
                    />
                  ) : null}

                  {/* 2. Statutory Compliance Audit */}
                  {tab === "compliance" ? (
                    <ComplianceAuditPanel
                      document={active}
                      onOpenQuote={openQuote}
                      onAskClick={handleAskPrefill}
                    />
                  ) : null}

                  {/* 3. Contract Review (Reading Order) */}
                  {tab === "contract_review" && review ? (
                    <ReviewPanel review={review} onOpenQuote={openQuote} />
                  ) : null}
                  {tab === "contract_review" && !review ? (
                    <p role="status">Checking conflicts, ambiguity, money and jurisdiction...</p>
                  ) : null}

                  {/* 4. Open India Law Library */}
                  {tab === "open_india_law" ? (
                    <OpenIndiaLawExplorer
                      initialSearchQuery={lawSearchQuery}
                      onAskQuestion={handleAskPrefill}
                    />
                  ) : null}

                  {/* 5. Document Map */}
                  {tab === "overview" && overview ? (
                    <DocumentMap overview={overview} onOpenQuote={openQuote} />
                  ) : null}

                  <div className="delete-zone">
                    <DeleteDialog
                      documentId={active.document_id}
                      displayName={active.display_name}
                      onDeleted={() => {
                        setDocuments((current) =>
                          current.filter((doc) => doc.document_id !== active.document_id),
                        );
                        setOverview(null);
                        setReview(null);
                        setCuadData(null);
                        setActiveId(null);
                        setViewerOpen(false);
                        void refresh();
                      }}
                    />
                  </div>
                </div>

                {viewerOpen ? (
                  <PageViewer
                    documentId={active.document_id}
                    page={viewerPage}
                    quote={quote}
                    onClose={() => setViewerOpen(false)}
                  />
                ) : (
                  <aside className="page-viewer page-viewer-empty">
                    <p className="hint">
                      Click any citation or quotation to see it in context on its page, with
                      the stored text and rendered scan.
                    </p>
                  </aside>
                )}
              </div>
            </section>
          ) : null}
        </>
      )}

      {/* Global Open India Law Explorer when no document is uploaded */}
      {documents.length === 0 && tab === "open_india_law" ? (
        <section className="standalone-explorer-section">
          <OpenIndiaLawExplorer initialSearchQuery={lawSearchQuery} />
        </section>
      ) : null}

      <footer className="page-footer">
        <p>
          GBDoc · Legal Intelligence &amp; Open India Law Dataset Integration. All answers and
          verdicts are strictly grounded in official statutory records and uploaded contract text.
          Not a substitute for formal legal counsel.
        </p>
      </footer>
    </main>
  );
}
