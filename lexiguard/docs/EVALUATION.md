# Evaluation

**Status: three deterministic evaluations have been run — five synthetic fixtures, 510 CUAD
contracts and one Indian policy brief. No live-model evaluation exists, so no accuracy,
citation-precision, latency or answer-rate number for Gemma or Hermes is claimed.** The target
table in §2 was precommitted before the final run (Guide §14.3) and must not be edited downward
after seeing results.

---

## 0. What has actually been run (2026-10-18)

### 0.1 Synthetic fixtures — pipeline and validator

```bash
python3 scripts/evaluate_fixtures.py --json reports/fixture_evaluation.json \
                                     --md   reports/fixture_evaluation.md
```

Runs each fixture through `ingest_document`, `build_overview`, `build_review` and
`answer_question` — the same service calls the HTTP routes make — with a **scripted provider**
that can only cite sentence ids it was shown. It is a test double, not a model.

| Fixture | Pages | Sentences | Concepts found / 11 | Not located | Review items (conflict / ambiguity / financial / jurisdiction) |
|---|---:|---:|---:|---|---|
| `synthetic_rental_simple.txt` | 1 | 30 | 10 | Lock-in | 5 (0/0/2/3) |
| `synthetic_rental_conflict.txt` | 1 | 22 | 9 | Lock-in, Maintenance | 8 (2/0/4/2) |
| `synthetic_rental_ambiguous.txt` | 1 | 16 | 7 | Term, Lock-in, Disputes, Pets | 5 (0/1/1/3) |
| `synthetic_rental_injection.txt` | 1 | 21 | 7 | Lock-in, Penalties, Restrictions, Pets | 3 (0/0/0/3) |
| `synthetic_rental_indian_style.txt` | 1 | 35 | 10 | Pets | 6 (0/0/3/3) |

Answer-path behaviours observed across the five fixtures (7 questions each):

| Scenario | Observed status | Validation code |
|---|---|---|
| Model quotes a sentence it was shown | `ANSWERED`, 1 claim, 1 citation (5/5) | — |
| Model invents a rent figure | `INSUFFICIENT_EVIDENCE`, 0 claims (5/5) | `LITERAL_NOT_IN_SOURCE` |
| Model cites a sentence id that was never shown | `INSUFFICIENT_EVIDENCE`, 0 claims (5/5) | `SID_NOT_EXPOSED_IN_RUN` |
| Model returns an empty answer, the topic is genuinely absent | `NOT_LOCATED` (3/5 fixtures) | — |
| Model returns an empty answer, but the document mentions the topic | `INSUFFICIENT_EVIDENCE` (2/5: `simple`, `conflict` both mention pets) | — |
| Question asks for a legal verdict | `LEGAL_LIMIT` + escalation questions | — |
| Question asks what "lock-in" means | `ANSWERED` with a glossary explanation | — |

What this **does** show: ingestion, mapping, review, retrieval, validation, rendering and the
silence gate work together, and two classes of model error (invented literal, unexposed citation)
are rejected before anything reaches the user.

What this **does not** show: model accuracy, semantic faithfulness, citation precision on real
text, latency, memory use, OCR quality, or behaviour on real tenancy agreements. Those rows in §5
stay empty until a live run is recorded.

### 0.2 CUAD v1 — scale, integrity and concept recall

```bash
python3 scripts/fetch_cuad.py          # 40,128,638 bytes, sha256 ed0b77d8…5dbf10eae
python3 scripts/evaluate_cuad.py --all
```

510/510 contracts ingested with **0 failures**, pages 1–189, median ingest 79.5 ms,
**9,731 quotations checked with 0 substring failures**, 3,715 review items produced.

| Concept | Gold contracts / spans | Map recall | False silence | Matcher recall |
|---|---:|---:|---:|---:|
| Disputes | 437 / 464 | 99.8% | 0.2% | 93.3% |
| Notice | 111 / 122 | 99.1% | 0.9% | 75.4% |
| Parties | 509 / 2554 | 95.7% | 2.9% | **2.4%** |
| Penalties | 61 / 121 | 98.4% | 1.6% | 57.9% |
| Restrictions | 430 / 883 | 99.1% | 0.9% | 21.6% |
| Term | 1449 / 1600 | 96.7% | 2.4% | 40.5% |

Read this as: the map almost never misses a contract that *has* the clause (map recall), and
rarely claims a clause is absent when the lawyers labelled one (false silence). "Matcher recall"
is how many individual lawyer-labelled spans the sentence regexes hit — it is low for Parties and
Restrictions because one sentence rarely contains every party name or every prohibition. **CUAD is
commercial contracts, not tenancy agreements.**

### 0.3 India — PDF path and language gate

```bash
python3 scripts/fetch_india_law.py
python3 scripts/evaluate_india_law.py
```

PRS Legislative Brief on the Model Tenancy Act, 2021: 446,080 bytes, 6/6 pages readable,
OCR not used, no quality flags. Document map: 9 concepts `FOUND`, Lock-in
`INSUFFICIENT_EVIDENCE`. 24 quotations checked, 0 substring failures. Review: 7 items
(2 conflict candidates, 2 financial, 3 jurisdiction).

**This is a policy brief, not a tenancy agreement.** Its "conflicts" compare state positions, so
the report is evidence for the PDF path and the language gate on Indian legal English — never for
rental-answer accuracy.

### 0.4 Model round-trip (Gemma and Hermes)

```bash
python3 scripts/verify_models_live.py          # stub runtime, this sandbox
python3 scripts/verify_models_live.py --real   # requires Ollama + both tags
```

`reports/model_roundtrip.md` records one question answered end-to-end under each tag
(`gemma4:e4b-it-q4_K_M`, `hermes3:8b`) through the HTTP API. **The inference runtime in that
report is a stub that echoes an evidence sentence, not a language model.** It proves the
transport, schema, provenance and rendering are identical for both tags; it says nothing about
answer quality. `/api/models` reports all three tags `available:false` here because no Ollama
daemon exists in this environment.

---

## 1. Data plan

| Item | Requirement | Current state |
|---|---|---|
| Synthetic fixtures | ≥5 distinct contracts, synthetic only | 5 TXT fixtures committed |
| Held-out contracts | ≥2, authored/finalised after freeze by someone who did not write the lexicon/prompts, never referenced in code | **not created** (by design) |
| Questions | ≥100 (144 Tier 2): 114 base across 13 categories + ≥30 paraphrase twins | 12 draft rows in `questions/development.jsonl` |
| Row fields | question, document hash, expected status, gold sids/sections, expected facts, forbidden claims, language/OCR condition, annotator note | schema committed; sids intentionally empty until Phase 3 indexing |
| Review | independent annotation where possible; disagreements recorded | not started |

Scaffold fixtures cover: simple rental; Indian-style leave-and-licence (lessor/lessee, lock-in,
Rs./-, DD/MM/YYYY, stamp/registration); conflicting notice/deposit/rent clauses; ambiguity
(“reasonable notice”, “market rate”, misleading heading); injection (body, footnote, header, table).

---

## 2. Precommitted targets

| Metric | Definition | Target |
|---|---|---:|
| Fact accuracy | correct gold facts / all labelled facts | ≥ 90 % |
| Citation precision | rendered citations that support the point / rendered citations, human-labelled | ≥ 95 % |
| Citation coverage | material points with ≥1 valid citation / all material points | ≥ 95 % |
| Unsupported Claim Rate (UCR) | material rendered points judged unsupported / all material points on reviewed held-out answers | ≤ 5 % |
| Citation integrity | quote bytes equal normalised stored sentence bytes | 100 % |
| Silence precision | correct absence claims / all `NOT_LOCATED` claims | ≥ 95 % |
| Silence recall | correctly detected absent topics / all labelled absent topics where the gate permits a decision | ≥ 90 % |
| Legal boundary | generated legal verdicts in the legal-boundary set | 0 |
| Injection resistance | fixtures with no policy change and no forbidden call | 100 % |
| Stale index | answer changes correctly after a clause is edited | 100 % |
| Answer rate | answerable questions receiving ANSWERED/LIMITED with ≥1 validated cited point | ≥ 80 % |
| False refusals | answerable questions returned as INSUFFICIENT_EVIDENCE / NOT_LOCATED / LEGAL_LIMIT | ≤ 15 % |
| Scanner quality | T-LEGAL-FP-01 missed must-block / false-block | 0 missed; ≤ 5 % |
| Fast-path rate | share of questions answered with one model call | measure and disclose |
| Latency / memory | p50/p95 and peak | measure and disclose |

Report denominators, confusion matrices, per-fixture results and representative failures.

---

## 3. Protocol

1. Freeze fixtures and question rows before the run; hash them.
2. Index each fixture through the real pipeline (Phase 1/3). Confirm gold sids resolve to the
   intended sentences; fix annotations, not the app, when they disagree.
3. Run the full question set with the default model, temperature 0, seed 42, one run per question.
   Log route/path, call counts, validation codes and status; never log question/answer text.
4. Human-label citation support and unsupported claims on held-out answers (the author who wrote
   the answer does not label their own).
5. Report per-category results and every failed gate. Missing a target means fix and rerun or
   document the failure; it is not a rounding error.
6. Do the same for the E2B-vs-E4B benchmark (`MODEL_BENCHMARK.md`) and, only if built, dense or
   Hermes comparisons.

---

## 4. What the validator does and does not prove

Proves: schema compliance, provenance, quote integrity, literal/date/number presence,
modality/negation, tenant/landlord role presence, conflict section diversity, legal-verdict scan.

Does not prove: semantic faithfulness (a correct set of numbers arranged in a wrong relationship),
completeness, legal correctness, or that a paraphrase means the same thing. UCR is the measure for
this gap and is labelled as such in `LIMITATIONS.md`.

---

## 5. Results (fill only with real output)

| Metric | Target | Measured | Command/report | Date |
|---|---:|---:|---|---|
| Pipeline end-to-end on fixtures | 5/5 fixtures | pass | `python3 scripts/evaluate_fixtures.py` | 2026-10-18 |
| Invented-literal rejection | 100 % | 5/5 rejected | same report | 2026-10-18 |
| Unexposed-citation rejection | 100 % | 5/5 rejected | same report | 2026-10-18 |
| CUAD ingestion | 510/510 | 510, 0 failures | `reports/cuad_evaluation.json` | 2026-10-18 |
| Citation integrity (real corpus) | 100 % | 9,731/9,731 quotations, 0 failures | same | 2026-10-18 |
| CUAD concept false silence | measure | 0.2–2.9 % across six concepts | same | 2026-10-18 |
| India PDF path | 6/6 pages readable | 6/6, 0 OCR, 0 flags, 24/24 quotes | `reports/india_law_evaluation.json` | 2026-10-18 |
| Dual-model transport (Gemma + Hermes) | both tags reach, validate, render | pass against stub runtime; live run **not** performed | `reports/model_roundtrip.md` | 2026-10-18 |
| Bulk delete on CUAD run | no residue | temp dirs removed per contract in the CUAD loop | `scripts/evaluate_cuad.py` | 2026-10-18 |
| Fact accuracy (live model) | ≥90 % | — | — | — |
| Citation precision | ≥95 % | — | — | — |
| Citation coverage | ≥95 % | — | — | — |
| Citation integrity | 100 % | — | — | — |
| UCR | ≤5 % | — | — | — |
| Silence precision / recall | ≥95 % / ≥90 % | — | — | — |
| Legal verdicts | 0 | — | — | — |
| Injection resistance | 100 % | — | — | — |
| Answer rate / false refusals (live model) | ≥80 % / ≤15 % | — | — | — |
| Scanner (block recall / false-block) | 0 missed / ≤5 % | 48/48, 0/51 on starter corpus | `pytest tests/unit/test_legal_scanner.py` | 2026-10-18 |

The scanner row is a unit-level corpus result, not an end-to-end evaluation.
