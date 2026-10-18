// Typed API client. The bearer token lives in module memory only: never
// localStorage, sessionStorage, IndexedDB, URL or cookies.
import type {
  ComplianceAuditResponse,
  CUADAnalysisResponse,
  DeletionResponse,
  DocumentListResponse,
  DocumentSummary,
  EnactmentMetadata,
  EvidenceResponse,
  HealthResponse,
  IndiaLawSearchResponse,
  ModelInfo,
  OverviewResponse,
  PageResponse,
  PrecedentJudgment,
  RenderedAnswer,
  ReviewResponse,
  StatutorySection,
  UploadResponse,
} from "../types/api";

export class ApiError extends Error {
  readonly status: number;
  readonly code?: string;
  constructor(status: number, message: string, code?: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

let sessionToken: string | null = null;

export function setSessionToken(token: string): void {
  sessionToken = token;
}

function authHeaders(): Record<string, string> {
  return sessionToken ? { Authorization: `Bearer ${sessionToken}` } : {};
}

type DetailShape = { detail?: string | { code?: string; message?: string } };

export async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(path, {
    ...init,
    cache: "no-store",
    headers: {
      ...(init.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...authHeaders(),
      ...(init.headers ?? {}),
    },
  });
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    let code: string | undefined;
    try {
      const body = (await response.json()) as DetailShape;
      const detail = body.detail;
      if (typeof detail === "string") message = detail;
      else if (detail && typeof detail === "object") {
        message = detail.message ?? message;
        code = detail.code;
      }
    } catch {
      // keep the status-based message
    }
    throw new ApiError(response.status, message, code);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export const api = {
  async listDocuments(): Promise<DocumentSummary[]> {
    const body = await request<DocumentListResponse>("/api/documents");
    return body.documents;
  },

  uploadDocument(file: File): Promise<UploadResponse> {
    const form = new FormData();
    form.append("file", file);
    return request<UploadResponse>("/api/documents", { method: "POST", body: form });
  },

  overview(documentId: string): Promise<OverviewResponse> {
    return request<OverviewResponse>(`/api/documents/${documentId}/overview`);
  },

  ask(
    documentId: string,
    question: string,
    model?: string,
    allowFallback: boolean = true,
  ): Promise<RenderedAnswer> {
    return request<RenderedAnswer>(`/api/documents/${documentId}/ask`, {
      method: "POST",
      body: JSON.stringify({
        question,
        ...(model ? { model } : {}),
        allow_fallback: allowFallback,
      }),
    });
  },

  cuad(documentId: string): Promise<CUADAnalysisResponse> {
    return request<CUADAnalysisResponse>(`/api/documents/${documentId}/cuad`);
  },

  async models(): Promise<ModelInfo[]> {
    const body = await request<{ models: ModelInfo[] }>("/api/models");
    return body.models;
  },

  review(documentId: string): Promise<ReviewResponse> {
    return request<ReviewResponse>(`/api/documents/${documentId}/review`, { method: "POST" });
  },

  page(documentId: string, page: number): Promise<PageResponse> {
    return request<PageResponse>(`/api/documents/${documentId}/pages/${page}`);
  },

  pageImageUrl(documentId: string, page: number): string {
    return `/api/documents/${documentId}/pages/${page}/image`;
  },

  evidence(documentId: string, sid: string): Promise<EvidenceResponse> {
    return request<EvidenceResponse>(`/api/documents/${documentId}/evidence/${sid}`);
  },

  deleteDocument(documentId: string): Promise<DeletionResponse> {
    return request<DeletionResponse>(`/api/documents/${documentId}`, { method: "DELETE" });
  },

  complianceAudit(documentId: string): Promise<ComplianceAuditResponse> {
    return request<ComplianceAuditResponse>(`/api/documents/${documentId}/compliance-audit`, {
      method: "POST",
    });
  },

  async enactments(): Promise<EnactmentMetadata[]> {
    const res = await request<{ enactments: EnactmentMetadata[] }>("/api/india-law/enactments");
    return res.enactments;
  },

  async sections(): Promise<StatutorySection[]> {
    const res = await request<{ sections: StatutorySection[] }>("/api/india-law/sections");
    return res.sections;
  },

  async judgments(): Promise<PrecedentJudgment[]> {
    const res = await request<{ judgments: PrecedentJudgment[] }>("/api/india-law/judgments");
    return res.judgments;
  },

  searchIndiaLaw(query: string, limit: number = 6): Promise<IndiaLawSearchResponse> {
    return request<IndiaLawSearchResponse>(
      `/api/india-law/search?q=${encodeURIComponent(query)}&limit=${limit}`,
    );
  },

  health(): Promise<HealthResponse> {
    return request<HealthResponse>("/api/health");
  },
};

/** Authenticated <img> fetch: the token is a header, not a query string. */
export async function fetchPageImage(
  documentId: string,
  page: number,
): Promise<string | null> {
  try {
    const response = await fetch(api.pageImageUrl(documentId, page), {
      headers: authHeaders(),
      cache: "no-store",
    });
    if (!response.ok) return null;
    return URL.createObjectURL(await response.blob());
  } catch {
    return null;
  }
}
