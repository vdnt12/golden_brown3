export function PrivacyBanner() {
  return (
    <section className="privacy-banner" aria-label="Privacy summary">
      <p>
        <strong>Local by default.</strong> Documents are parsed, indexed and searched on this
        machine. Nothing is sent to a cloud service. Questions go only to the local model
        runtime on <code>127.0.0.1</code>; if it is not running, GBDoc returns an error
        instead of guessing.
      </p>
      <p className="hint">
        GBDoc is not a lawyer and does not give legal advice. It shows what the document
        says, where it says it, and what could not be found.
      </p>
    </section>
  );
}
