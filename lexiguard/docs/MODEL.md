# Model contract

## Model

| Item | Value |
|---|---|
| Primary tag | `gemma4:e4b-it-q4_K_M` (GGUF q4_K_M only) |
| Memory-constrained alternative | `gemma4:e2b-it-q4_K_M`, same quantisation family |
| Forbidden | `:cloud`, `-mlx`, `-nvfp4`, `-mxfp8`, `-qat`, 12B/26B/31B, any cloud fallback |
| Minimum Ollama | 0.21.1 (fixes `think:false` dropping `format` on Gemma 4) |
| API | native `POST http://127.0.0.1:11434/api/chat` (never `/v1`) |
| Request | `stream:false`, `think:false`, simple app-owned JSON Schema, `options.seed` fixed, `temperature:0`, `num_ctx:8192` |
| Never sent | `tools` key — tool choice is a schema-constrained `NextAction` executed by code |
| Output validation | Pydantic always; one format-retry; empty/invalid content fails closed |
| Context guard | pre-budget by chars/3.2 **and** `prompt_eval_count + eval_count < num_ctx` |
| Tags/digest | record from *your* `/api/tags`; tags move |
| Tags seen 2026-10-18 | E4B 6.6 GB `dc35e8d9c606`; E2B 4.6 GB `b37049369adf` (informational only) |

## Who does what (publish this in every demo)

| Gemma may propose | Deterministic code decides |
|---|---|
| Route proposal only when the pre-router is unsure; query-expansion terms; one `NextAction`; the text of restatement/interpretation/concern/ambiguity/conflict points; reading-level paraphrase of curated glossary entries | File validation, ids, page/section metadata, offsets, hashes, DB, retrieval caps, citation rendering, validation, legal policy, status/route precedence, missing-information decisions, jurisdiction/escalation panels, deletion, network policy, tool allowlists, schema validation |

The model never returns quotes, page numbers, section numbers, evidence ids, final statuses,
missing-information decisions, professional-review flags or legal verdicts. `ModelAnswer` is
`{points:[{point_id, kind, text, sids}]}` with unknown keys rejected.

## Call budget

| Path | Calls | Worst case |
|---|---|---|
| Fast (confident retrieval) | 1 answer call | answer + format retry + validation retry = 3 |
| Refinement | 1 refinement **or** 1 NextAction, then answer | 4 total |
| Ceiling | **4 per question**, retries included | fail closed at the ceiling |
| Router proposal | only when pre-router unsure | counts inside the 4 |
| Entailment pass | off by default (Tier 2) | — |
| Wall clock | 4 × Day-0 p50, capped by request timeout | skip refinement if > half spent |

Evidence packet ≤ ~2,500 estimated tokens; prompt pre-budget ~3,000 tokens.

## Failure mapping

| Condition | Result |
|---|---|
| Ollama unreachable / non-200 | `ERROR_LOCAL_MODEL_UNAVAILABLE` (no fallback) |
| Empty `message.content` (even if thinking exists) | failure; never parsed |
| Invalid JSON / schema after one retry | `ERROR_PROCESSING` |
| `prompt_eval_count + eval_count ≥ num_ctx` | `ERROR_PROCESSING` (`ContextOverflowError`) |
| All points rejected by validation | `INSUFFICIENT_EVIDENCE` |

## Secrecy and logging

- Only a bounded question and the nonce-delimited evidence block enter the prompt. Filenames, file
  metadata, full documents, prior answers and run history are excluded.
- Thinking text is never parsed or shown.
- “Why this answer?” exposes route/path/tool names/counts/validation codes/duration — never
  chain-of-thought or prompt text.

## Interface

```python
class LLMProvider(Protocol):
    def answer_from_evidence(self, *, messages) -> ModelAnswer: ...
    def route_proposal(self, *, question) -> RouterProposal | None: ...
    def expand_query(self, *, question, topic) -> list[str] | None: ...
    def next_action(self, *, question, evidence_block, known_refs, page_count) -> NextAction: ...
    def unload(self) -> bool: ...
```

`OllamaNativeProvider` is the only implementation and serves every allowlisted tag, including
`hermes3:8b`. `HermesModelGateway` (the *agent framework*) refuses construction
(ADR-0010). No arbitrary URL or model name is ever accepted from a client.
