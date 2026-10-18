export interface UploadResponse {
  document_id: string;
  filename: string;
  status: string;
}

export interface DocumentStatus {
  document_id: string;
  filename: string;
  status: "processing" | "ready" | "failed";
  pages?: number | null;
  chunks?: number | null;
  error?: string | null;
}

export interface ChatMessageItem {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface ChatSourceItem {
  filename: string;
  page?: number | null;
  chunk_id: string;
}

export interface ChatResponse {
  answer: string;
  sources: ChatSourceItem[];
}

const BASE_URL = "/api";

export async function uploadDocument(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${BASE_URL}/upload`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(errorData.detail || "Upload failed");
  }

  return res.json();
}

export async function getDocumentStatus(documentId: string): Promise<DocumentStatus> {
  const res = await fetch(`${BASE_URL}/document/${documentId}/status`);
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: "Failed to fetch status" }));
    throw new Error(errorData.detail || "Failed to fetch status");
  }
  return res.json();
}

export async function chatWithDocument(
  documentId: string,
  question: string,
  conversation: ChatMessageItem[] = [],
): Promise<ChatResponse> {
  const res = await fetch(`${BASE_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      document_id: documentId,
      question,
      conversation,
    }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: "Chat request failed" }));
    throw new Error(errorData.detail || "Chat request failed");
  }

  return res.json();
}

export async function deleteDocument(documentId: string): Promise<{ success: boolean }> {
  const res = await fetch(`${BASE_URL}/document/${documentId}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: "Delete failed" }));
    throw new Error(errorData.detail || "Delete failed");
  }
  return res.json();
}

export async function checkHealth(): Promise<{ status: string }> {
  const res = await fetch(`${BASE_URL}/health`);
  return res.json();
}

export interface SummarizeResponse {
  document_id: string;
  summary: string;
  status: string;
  message?: string;
  total_chunks_processed?: number;
}

export async function summarizeDocument(documentId: string): Promise<SummarizeResponse> {
  const res = await fetch(`${BASE_URL}/documents/${documentId}/summarize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ document_id: documentId }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: "Summarization failed" }));
    throw new Error(errorData.detail || "Unable to generate document summary.");
  }
  return res.json();
}

