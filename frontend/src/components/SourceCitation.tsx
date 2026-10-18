import React from "react";
import { ChatSourceItem } from "../services/api";

interface SourceCitationProps {
  sources: ChatSourceItem[];
}

export function SourceCitation({ sources }: SourceCitationProps) {
  if (!sources || sources.length === 0) return null;

  return (
    <div className="citations-container">
      <span className="citations-label">Sources:</span>
      <div className="citations-list">
        {sources.map((s, idx) => (
          <div key={`${s.chunk_id}-${idx}`} className="citation-badge">
            <span className="citation-icon">📌</span>
            {s.page ? <span className="citation-page">Page {s.page}</span> : null}
            <span className="citation-file">{s.filename}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
