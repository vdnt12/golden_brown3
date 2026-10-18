import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { ModelInfo } from "../types/api";

/**
 * Local model selector. Only allowlisted tags are shown, and an uninstalled
 * model is disabled rather than silently substituted. The backend records which
 * model answered in the run metadata.
 */
export function ModelPicker({
  value,
  onChange,
  disabled,
}: {
  value: string;
  onChange: (alias: string) => void;
  disabled?: boolean;
}) {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    api
      .models()
      .then((rows) => {
        if (cancelled) return;
        setModels(rows);
        const current = rows.find((row) => row.alias === value);
        if (!current?.available) {
          const fallback = rows.find((row) => row.available) ?? rows.find((row) => row.default);
          if (fallback && fallback.alias !== value) onChange(fallback.alias);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Model list unavailable.");
      });
    return () => {
      cancelled = true;
    };
    // Load once; the inventory is stable for a session.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const selected = models.find((row) => row.alias === value);
  const reachable = models.some((row) => row.ollama_reachable);

  return (
    <div className="model-picker">
      <label htmlFor="model-select">Answering model</label>
      <select
        id="model-select"
        value={value}
        disabled={disabled || models.length === 0}
        onChange={(event) => onChange(event.target.value)}
      >
        {models.length === 0 ? <option value={value}>Loading local models…</option> : null}
        {models.map((row) => (
          <option key={row.alias} value={row.alias} disabled={!row.available}>
            {row.label} — {row.available ? "installed" : "not installed"}
          </option>
        ))}
      </select>
      {selected && !selected.available ? (
        <p className="hint warn-text">
          {selected.tag} is not installed. Questions will return{" "}
          <code>ERROR_LOCAL_MODEL_UNAVAILABLE</code> instead of guessing.
        </p>
      ) : null}
      {!reachable && models.length > 0 ? (
        <p className="hint">
          No local Ollama was detected on <code>127.0.0.1:11434</code>. Start it with{" "}
          <code>OLLAMA_NO_CLOUD=1 ollama serve</code> and pull a model to get answers.
        </p>
      ) : null}
      {error ? <p className="error" role="alert">{error}</p> : null}
    </div>
  );
}
