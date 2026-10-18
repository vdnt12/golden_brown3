import { useState } from "react";

interface VaquillHeaderProps {
  onSearch: (query: string) => void;
  activeDocumentName?: string | null;
}

export function VaquillHeader({ onSearch, activeDocumentName }: VaquillHeaderProps) {
  const [searchQuery, setSearchQuery] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (searchQuery.trim()) {
      onSearch(searchQuery.trim());
    }
  }

  return (
    <header className="vaquill-header" aria-label="GBDoc Top Navigation">
      <div className="vaquill-brand-row">
        <div className="vaquill-logo-group">
          <div className="vaquill-badge-icon" aria-hidden="true">
            ⚖️
          </div>
          <div>
            <div className="vaquill-brand-title">
              <span className="brand-primary">GB</span>
              <span className="brand-accent">Doc</span>
              <span className="brand-subtag">Legal Intelligence</span>
            </div>
            <p className="vaquill-brand-tagline">
              Powered by Open India Law Dataset &amp; CUAD 41-Category Clause Intelligence
            </p>
          </div>
        </div>

        <div className="vaquill-header-meta">
          {activeDocumentName ? (
            <div className="active-matter-pill" title={activeDocumentName}>
              <span className="matter-dot" />
              <span className="matter-label">Active Matter:</span>
              <strong className="matter-name">{activeDocumentName}</strong>
            </div>
          ) : null}
          <div className="privacy-chip">
            <span>🔒 Local &amp; Private</span>
          </div>
        </div>
      </div>

      <form className="vaquill-global-search" onSubmit={handleSubmit}>
        <div className="search-input-wrapper">
          <span className="search-icon" aria-hidden="true">
            🔍
          </span>
          <input
            type="search"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search Open India Law: Central Acts, Sections (e.g. S. 27, S. 74), Supreme Court Precedents..."
            aria-label="Search Open India Law"
          />
          <button type="submit" className="search-submit-btn">
            Search Law
          </button>
        </div>
      </form>
    </header>
  );
}
