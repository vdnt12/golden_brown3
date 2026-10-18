import React from "react";

export type ProcessingStage = "uploading" | "reading" | "indexing" | "ready" | "failed";

interface ProcessingStatusProps {
  stage: ProcessingStage;
  filename: string;
  pages?: number | null;
  chunks?: number | null;
  error?: string | null;
  onReset?: () => void;
  onSummarize?: () => void;
  isSummarizing?: boolean;
}

export function ProcessingStatus({
  stage,
  filename,
  pages,
  chunks,
  error,
  onReset,
  onSummarize,
  isSummarizing,
}: ProcessingStatusProps) {
  return (
    <div className={`status-container stage-${stage}`}>
      <div className="status-header">
        <div className="status-file-info">
          <span className="file-icon">📁</span>
          <div>
            <strong className="status-filename">{filename}</strong>
            {pages ? (
              <span className="status-meta">
                {pages} page{pages === 1 ? "" : "s"}
                {chunks ? ` · ${chunks} chunks` : ""}
              </span>
            ) : null}
          </div>
        </div>

        <div className="header-actions">
          {stage === "ready" && onSummarize && (
            <button
              type="button"
              className="action-summarize-btn"
              onClick={onSummarize}
              disabled={isSummarizing}
              title="Generate a full document hierarchical summary"
            >
              📑 Summarize Document
            </button>
          )}

          {onReset && (
            <button
              type="button"
              className="reset-btn"
              onClick={onReset}
              title="Upload a new document"
            >
              Change Document
            </button>
          )}
        </div>
      </div>

      <div className="status-body">
        {stage === "uploading" && (
          <div className="status-indicator">
            <span className="spinner" />
            <span>Uploading document...</span>
          </div>
        )}

        {stage === "reading" && (
          <div className="status-indicator">
            <span className="spinner" />
            <span>Reading document and extracting text...</span>
          </div>
        )}

        {stage === "indexing" && (
          <div className="status-indicator">
            <span className="spinner" />
            <span>Creating searchable index and vectors...</span>
          </div>
        )}

        {stage === "ready" && (
          <div className="status-indicator ready">
            <span className="check-icon">✓</span>
            <span>Document ready — ask questions or click &ldquo;Summarize Document&rdquo;.</span>
          </div>
        )}

        {stage === "failed" && (
          <div className="status-indicator failed">
            <span className="error-icon">⚠️</span>
            <div>
              <strong>Document processing failed.</strong>
              <p className="error-desc">{error || "An unknown error occurred."}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
