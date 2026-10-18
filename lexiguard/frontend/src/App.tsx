
import { useEffect, useState } from "react";
import { bootstrapSession } from "./api/session";
import { HomePage } from "./pages/HomePage";

type BootState =
  | { phase: "booting" }
  | { phase: "ready" }
  | { phase: "error"; message: string };

export default function App() {
  const [state, setState] = useState<BootState>({ phase: "booting" });

  useEffect(() => {
    let cancelled = false;
    bootstrapSession()
      .then(() => {
        if (!cancelled) setState({ phase: "ready" });
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setState({
          phase: "error",
          message: error instanceof Error ? error.message : "Session bootstrap failed.",
        });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (state.phase === "booting") {
    return (
      <main className="page">
        <p role="status">Starting a local session...</p>
      </main>
    );
  }

  if (state.phase === "error") {
    return (
      <main className="page" style={{ padding: "4rem 2rem", maxWidth: "600px", margin: "0 auto", textAlign: "center" }}>
        <h1>GBDoc Legal Workspace</h1>
        <p role="alert" style={{ color: "var(--vaquill-danger, #ef4444)", marginBottom: "1.5rem" }}>{state.message}</p>
        <button
          type="button"
          className="vaquill-btn-primary"
          onClick={() => {
            setState({ phase: "booting" });
            bootstrapSession()
              .then(() => setState({ phase: "ready" }))
              .catch((err: unknown) =>
                setState({
                  phase: "error",
                  message: err instanceof Error ? err.message : "Session bootstrap failed.",
                }),
              );
          }}
        >
          🚀 Launch GBDoc Dashboard
        </button>
      </main>
    );
  }

  return <HomePage />;
}
