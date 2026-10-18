import React, { useState, useRef, useEffect } from "react";
import { Message, ChatMessage } from "./ChatMessage";
import { chatWithDocument, summarizeDocument, ChatMessageItem } from "../services/api";

interface ChatWindowProps {
  documentId: string;
  disabled?: boolean;
}

type QueryState =
  | "idle"
  | "searching"
  | "generating"
  | "reading_doc"
  | "generating_summary"
  | "finalizing_summary";

function isSummaryIntent(text: string): boolean {
  const t = text.trim().toLowerCase();
  return (
    t.includes("summarize") ||
    t.includes("summarise") ||
    t.includes("key points") ||
    t.includes("give me a summary") ||
    t.includes("give me the summary") ||
    t.includes("what is this document about") ||
    t.includes("explain this document") ||
    t.includes("give me an overview")
  );
}

export function ChatWindow({ documentId, disabled }: ChatWindowProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [queryState, setQueryState] = useState<QueryState>("idle");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, queryState]);

  const handleSummarize = async () => {
    if (disabled || queryState !== "idle") return;

    setQueryState("reading_doc");
    const userMsgId = `usr_${Date.now()}`;
    setMessages((prev) => [
      ...prev,
      { id: userMsgId, sender: "user", text: "Summarize the document." },
    ]);

    // Section 13 & 16: Visible progressive steps
    const t1 = setTimeout(() => {
      setQueryState("generating_summary");
    }, 450);

    const t2 = setTimeout(() => {
      setQueryState("finalizing_summary");
    }, 900);

    try {
      const res = await summarizeDocument(documentId);
      clearTimeout(t1);
      clearTimeout(t2);

      setMessages((prev) => [
        ...prev,
        {
          id: `ast_${Date.now()}`,
          sender: "assistant",
          text: res.summary,
          isSummary: true,
        },
      ]);
    } catch (err) {
      clearTimeout(t1);
      clearTimeout(t2);
      setMessages((prev) => [
        ...prev,
        {
          id: `err_${Date.now()}`,
          sender: "assistant",
          text: err instanceof Error ? err.message : "Unable to generate document summary.",
          error: true,
        },
      ]);
    } finally {
      setQueryState("idle");
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  };

  const handleSend = async (questionText?: string) => {
    const q = (questionText || input).trim();
    if (!q || disabled || queryState !== "idle") return;

    // Detect summary intent in chat messages (Section 14)
    if (isSummaryIntent(q)) {
      setInput("");
      await handleSummarize();
      return;
    }

    setInput("");
    const userMsgId = `usr_${Date.now()}`;
    const newMessages: Message[] = [
      ...messages,
      { id: userMsgId, sender: "user", text: q },
    ];
    setMessages(newMessages);

    // Section 24: Visible loading states
    setQueryState("searching");
    setTimeout(() => {
      setQueryState((current) => (current === "searching" ? "generating" : current));
    }, 400);

    try {
      // Build conversation history for follow-ups (Section 19)
      const convPayload: ChatMessageItem[] = newMessages.map((m) => ({
        role: m.sender === "user" ? "user" : "assistant",
        content: m.text,
      }));

      const res = await chatWithDocument(documentId, q, convPayload);

      setMessages((prev) => [
        ...prev,
        {
          id: `ast_${Date.now()}`,
          sender: "assistant",
          text: res.answer,
          sources: res.sources,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err_${Date.now()}`,
          sender: "assistant",
          text: err instanceof Error ? err.message : "I couldn't generate an answer right now. Please try again.",
          error: true,
        },
      ]);
    } finally {
      setQueryState("idle");
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void handleSend();
    }
  };

  const sampleSuggestions = [
    "What is the company name?",
    "Who is the CEO?",
    "When was the company founded?",
    "What is the notice period?",
    "How many annual leave days are provided?",
    "What is the company's revenue?",
  ];

  return (
    <div className="chat-window-container">
      <div className="chat-toolbar">
        <div className="toolbar-left">
          <span className="chat-title">💬 Document Chat</span>
        </div>
        <div className="toolbar-right">
          <button
            type="button"
            className="summarize-toolbar-btn"
            onClick={handleSummarize}
            disabled={disabled || queryState !== "idle"}
            title="Run hierarchical full-document summary"
          >
            📑 Summarize Document
          </button>
          {messages.length > 0 && (
            <button
              type="button"
              className="clear-chat-btn"
              onClick={() => setMessages([])}
              disabled={queryState !== "idle"}
            >
              Clear Messages
            </button>
          )}
        </div>
      </div>

      <div className="chat-messages-area">
        {messages.length === 0 ? (
          <div className="empty-chat-placeholder">
            <div className="empty-icon">🤖</div>
            <h3>Ask anything about this document</h3>
            <p>
              Answers are strictly grounded in your uploaded text. If information is not in the document,
              the assistant will explicitly state so without hallucinating.
            </p>

            <div className="hero-action-box">
              <button
                type="button"
                className="hero-summarize-btn"
                onClick={handleSummarize}
                disabled={disabled || queryState !== "idle"}
              >
                📑 Generate Full Document Summary
              </button>
            </div>

            <div className="suggestions-grid">
              {sampleSuggestions.map((s, idx) => (
                <button
                  key={idx}
                  type="button"
                  className="suggestion-chip"
                  onClick={() => void handleSend(s)}
                  disabled={disabled}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => <ChatMessage key={msg.id} message={msg} />)
        )}

        {/* Section 24 & Section 13/16: Visible Progressive Loading States */}
        {queryState === "searching" && (
          <div className="query-status-indicator">
            <span className="spinner" />
            <span>Searching the document...</span>
          </div>
        )}
        {queryState === "generating" && (
          <div className="query-status-indicator">
            <span className="spinner" />
            <span>Generating answer from retrieved context...</span>
          </div>
        )}
        {queryState === "reading_doc" && (
          <div className="query-status-indicator">
            <span className="spinner" />
            <span>Reading the entire document...</span>
          </div>
        )}
        {queryState === "generating_summary" && (
          <div className="query-status-indicator">
            <span className="spinner" />
            <span>Generating intermediate summaries across all sections...</span>
          </div>
        )}
        {queryState === "finalizing_summary" && (
          <div className="query-status-indicator">
            <span className="spinner" />
            <span>Finalizing document summary...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-bar">
        <input
          ref={inputRef}
          type="text"
          className="chat-input"
          placeholder={disabled ? "Please wait until the document is ready..." : "Ask anything or type 'Summarize this'..."}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled || queryState !== "idle"}
        />
        <button
          type="button"
          className="chat-send-btn"
          onClick={() => void handleSend()}
          disabled={disabled || !input.trim() || queryState !== "idle"}
        >
          Send
        </button>
      </div>
    </div>
  );
}

