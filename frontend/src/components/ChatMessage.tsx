import React from "react";
import { ChatSourceItem } from "../services/api";
import { SourceCitation } from "./SourceCitation";

export interface Message {
  id: string;
  sender: "user" | "assistant";
  text: string;
  sources?: ChatSourceItem[];
  error?: boolean;
  isSummary?: boolean;
}

interface ChatMessageProps {
  message: Message;
}

function renderFormattedText(text: string) {
  // Simple clean markdown parser for headings, bullet points, and bold text
  const lines = text.split("\n");
  const elements: React.ReactNode[] = [];
  let listItems: React.ReactNode[] = [];

  const flushList = () => {
    if (listItems.length > 0) {
      elements.push(
        <ul key={`list-${elements.length}`} className="message-bullet-list">
          {listItems}
        </ul>
      );
      listItems = [];
    }
  };

  const formatBold = (str: string) => {
    const parts = str.split(/(\*\*.*?\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return <strong key={i}>{part.slice(2, -2)}</strong>;
      }
      return part;
    });
  };

  lines.forEach((line, idx) => {
    const trimmed = line.trim();
    if (!trimmed) {
      flushList();
      return;
    }

    if (trimmed.startsWith("# ")) {
      flushList();
      elements.push(<h2 key={idx} className="msg-h1">{formatBold(trimmed.slice(2))}</h2>);
    } else if (trimmed.startsWith("## ")) {
      flushList();
      elements.push(<h3 key={idx} className="msg-h2">{formatBold(trimmed.slice(3))}</h3>);
    } else if (trimmed.startsWith("### ")) {
      flushList();
      elements.push(<h4 key={idx} className="msg-h3">{formatBold(trimmed.slice(4))}</h4>);
    } else if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
      listItems.push(<li key={`li-${idx}`}>{formatBold(trimmed.slice(2))}</li>);
    } else {
      flushList();
      elements.push(<p key={idx} className="msg-p">{formatBold(trimmed)}</p>);
    }
  });

  flushList();
  return elements;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.sender === "user";

  return (
    <div className={`message-row ${isUser ? "user-row" : "assistant-row"}`}>
      <div className={`message-bubble ${isUser ? "user-bubble" : "assistant-bubble"} ${message.error ? "error-bubble" : ""} ${message.isSummary ? "summary-bubble" : ""}`}>
        <div className="bubble-sender-tag">
          {isUser ? "You" : (message.isSummary ? "GBDoc · Full Document Summary" : "GBDoc")}
        </div>
        <div className="bubble-content">
          {renderFormattedText(message.text)}
        </div>
        {!isUser && message.sources && message.sources.length > 0 && (
          <SourceCitation sources={message.sources} />
        )}
      </div>
    </div>
  );
}

