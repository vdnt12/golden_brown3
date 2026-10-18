import React, { useState, useEffect } from "react";
import { FileUpload } from "./components/FileUpload";
import { ProcessingStatus, ProcessingStage } from "./components/ProcessingStatus";
import { ChatWindow } from "./components/ChatWindow";
import { uploadDocument, getDocumentStatus, deleteDocument, DocumentStatus } from "./services/api";

export default function App() {
  const [documentId, setDocumentId] = useState<string | null>(null);
  const [filename, setFilename] = useState<string>("");
  const [stage, setStage] = useState<ProcessingStage | "idle">("idle");
  const [docMeta, setDocMeta] = useState<DocumentStatus | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Poll status while processing
  useEffect(() => {
    if (!documentId || stage === "ready" || stage === "failed") return;

    const interval = setInterval(async () => {
      try {
        const status = await getDocumentStatus(documentId);
        setDocMeta(status);

        if (status.status === "ready") {
          setStage("ready");
          clearInterval(interval);
        } else if (status.status === "failed") {
          setStage("failed");
          setUploadError(status.error || "Document processing failed.");
          clearInterval(interval);
        } else {
          // Progress through stages
          setStage((prev) => (prev === "uploading" ? "reading" : "indexing"));
        }
      } catch (err) {
        clearInterval(interval);
      }
    }, 600);

    return () => clearInterval(interval);
  }, [documentId, stage]);

  const handleFileUpload = async (file: File) => {
    setUploadError(null);
    setFilename(file.name);
    setStage("uploading");
    setDocMeta(null);

    try {
      const res = await uploadDocument(file);
      setDocumentId(res.document_id);

      if (res.status === "ready") {
        setStage("ready");
        const status = await getDocumentStatus(res.document_id);
        setDocMeta(status);
      } else {
        setStage("reading");
      }
    } catch (err) {
      setStage("failed");
      setUploadError(err instanceof Error ? err.message : "Upload failed.");
    }
  };

  const handleResetDocument = async () => {
    if (documentId) {
      try {
        await deleteDocument(documentId);
      } catch (e) {
        console.warn("Delete error:", e);
      }
    }
    setDocumentId(null);
    setFilename("");
    setStage("idle");
    setDocMeta(null);
    setUploadError(null);
  };

  return (
    <div className="app-layout">
      <header className="app-header">
        <div className="header-brand">
          <span className="brand-logo">⚖️</span>
          <div>
            <h1 className="brand-name">GBDoc</h1>
            <p className="brand-sub">Document-Grounded RAG System</p>
          </div>
        </div>
        <div className="header-badge">
          <span>🔒 100% Grounded in Document · Zero Hallucination</span>
        </div>
      </header>

      <main className="main-content">
        {stage === "idle" ? (
          <div className="welcome-hero">
            <h2 className="hero-title">Chat with your document</h2>
            <p className="hero-subtitle">
              Upload a contract, agreement, or report. The system retrieves verified facts directly from your file.
            </p>
            <FileUpload onFileSelect={handleFileUpload} />
          </div>
        ) : (
          <div className="active-workspace">
            <ProcessingStatus
              stage={stage}
              filename={filename}
              pages={docMeta?.pages}
              chunks={docMeta?.chunks}
              error={uploadError || docMeta?.error}
              onReset={handleResetDocument}
            />

            {stage === "ready" && documentId && (
              <ChatWindow documentId={documentId} disabled={stage !== "ready"} />
            )}
          </div>
        )}
      </main>

      <footer className="app-footer">
        <p>
          GBDoc RAG Chatbot · The uploaded document is the sole source of truth. Unstated claims are strictly rejected.
        </p>
      </footer>
    </div>
  );
}
