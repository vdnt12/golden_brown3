import { useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import type { RenderedAnswer } from "../types/api";
import { AnswerView } from "./AnswerView";
import { ModelPicker } from "./ModelPicker";
import type { QuoteRef } from "./SourceQuote";

type ChatMode = "document" | "indian_law" | "compliance";

const CONTRACT_SUGGESTIONS = [
  "What is the monthly rent, maintenance, and due date?",
  "What notice period applies if either party terminates?",
  "How much is the security deposit, and when is it refunded?",
  "Who is responsible for repairs and structural maintenance?",
  "What are the lock-in conditions and early exit terms?",
];

const INDIAN_LAW_SUGGESTIONS = [
  "What does Section 27 of the Indian Contract Act say about non-compete clauses?",
  "Can a landlord forfeit the entire security deposit under Section 74?",
  "What is the distinction between a Lease and Leave & License in Indian law?",
  "Are 11-month tenancy agreements exempt from registration under Section 17?",
  "What does Supreme Court rule in Percept D'Mark v. Zaheer Khan?",
];

const COMPLIANCE_SUGGESTIONS = [
  "Does the non-compete or restraint clause in this contract comply with Section 27?",
  "Are the deposit forfeiture terms compliant with Section 74 of the Contract Act?",
  "Does this agreement require mandatory registration under the Registration Act or state law?",
  "Is the governing law and dispute jurisdiction clause valid under Indian law?",
];

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text?: string;
  answer?: RenderedAnswer;
  error?: string;
  loading?: boolean;
  mode?: ChatMode;
}

export function AskPanel({
  documentId,
  disabled,
  onOpenQuote,
  initialQuestion,
}: {
  documentId: string;
  disabled?: boolean;
  onOpenQuote: (ref: QuoteRef) => void;
  initialQuestion?: string;
}) {
  const [mode, setMode] = useState<ChatMode>("document");
  const [question, setQuestion] = useState("");
  const [model, setModel] = useState("gemma");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [busy, setBusy] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMessages([]);
  }, [documentId]);

  useEffect(() => {
    if (initialQuestion && !busy) {
      void submit(initialQuestion);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialQuestion]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  async function submit(text: string) {
    const trimmed = text.trim();
    if (!trimmed || busy) return;

    const userMsgId = `user-${Date.now()}`;
    const assistantMsgId = `assistant-${Date.now()}`;

    setMessages((prev) => [
      ...prev,
      { id: userMsgId, role: "user", text: trimmed, mode },
      { id: assistantMsgId, role: "assistant", loading: true, mode },
    ]);
    setQuestion("");
    setBusy(true);

    try {
      const result = await api.ask(documentId, trimmed, model, true);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantMsgId ? { ...m, loading: false, answer: result } : m,
        ),
      );
    } catch (err) {
      const errMsg =
        err instanceof Error ? err.message : "The question could not be answered.";
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantMsgId ? { ...m, loading: false, error: errMsg } : m,
        ),
      );
    } finally {
      setBusy(false);
    }
  }

  const currentSuggestions =
    mode === "indian_law"
      ? INDIAN_LAW_SUGGESTIONS
      : mode === "compliance"
        ? COMPLIANCE_SUGGESTIONS
        : CONTRACT_SUGGESTIONS;

  return (
    <section className="ask-chatbot-panel" aria-labelledby="ask-heading">
      <div className="section-head chatbot-head">
        <div>
          <span className="dataset-source-badge">
            💬 GBDoc AI Dual-Grounding Assistant
          </span>
          <h2 id="ask-heading">Legal Chatbot Assistant</h2>
          <p className="hint">
            Directly grounded in your uploaded agreement and the <strong>Open India Law</strong> primary
            dataset. Answers provide verbatim quotes with verifiable citations.
          </p>
        </div>
        {messages.length > 0 ? (
          <button
            type="button"
            className="clear-chat-btn"
            onClick={() => setMessages([])}
            disabled={busy}
          >
            Clear conversation
          </button>
        ) : null}
      </div>

      {/* Chat Mode Switcher */}
      <div className="chat-mode-tabs" role="tablist" aria-label="Chat query mode">
        <button
          type="button"
          role="tab"
          aria-selected={mode === "document"}
          className={`mode-tab ${mode === "document" ? "active" : ""}`}
          onClick={() => setMode("document")}
          disabled={busy}
        >
          📄 Chat with Contract
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={mode === "indian_law"}
          className={`mode-tab ${mode === "indian_law" ? "active" : ""}`}
          onClick={() => setMode("indian_law")}
          disabled={busy}
        >
          🏛️ Research Open India Law
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={mode === "compliance"}
          className={`mode-tab ${mode === "compliance" ? "active" : ""}`}
          onClick={() => setMode("compliance")}
          disabled={busy}
        >
          ⚖️ Statutory Compliance Audit
        </button>
      </div>

      <div className="model-selection-bar">
        <ModelPicker value={model} onChange={setModel} disabled={disabled || busy} />
      </div>

      {/* Chat conversation area */}
      <div className="chat-thread" role="log" aria-live="polite">
        {messages.length === 0 ? (
          <div className="chat-welcome">
            <div className="welcome-icon">
              {mode === "indian_law" ? "🏛️" : mode === "compliance" ? "⚖️" : "💬"}
            </div>
            <h3>
              {mode === "indian_law"
                ? "Research Indian Primary Law & Judgments"
                : mode === "compliance"
                  ? "Audit Contract Against Indian Statutes"
                  : "How can I assist with this contract?"}
            </h3>
            <p className="hint">
              {mode === "indian_law"
                ? "Search Central Acts (Contract Act, TPA, Registration Act) and Supreme Court holdings from the Open India Law dataset."
                : mode === "compliance"
                  ? "Select a compliance question to evaluate non-competes, deposit forfeiture, or lease terms under Indian law."
                  : "Select a suggestion below or type any question about the uploaded document."}
            </p>

            <div className="chat-suggestions-grid">
              {currentSuggestions.map((suggestion) => (
                <button
                  type="button"
                  key={suggestion}
                  className="suggestion-bubble"
                  disabled={disabled || busy}
                  onClick={() => void submit(suggestion)}
                >
                  <span className="suggestion-arrow">→</span>
                  <span>{suggestion}</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="message-list">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`chat-bubble-container ${msg.role === "user" ? "user-container" : "assistant-container"}`}
              >
                {msg.role === "user" ? (
                  <div className="chat-bubble user-bubble">
                    <div className="bubble-header">
                      <span className="bubble-author">You</span>
                    </div>
                    <p className="bubble-text">{msg.text}</p>
                  </div>
                ) : (
                  <div className="chat-bubble assistant-bubble">
                    <div className="bubble-header">
                      <span className="bubble-author">
                        GBDoc AI (
                        {model === "hermes"
                          ? "Hermes 3"
                          : model === "gemma-e2b"
                            ? "Gemma 4 E2B"
                            : "Gemma 4 E4B"}
                        )
                      </span>
                    </div>
                    {msg.loading ? (
                      <div className="assistant-loading">
                        <span className="spinner" />
                        <span>Retrieving verified evidence and analyzing law...</span>
                      </div>
                    ) : msg.error ? (
                      <div className="chat-error" role="alert">
                        <p>{msg.error}</p>
                      </div>
                    ) : msg.answer ? (
                      <div className="assistant-answer-payload">
                        <AnswerView answer={msg.answer} onOpenQuote={onOpenQuote} />
                      </div>
                    ) : null}
                  </div>
                )}
              </div>
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* Suggested prompts footer bar when chat is active */}
      {messages.length > 0 ? (
        <div className="active-chat-suggestions">
          <span className="suggestions-label">Suggestions:</span>
          {currentSuggestions.slice(0, 3).map((suggestion) => (
            <button
              type="button"
              key={suggestion}
              className="chip compact"
              disabled={disabled || busy}
              onClick={() => void submit(suggestion)}
            >
              {suggestion}
            </button>
          ))}
        </div>
      ) : null}

      {/* Input bar */}
      <form
        className="chat-input-bar"
        onSubmit={(event) => {
          event.preventDefault();
          void submit(question);
        }}
      >
        <div className="chat-input-wrapper">
          <textarea
            id="chat-question-input"
            value={question}
            maxLength={600}
            rows={2}
            placeholder={
              mode === "indian_law"
                ? "Ask about Indian statutes or Supreme Court precedent (e.g. What does Section 27 state?)..."
                : mode === "compliance"
                  ? "Ask compliance question (e.g. Does the deposit forfeiture clause violate Section 74?)..."
                  : "Ask about this agreement (e.g. What is the rent amount? What is the termination notice?)..."
            }
            disabled={disabled || busy}
            onChange={(event) => setQuestion(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                void submit(question);
              }
            }}
          />
          <div className="input-actions">
            <span className="char-count">{question.length}/600</span>
            <button
              type="submit"
              className="send-button"
              disabled={disabled || busy || question.trim().length === 0}
            >
              {busy ? "Analyzing..." : "Ask Chatbot"}
            </button>
          </div>
        </div>
      </form>
    </section>
  );
}
