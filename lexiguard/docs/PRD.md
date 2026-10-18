# Product requirements (summary)

The authority is `SOLUTION_GUIDE_v3.md`; this page is the short product brief used for the README,
the demo script and submission answers.

---

## 1. Problem

Rental agreements are long, dense, and written in a register most tenants do not read comfortably.
The questions people actually have — *What must I pay, by when, and what happens if I stop? Can the
landlord keep my deposit? How much notice must I give?* — are answerable from the document, but the
cost of finding and interpreting the clause is high.

## 2. Product

LexiGuard reads **one rental agreement at a time**, on the user's machine, and answers questions
with quotations tied to that agreement. It distinguishes what the document says from what it might
mean, shows when the document is silent or contradicts itself, and refuses to give a legal verdict.

## 3. Primary journeys

1. **Upload → overview**: tenant uploads a PDF/TXT; sees parties, rent, deposit, notice, term and
   flagged topics with page/section references.
2. **Ask → verified answer**: asks “What is the notice period for ending the tenancy?”; gets a
   plain-language answer whose factual points quote stored sentences; interpretive points are
   separated and labelled.
3. **Review → attention list**: sees top legal-attention items (missing deposit-return timeline,
   conflicting notice periods), legal-boundary items, and questions to take to a professional.
4. **Delete → verified removal**: removes the document; app-controlled files are removed and the
   absence is checked; wording never claims forensic erasure.

## 4. Non-goals

No legal advice or verdicts; no prediction of outcomes; no multi-document comparison; no
jurisdiction-specific advice; no non-English documents; no cloud models, accounts, telemetry,
bundled analytics or CDN assets; no document history; no OCR-by-default for digital PDFs.

## 5. Requirements in one line each

| ID | Requirement |
|---|---|
| L1 | Accept PDF/TXT, private ingestion |
| L2 | Local extraction and local model interpretation on 127.0.0.1 |
| L3 | Plain-language glossary, clearly not legal advice |
| L4 | Coverage of rights, obligations, dates, penalties, termination |
| L5 | Verifiable passages with stable ids and backend-rendered quotes |
| L6 | Explicit (quoted/paraphrased) separated from interpretive/concern content |
| L7 | Ambiguity, silence and jurisdiction dependence surfaced |
| L8 | Limit, refuse and escalate legal conclusions |
| L9 | Privacy demonstrated with an isolated-network run, not asserted |
| L10 | Meaningful Gemma use and a reusable open-source implementation |

## 6. Status words used in this repo

| Status | Meaning |
|---|---|
| ANSWERED | Evidence found; all rendered points passed validation |
| LIMITED | Sound evidence for part of the question |
| OUT_OF_SCOPE | Not a rental-agreement question |
| NOT_LOCATED | Checked readable text; the topic is absent |
| INSUFFICIENT_EVIDENCE | Cannot prove absence or support an answer |
| AMBIGUOUS / CONFLICTING | Document wording is indefinite / contradicts itself |
| LEGAL_LIMIT | Would require a legal conclusion |
| ERROR_LOCAL_MODEL_UNAVAILABLE / ERROR_PROCESSING | Fail closed, never fall back |

`legal_verdict` is always `null`. Status precedence is defined in `core/enums.py`.

## 7. Demo narrative (5 minutes, once Phase 4 exists)

1. Show startup: one-time link, “Designed for local processing”.
2. Upload a synthetic Indian-style agreement; show OCR/quality banner only if the page needs it.
3. Ask a factual question; open the quote; show page and section.
4. Ask a boundary question (“Is this clause valid?”); show the limitation template.
5. Ask about an absent topic; show `NOT_LOCATED` and why absence cannot be concluded.
6. Delete; read the honest deletion sentence; show the privacy report and its negative control.
