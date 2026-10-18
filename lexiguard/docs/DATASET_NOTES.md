# Dataset notes

All fixtures are synthetic. No real agreement, no scraped contract, no personal data is included.

---

## 1. Fixture inventory

| Fixture | Purpose | Length | Canary | PDF variant |
|---|---|---|---|---|
| `synthetic_rental_simple.txt` | Clean baseline: rent, deposit, notice, maintenance, termination | 337 words | `CANARY-LG-SIMPLE-001` | planned |
| `synthetic_rental_indian_style.txt` | Regional phrasing: lessor/lessee, lock-in, `Rs.`, DD/MM/YYYY, stamp/registration, jurisdiction cue | 338 words | `CANARY-LG-INDIAN-002` | planned |
| `synthetic_rental_conflict.txt` | Contradictory notice/deposit/rent clauses in different sections | 203 words | `CANARY-LG-CONFLICT-003` | planned |
| `synthetic_rental_ambiguous.txt` | “Reasonable notice”, “market rate”, heading/body mismatch | 162 words | `CANARY-LG-AMBIGUOUS-004` | planned |
| `synthetic_rental_injection.txt` | Ignore-instructions text in body, footnote, header and a table row | 154 words | `CANARY-LG-INJECTION-005` | planned |
| Scanned page set | OCR path and unreadable-page banner | — | — | Phase 1b |
| Malformed/oversized set | Fail-closed parser tests | — | — | Phase 1 |

Generation method: hand-authored for this project (no source text copied). Every fixture is
clearly fictional (names, addresses, amounts). Exact hashes are recorded in `fixtures/README.md`
once frozen; changing a fixture requires re-annotating affected questions.

---

## 2. Question set

`questions/development.jsonl` holds 12 starter rows with `status: draft` and this shape:

```json
{"id":"Q-FACT-001","document":"fixtures/synthetic_rental_simple.txt","category":"direct_fact",
 "question":"What is the monthly rent?","expected_status":"ANSWERED",
 "gold_sids":[],"gold_sections":[],"expected_facts":["Rs. 25,000 per month","payable by the 5th"],
 "forbidden_claims":["any other amount"],"language_condition":"english",
 "ocr_condition":"not_applicable","annotator_note":"Rent clause 4. Fill gold sids after Phase 3 indexing.",
 "annotation_status":"draft"}
```

Categories (closed in `questions/schema.json`): `direct_fact`, `multi_clause`, `not_located`,
`ambiguity`, `conflict`, `legal_boundary`, `term`, `injection`, `robustness`, `paraphrase_twin`.
The current 12 rows are unannotated drafts. The final set needs ≥114 base rows + ≥30 paraphrase
twins. Held-out rows live in `questions/heldout/` and must not be read by prompts, lexicons or
code paths.

---

## 3. Why gold sids are empty today

Sentence ids are derived from stored offsets, which require the Phase 1/3 indexing pipeline. Filling
them by hand before indexing would encode ids that later disagree with the index. The annotation
step is therefore: index fixture → resolve intended sentence text → write sid → verify via the
evidence endpoint.

---

## 4. Provenance and licence of data

- Authored by the team, no third-party text; released under the repository licence.
- Glossary entries are curated summaries, `reviewed: false`; they are not copied from any
  proprietary legal glossary.
- Lexicons are authored keyword/synonym lists, not scraped ontologies.
- If a public corpus is ever added, record its licence, version, URL, and the exact preparation
  script; it must not be personal or identifiable data.

---

## 5. Risks

| Risk | Mitigation |
|---|---|
| Fixtures too clean/templated → optimistic metrics | Hold-out authored separately; adversarial injection rows |
| Lexicon tuned to the fixtures | Freeze questions first; require paraphrase twins; report per-category |
| Annotation drift | Single annotation sheet, recorded notes, independent review where possible |
| Held-out leakage | Never referenced in code, prompts, lexicons, ADRs or reviews before the final run |
