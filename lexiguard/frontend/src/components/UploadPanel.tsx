import { useRef, useState, type DragEvent } from "react";
import { api } from "../api/client";
import type { UploadResponse } from "../types/api";

const MAX_BYTES = 20 * 1024 * 1024;

const SAMPLE_COMMERCIAL_LEASE = `COMMERCIAL LEASE & SERVICES AGREEMENT

This Agreement is made on this 1st day of January 2026 at Mumbai, Maharashtra between Alpha Commercial Properties ("Landlord") and Beta Technologies Pvt Ltd ("Tenant").

1. Governing Law & Jurisdiction: This agreement shall be governed by the laws of India and the courts at Mumbai shall have exclusive jurisdiction.

2. Covenant Not to Sue: The Tenant covenants not to sue or initiate any litigation against the Landlord regarding prior premises maintenance.

3. Perpetual License: Landlord hereby grants Tenant a perpetual, irrevocable, worldwide license to use the building HVAC software.

4. Non-Compete: The Tenant shall not engage in any competitive co-working or commercial leasing business within 5 km for 3 years post-termination.

5. Security Deposit & Forfeiture: Tenant has deposited an interest-free security deposit of Rs. 10,00,000. In case of any early termination during the 36-month lock-in period, the entire deposit shall be forfeited as liquidated damages and penalty.

6. Term & Registration: The lease term is for 36 months, executed on an unregistered stamp paper.

7. Cap on Liability: The aggregate liability of Landlord shall not exceed Rs. 50,000 under any circumstances.
`;

const SAMPLE_EMPLOYMENT_AGREEMENT = `EXECUTIVE EMPLOYMENT & CONFIDENTIALITY AGREEMENT

This Agreement is entered into between Zenith Software India Private Limited ("Company") and the Employee.

1. Term & Position: The Executive agrees to serve the Company in a full-time capacity for 24 months.

2. Post-Termination Non-Compete: For a period of 24 months following termination of employment for any reason, the Executive shall not directly or indirectly engage in, consult for, or establish any business competing with the Company in India.

3. Restraint of Legal Proceedings: The Executive covenants not to sue and waives all rights to initiate litigation against the Company before ordinary civil courts.

4. Liquidated Damages & Penalties: In event of breach, the entire deposit and performance bonus shall be forfeited as penalty.

5. Intellectual Property & Inventions: All inventions and intellectual property created by Executive shall remain the exclusive property of Company in perpetuity.
`;

export function UploadPanel({
  onUploaded,
  disabled,
}: {
  onUploaded: (document: UploadResponse) => void;
  disabled?: boolean;
}) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [busy, setBusy] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [warnings, setWarnings] = useState<UploadResponse["extraction_warnings"]>([]);

  async function upload(file: File) {
    setError("");
    setMessage("");
    setWarnings([]);
    if (file.size > MAX_BYTES) {
      setError("File exceeds 20 MB limit. Please upload a contract up to 20 MB.");
      return;
    }
    const lower = file.name.toLowerCase();
    if (!lower.endsWith(".pdf") && !lower.endsWith(".txt")) {
      setError("Only PDF (.pdf) and plain-text (.txt) agreements are supported.");
      return;
    }
    setBusy(true);
    try {
      const document = await api.uploadDocument(file);
      const metrics = document.quality_metrics;
      const notes = [
        `${document.page_count} page${document.page_count === 1 ? "" : "s"}`,
        `${document.readable_pages} readable`,
        metrics.ocr_used ? "OCR text layer" : "text stream",
        `language: ${metrics.language_detected}`,
      ];
      if (metrics.hidden_text_detected) notes.push("possible hidden text");
      if (document.status === "PARTIAL") notes.push("some pages unread");
      setMessage(`Successfully ingested "${document.display_name}" (${notes.join(" · ")}).`);
      setWarnings(document.extraction_warnings);
      onUploaded(document);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setBusy(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setIsDragging(false);
    if (disabled || busy) return;
    const file = e.dataTransfer.files?.[0];
    if (file) void upload(file);
  }

  function loadSample(title: string, content: string) {
    if (disabled || busy) return;
    const blob = new Blob([content], { type: "text/plain" });
    const file = new File([blob], title, { type: "text/plain" });
    void upload(file);
  }

  return (
    <section className="vaquill-upload-container panel" aria-labelledby="upload-heading">
      <div className="vaquill-upload-header">
        <div>
          <h2 id="upload-heading" className="vaquill-panel-title">
            📄 Upload Legal Agreement &amp; Contract
          </h2>
          <p className="vaquill-panel-subtitle">
            Upload any PDF or TXT contract for instant <strong>Atticus CUAD (41 categories)</strong> clause review, 
            <strong>Open India Law</strong> compliance audit, and grounded legal chatbot assistance.
          </p>
        </div>
        <div className="vaquill-badge vaquill-badge-secure">
          🔒 Local Privacy · Zero External Leakage
        </div>
      </div>

      <div
        className={`vaquill-dropzone ${isDragging ? "dragging" : ""} ${busy ? "busy" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.txt,application/pdf,text/plain"
          disabled={busy || disabled}
          style={{ display: "none" }}
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) void upload(file);
          }}
          aria-label="Upload PDF or text agreement"
        />

        <div className="dropzone-icon">📁</div>
        <div className="dropzone-content">
          <p className="dropzone-title">
            {busy ? "Parsing & Indexing Agreement Locally..." : "Click or drag & drop agreement here"}
          </p>
          <p className="dropzone-hint">
            Supports PDF and TXT up to 20 MB · Automatic page-by-page tokenization &amp; SQLite FTS indexing
          </p>
        </div>
        <button
          type="button"
          className="vaquill-btn-secondary browse-btn"
          disabled={busy || disabled}
          onClick={(e) => {
            e.stopPropagation();
            inputRef.current?.click();
          }}
        >
          {busy ? "Ingesting..." : "Browse Local File"}
        </button>
      </div>

      {/* Quick 1-Click Sample Ingestion */}
      <div className="sample-contracts-bar">
        <span className="sample-label">⚡ Quick Demo Samples:</span>
        <button
          type="button"
          className="sample-chip"
          disabled={busy || disabled}
          onClick={() => loadSample("commercial_lease_mumbai.txt", SAMPLE_COMMERCIAL_LEASE)}
        >
          🏢 Commercial Lease (36-mo, Lock-in, S.27 &amp; S.74)
        </button>
        <button
          type="button"
          className="sample-chip"
          disabled={busy || disabled}
          onClick={() => loadSample("executive_employment_agreement.txt", SAMPLE_EMPLOYMENT_AGREEMENT)}
        >
          💼 Employment Agreement (Non-Compete &amp; S.27 Voidness)
        </button>
      </div>

      {message ? (
        <div className="vaquill-alert vaquill-alert-success" role="status">
          ✓ {message}
        </div>
      ) : null}

      {warnings.length ? (
        <ul className="warnings">
          {warnings.map((warning) => (
            <li key={`${warning.code}-${warning.message}`}>
              <span className="warning-code">{warning.code.split("_").join(" ").toLowerCase()}</span>{" "}
              {warning.message}
            </li>
          ))}
        </ul>
      ) : null}

      {error ? (
        <div className="vaquill-alert vaquill-alert-danger" role="alert">
          ⚠️ {error}
        </div>
      ) : null}
    </section>
  );
}
