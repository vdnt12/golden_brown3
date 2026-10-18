# LexiGuard data flow

Companion to [`ARCHITECTURE.md`](ARCHITECTURE.md). Each flow names the exact data objects that
cross each boundary and what is persisted (or deliberately not persisted).

> Every flow below is implemented. Anything still unmeasured is called out in
> `LIMITATIONS.md` rather than hidden in a phase note.

---

## 0. Data objects

| Object | Producer | Shape (essentials) | Persisted? |
|---|---|---|---|
| `UploadInspection` | `ingest/upload.py` | kind, size, sanitised display name | no |
| `ParsedDocument` / `ParsedPage` | `ingest/parser.py` | source kind, virtual flag, normalised page text, warnings | yes (pages + source file) |
| `SentenceRecord` | `ingest/segment.py` | sid, page, section, char_start/end, text | yes (`sentences`) |
| `PageQuality`, `LanguageVerdict` | `ingest/quality.py`, `language.py` | char count, garble/coverage, OCR flags; English/unread reason | flags persisted |
| `ChunkInsert` | `store/chunks.py` | ev_id, section, heading, offsets, text, sentence_ids, numbers | yes (`chunks` + FTS) |
| `Evidence` | `validation/provenance.py` | sid, page, section, quote, OCR flag, doc hash | quote is read from store, not stored again |
| `ModelAnswer` | model | points: point_id, kind, text, sids | **no** (untrusted, transient) |
| `ValidationOutcome` | `validation/pipeline.py` | accepted/rejected points + codes | codes in run ledger only |
| `RenderedAnswer` | `validation/renderer.py` | status, answer, typed claims with evidence, missing info, flags, `legal_verdict: null` | rendered per request; not stored by default |
| `RunMeta` | runtime | route, path, digest, durations, counts, validation codes, sids exposed | yes (`run_ledger`, no text) |
| `DeletionReport` | `store/delete.py` | directory removed, canary hits, forensic_erasure=false, notes | returned to caller; not retained |

Never persisted by default: question text, answer text, evidence text, embeddings, browser
storage, model prompts, thinking channel.

---

## 1. Upload → parse → index

```text
Browser                FastAPI                 ingest                  store
  │  multipart file       │                       │                      │
  ├──────────────────────►│ upload.inspect_upload │                      │
  │                       ├──────────────────────►│ magic/size/encoding  │
  │                       │                       │  reject or continue  │
  │                       ├───────────────────────┤ child process (PDF)  │
  │                       │                       │  or TXT virtual pages│
  │                       │                       ├─ normalize_text ────►│
  │                       │                       ├─ assess_pages        │
  │                       │                       ├─ classify_page      │
  │                       │                       ├─ segment_pages      │
  │                       │                       │  (sid, offsets)      │
  │                       │                       ├─ insert document ───►│ document
  │                       │                       ├─ insert pages ──────►│ pages
  │                       │                       ├─ insert sentences ──►│ sentences
  │                       │                       ├─ build chunks ──────►│ chunks
  │                       │                       │                      ├─ FTS trigger
  │◄── {document_id, page_count, quality, warnings} ◄────────────────────┤
```

Rules:
- `doc_id` is 128-bit random, generated server-side; filename never becomes a path.
- Upload source file is stored under `data/docs/<doc_id>/`; the SQLite file lives beside it.
- Parse output is validated field-by-field in the parent before any insert.
- If any step fails, no partial searchable document is left: the directory is removed and the
  error is controlled.
- TXT is split into virtual pages of ~3,000 chars at paragraph boundaries. Citations and the
  source viewer treat these as physical pages and label them “virtual page (TXT)”.

Scaffold reality: `parse_txt_bytes`, `normalize_text`, `segment_page`, `assess_pages`,
`classify_page` and all store writers run in unit tests, but no HTTP route calls them yet.

---

## 2. Ask flow

### 2.1 Fast path (one model call)

```text
Browser ──POST /api/documents/{id}/ask {question≤500}──► FastAPI
                                                            │
       auth + doc binding + caps ──────────────────────────┤
                                                            ▼
                                   pre_route(question)  [router.py]
                                                            │
                       lexicon + FTS + headings + xrefs + silence gate (no model)
                                                            │
                                       build evidence packet (≤12 chunks, ≤2.5K tokens)
                                                            │
                                       PromptRecord[] → nonce-delimited block
                                                            │
                                       exactly one Ollama /api/chat call
                                       (think:false, format=simple schema, no tools)
                                                            │
                              ModelAnswer (Pydantic-validated; one format retry)
                                                            │
                    provenance → citation → literal/modality/role → scanner → renderer
                                                            │
                                          RenderedAnswer (backend-owned)
                                                            │
Browser ◄──────────────────── JSON, Cache-Control: no-store ─┘
```

### 2.2 Refinement path (one extra call)

Used only when retrieval is **not** confident: exactly one of query expansion (T6, widens BM25
only) **or** one `NextAction` round — never both — then the answer call. Total model calls for a
question never exceed 4 including retries. The chosen path is recorded in `run_meta.path`.

### 2.3 Validation inside the ask flow

```text
ModelAnswer.points[]
   │
   ├─ schema (Pydantic, unknown keys rejected) ─────────── reject answer on hard failure
   ├─ sid ∈ ProvenanceRegistry(this run, this doc) ─────── drop point + SID_NOT_EXPOSED_IN_RUN
   ├─ backend loads quote/page/section from store ─────── never from model text
   ├─ kind checks:
   │    STATED: normalized text must be extractive
   │    RESTATEMENT: literals, modality/negation, roles must match cited sentences
   │    INTERPRETATION/CONCERN/AMBIGUITY: ≥1 citation + labelled
   │    CONFLICT: ≥2 sids from different sections, both shown
   │    GENERAL_EXPLANATION: no document-specific numbers/names
   ├─ legal scanner (assistant text only; source-echo limited to STATED/RESTATEMENT)
   └─ renderer (validated points only) → status precedence → RenderedAnswer
```

If everything is rejected, the caller returns `INSUFFICIENT_EVIDENCE` (or the legal-limit path if
the route demanded it); it never shows an unvalidated point.

---

## 3. Silence decision

```text
topic/question
   │
   ├─ topic lexicon search
   ├─ lexical full-text + heading search
   ├─ cross-reference + incorporated schedules check
   ├─ coverage: readable pages / all pages
   ├─ language: any unread page?
   └─ dense check only if dense is enabled (not in default build)
                     │
        all checks done AND coverage ok AND no unread pages
                     │ yes                            │ no
                     ▼                                ▼
               NOT_LOCATED                    INSUFFICIENT_EVIDENCE
```

`TOPIC_NOT_LOCATED` missing-information is allowed only in the left branch. Unread pages always
force the right branch, because the topic could be in the unread text.

---

## 4. Review / Overview

Review runs the same retrieval + validation machinery per topic and assigns only:
`FOUND`, `NOT_FOUND` (displayed “Not located”), `AMBIGUOUS`, `POSSIBLE_CONFLICT`, `NOT_ASSESSED`.
Overview cards are extracted deterministically first (money, dates, durations, parties with sids);
Gemma may only restate them. “Attention first” order is deterministic and templated — conflicts →
money/time/termination ambiguity → payment/forfeiture/lock-in obligations → jurisdiction flags →
everything else. No scores, grades or colours.

---

## 5. Delete flow

```text
DELETE /api/documents/{id}
   │
   ├─ validate doc id (32 hex) and resolve under data/docs/ (no traversal)
   ├─ reject new work; cancel/await active operations                    [Phase 4]
   ├─ close SQLite connections, cursors, parser/page handles              [Phase 1]
   ├─ Ollama unload keep_alive:0 and verify the installed version        [Phase 2]
   ├─ purge rows + FTS shadows (trigger-driven)
   ├─ remove data/docs/<doc_id>/ entirely (source, db, page images, history)
   ├─ verify directory absence
   ├─ canary scan of app-controlled logs/temp (+ optional Hermes tmpfs)
   ├─ clear frontend state; revoke document binding
   └─ return DeletionReport {directory_removed, canary_hits, forensic_erasure:false}
```

Wording rule: “app-controlled files removed and verified” — never “forensically erased”.
SSD wear-levelling, OS swap/hibernation and external backups are outside application control.

Scaffold reality: `services/lifecycle.document_dir()` rejects traversal and non-32-hex ids;
`store/delete.delete_document_directory()` removes the directory and reports canary hits. Both are
tested. The route and the connection/model-unload steps are Phase 1/2.

---

## 6. Model interaction

Request shape built by `model/ollama_native.build_chat_payload`:

```json
{
  "model": "gemma4:e4b-it-q4_K_M",
  "stream": false,
  "think": false,
  "messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "... evidence ..."}],
  "format": { "type": "object", "properties": { "points": { "...": "..." } }, "required": ["points"] },
  "options": { "seed": 7, "temperature": 0.0, "num_ctx": 8192 }
}
```

- **No `tools` key, ever** (structural guard + test).
- Simple flat schema only: no `pattern`, `format`, `oneOf`, deep nesting; `additionalProperties`
  is not relied on (the Guide's smoke schema contradiction is removed).
- Reply: `message.content` must be non-empty JSON; empty content fails even if `thinking` exists.
- After the call: `prompt_eval_count + eval_count < num_ctx`, else `ContextOverflowError`.
- One format-retry; then `ERROR_LOCAL_MODEL_UNAVAILABLE` / `ERROR_PROCESSING` as appropriate.
- Thinking text is never parsed.

---

## 7. Retention matrix

| Data | Where | Default retention | Removed by |
|---|---|---|---|
| Source file | `data/docs/<doc_id>/` | until Delete | Delete |
| SQLite (pages/sentences/chunks/FTS) | same directory | until Delete | Delete + purge |
| Rendered answers | response only | not stored | — |
| Questions | request only | not stored | — |
| Run ledger | per-doc SQLite | until Delete | Delete (no text stored) |
| Browser token | JS memory | until tab close/launch code expiry | reload requires new launch URL |
| History / embeddings | not created | — | — |
| Logs | application logs | content-free by policy | retention policy at Phase 1 |
| Privacy evidence | `reports/privacy/<release>/` | committed | not raw payloads |

---

## 8. Failure → status mapping

| Failure | Status | Notes |
|---|---|---|
| Upload invalid (magic/size/encoding/page cap) | `ERROR_PROCESSING` on the upload route | Controlled 4xx/5xx; no partial document |
| Parser child timeout/crash | `ERROR_PROCESSING` | Directory cleanup runs |
| Ollama unreachable / empty content / schema invalid after retry | `ERROR_LOCAL_MODEL_UNAVAILABLE` or `ERROR_PROCESSING` | No cloud fallback |
| Context overflow | `ERROR_PROCESSING` | Detected before rendering |
| All model points rejected | `INSUFFICIENT_EVIDENCE` | Never show unvalidated claims |
| Verdict detected in assistant text | `LEGAL_LIMIT` | Text replaced by template; quotation untouched |
| Unread pages forbid absence claim | `INSUFFICIENT_EVIDENCE` | Silence gate |
| Two conflicting passages found | `CONFLICTING` | Both cited; no winner chosen |
| Question over 500 chars / empty / off-topic | `OUT_OF_SCOPE` | No model call |

Status precedence and exact ordering: `ARCHITECTURE.md` §7.
