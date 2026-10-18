// Mirrors backend/app/schemas/response.py exactly (snake_case, no aliases).
// The UI renders these objects; it never constructs a claim or a verdict.

export type ResponseStatus =
  | "ANSWERED"
  | "LIMITED"
  | "NOT_LOCATED"
  | "AMBIGUOUS"
  | "CONFLICTING"
  | "INSUFFICIENT_EVIDENCE"
  | "LEGAL_LIMIT"
  | "OUT_OF_SCOPE"
  | "UNSUPPORTED_LANGUAGE"
  | "ERROR_LOCAL_MODEL_UNAVAILABLE"
  | "ERROR_PROCESSING";

export type Classification = "DIRECT" | "SUPPORTED" | "INTERPRETATION" | "CONCERN" | "AMBIGUITY";

export interface EvidenceItem {
  sid: string;
  page: number;
  section: string | null;
  quote: string;
  ocr_derived: boolean;
  document_sha256: string | null;
}

export interface Claim {
  claim_id: string;
  text: string;
  classification: Classification;
  evidence: EvidenceItem[];
}

export interface GeneralExplanation {
  entry_id: string;
  term: string;
  definition: string;
  source: "glossary";
  disclaimer: string;
}

export interface MissingInformation {
  code: string;
  message: string;
  evidence: EvidenceItem[];
  searches: string[];
}

export interface ExtractionWarning {
  code: string;
  message: string;
  page: number | null;
  ocr_derived: boolean;
}

export interface JurisdictionFlag {
  topic: string;
  label: string;
  evidence: EvidenceItem[];
}

export interface EscalationQuestion {
  question: string;
  topics: string[];
  evidence: EvidenceItem[];
}

export interface DocumentRef {
  document_id: string;
  display_name: string;
  page_count: number;
  sha256: string;
}

export interface RunMeta {
  route: string;
  path: string;
  provider: string;
  model_tag: string | null;
  model_digest: string | null;
  duration_ms: number;
  tool_calls: number;
  model_calls: number;
  retrieval_loops: number;
  chunks_considered: number;
  validation_codes: string[];
  sids_exposed: string[];
}

export interface RenderedAnswer {
  status: ResponseStatus;
  answer: string;
  claims: Claim[];
  interpretations: Claim[];
  concerns: Claim[];
  ambiguities: Claim[];
  conflicts: Claim[];
  general_explanations: GeneralExplanation[];
  missing_information: MissingInformation[];
  extraction_warnings: ExtractionWarning[];
  jurisdiction_flags: JurisdictionFlag[];
  escalation: EscalationQuestion[];
  external_law_required: boolean;
  recommend_professional_review: boolean;
  legal_verdict: null;
  document: DocumentRef | null;
  run_meta: RunMeta | null;
}

export interface CardEvidence {
  sid: string;
  page: number;
  section: string | null;
  quote: string;
  ocr_derived: boolean;
}

export type CardStatus = "FOUND" | "NOT_LOCATED" | "NOT_ASSESSED" | "INSUFFICIENT_EVIDENCE";

export interface MapCard {
  status: CardStatus;
  summary: string;
  evidence: CardEvidence[];
  note: string;
}

/** Keyed by display label: Parties, Term, Rent, ... — fixed by the contract. */
export interface OverviewResponse {
  document: DocumentRef;
  cards: Record<string, MapCard>;
  warnings: ExtractionWarning[];
}

export interface ReviewAttentionItem {
  category: "CONFLICT" | "AMBIGUITY" | "FINANCIAL" | "JURISDICTION" | "OTHER" | string;
  priority: number;
  title: string;
  reason: string;
  citations: CardEvidence[];
  order_reason: string;
}

export interface ProfessionalQuestion {
  topic: string;
  prompt: string;
}

export interface ReviewResponse {
  document: DocumentRef;
  review_status: "CLEAR" | "ATTENTION" | "NOT_ASSESSED";
  attention_first: ReviewAttentionItem[];
  questions_for_professional: ProfessionalQuestion[];
  disclaimer: string;
}

export interface DocumentSummary {
  document_id: string;
  display_name: string;
  source_kind: "pdf" | "txt";
  page_count: number;
  sha256: string;
  created_at: string;
  readable_pages: number;
  unread_pages: number;
  ocr_used: boolean;
  quality_flags: string[];
}

export interface DocumentListResponse {
  documents: DocumentSummary[];
}

export interface QualityMetrics {
  pages_read: number;
  ocr_used: boolean;
  language_detected: "en" | "mixed" | "unknown" | string;
  garble_ratio: number;
  hidden_text_detected: boolean;
}

export interface UploadResponse {
  document_id: string;
  document_hash: string;
  display_name: string;
  source_kind: "pdf" | "txt";
  page_count: number;
  readable_pages: number;
  quality_metrics: QualityMetrics;
  extraction_warnings: ExtractionWarning[];
  status: "READY" | "PARTIAL";
  created_at: string;
}

export interface HealthResponse {
  status: "ok" | "degraded";
  local_model_available: boolean;
  model_tag: string;
  model_digest: string | null;
  parser_engine: string;
  storage_backend: string;
  models: Record<string, boolean>;
  ocr_available: boolean;
  history_enabled: boolean;
}

export interface PageSentence {
  sid: string;
  start_offset: number;
  end_offset: number;
  text: string;
  section: string | null;
  ocr_derived: boolean;
}

export interface PageResponse {
  document_id: string;
  page_number: number;
  is_virtual_page: boolean;
  ocr_used: boolean;
  text: string;
  flags: string[];
  sentences: PageSentence[];
}

export interface DeletionResponse {
  document_id: string;
  files_purged: number;
  database_unlinked: boolean;
  model_cache_evicted: boolean;
  canary_scan_passed: boolean;
  forensic_erasure_disclaimer: string;
  remaining_derived_files: string[];
  session_binding_cleared: boolean;
  notes: string[];
}

export interface EvidenceResponse {
  evidence_id: string;
  document_hash: string;
  page: number;
  section: string | null;
  sids: string[];
  verbatim_text: string;
  text_sha256: string;
  ocr_derived: boolean;
}

export interface ModelInfo {
  alias: string;
  tag: string;
  label: string;
  role: "primary" | "low-memory" | "alternate" | string;
  available: boolean;
  ollama_reachable: boolean;
  default: boolean;
}

export interface ModelsResponse {
  models: ModelInfo[];
}

export interface CUADFinding {
  category: string;
  label: string;
  description: string;
  badge_type: "normal" | "warning" | "danger";
  badge_icon: string;
  quote: string;
  page: number;
  section: string | null;
  sid: string;
}

export interface CUADAnalysisResponse {
  document_id: string;
  document_name: string;
  page_count: number;
  findings: CUADFinding[];
  total_categories_checked: number;
  found_count: number;
}

export interface EnactmentMetadata {
  act_id: string;
  act_number: string;
  title: string;
  year: number;
  enactment_date: string;
  ministry: string;
  jurisdiction: string;
  total_sections: number;
  summary: string;
  source_url: string;
}

export interface StatutorySection {
  section_id: string;
  section_number: string;
  title: string;
  text: string;
  act_id: string;
  act_name: string;
  year: number;
  jurisdiction: string;
  keywords: string[];
  source_url: string;
  gazette_ref: string;
}

export interface PrecedentJudgment {
  judgment_id: string;
  citation: string;
  case_name: string;
  court: string;
  date: string;
  bench: string;
  relevant_acts: string[];
  sections_interpreted: string[];
  issue: string;
  holding: string;
  quote: string;
  ratio_decidendi: string;
  source_url: string;
}

export interface StatutoryAuditFinding {
  clause_category: string;
  contract_quote: string;
  contract_page: number;
  statute: string;
  section: string;
  legal_rule: string;
  compliance_status: "COMPLIANT" | "CAUTION" | "VOID_UNENFORCEABLE";
  risk_level: "LOW" | "MEDIUM" | "HIGH";
  statutory_citation: string;
  relevant_precedent: string;
  explanation: string;
}

export interface ComplianceAuditResponse {
  document_id: string;
  document_name: string;
  page_count: number;
  audit_findings: StatutoryAuditFinding[];
  total_rules_evaluated: number;
  high_risk_count: number;
  medium_risk_count: number;
  compliant_count: number;
}

export interface IndiaLawSearchResponse {
  query: string;
  sections: StatutorySection[];
  judgments: PrecedentJudgment[];
  total_sections_matched: number;
  total_judgments_matched: number;
}

