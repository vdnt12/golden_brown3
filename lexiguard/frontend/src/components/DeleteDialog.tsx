import { useState } from "react";
import { api } from "../api/client";
import type { DeletionResponse } from "../types/api";

/**
 * Delete asks for the exact confirmation word and then reports what was
 * actually removed. It never claims secure or forensic erasure.
 */
export function DeleteDialog({
  documentId,
  displayName,
  onDeleted,
}: {
  documentId: string;
  displayName: string;
  onDeleted: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [typed, setTyped] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [report, setReport] = useState<DeletionResponse | null>(null);

  async function remove() {
    setBusy(true);
    setError("");
    try {
      const result = await api.deleteDocument(documentId);
      setReport(result);
      onDeleted();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Deletion failed.");
    } finally {
      setBusy(false);
    }
  }

  if (report) {
    return (
      <section className="panel deletion-report" aria-labelledby="delete-report-heading">
        <h2 id="delete-report-heading">Deletion report</h2>
        <ul>
          <li>Files purged: {report.files_purged}</li>
          <li>SQLite index unlinked: {report.database_unlinked ? "yes" : "no"}</li>
          <li>Model cache eviction requested: {report.model_cache_evicted ? "yes" : "no"}</li>
          <li>Canary scan passed: {report.canary_scan_passed ? "yes" : "no"}</li>
          <li>Derived files left behind: {report.remaining_derived_files.length}</li>
        </ul>
        {report.remaining_derived_files.length ? (
          <p className="hint">Remaining: {report.remaining_derived_files.join(", ")}</p>
        ) : null}
        <p className="hint">{report.forensic_erasure_disclaimer}</p>
        {report.notes.map((note) => (
          <p className="hint" key={note}>{note}</p>
        ))}
      </section>
    );
  }

  if (!open) {
    return (
      <button type="button" className="danger" onClick={() => setOpen(true)}>
        Delete this document and its index
      </button>
    );
  }

  return (
    <section className="panel danger-panel" aria-labelledby="delete-heading">
      <h2 id="delete-heading">Delete &ldquo;{displayName}&rdquo;?</h2>
      <p>
        This removes the stored copy, the extracted text, the search index and the page
        images for this document from GBDoc&rsquo;s data folder. Your original file is
        untouched.
      </p>
      <label htmlFor="delete-confirm">
        Type <code>DELETE</code> to confirm
      </label>
      <input
        id="delete-confirm"
        value={typed}
        onChange={(event) => setTyped(event.target.value)}
        autoComplete="off"
      />
      {error ? <p className="error" role="alert">{error}</p> : null}
      <div className="row">
        <button
          type="button"
          className="danger"
          disabled={typed !== "DELETE" || busy}
          onClick={() => void remove()}
        >
          {busy ? "Deleting..." : "Delete permanently"}
        </button>
        <button type="button" onClick={() => setOpen(false)} disabled={busy}>
          Cancel
        </button>
      </div>
    </section>
  );
}
