# Model benchmark

**Status: not run. This file contains a method and empty tables, not results.**
Any published number must come from `scripts/benchmark_model.py`, with the environment recorded in
`MODEL_SETUP.md` and the raw output saved under `reports/`.

---

## 1. Purpose

Two questions:

1. Is the chosen model usable on the demo machine? (Day-0 gate: E4B p50 > ~60 s for a ~3K-in /
   ~300-out call → default to E2B; neither under ~120 s → stop.)
2. Which of E2B/E4B gives the better quality/latency trade-off on *our* evidence packets, at the
   same quantisation family, seed, context and retrieval inputs?

---

## 2. Method

| Control | Value |
|---|---|
| Models | `gemma4:e4b-it-q4_K_M`, `gemma4:e2b-it-q4_K_M` |
| Quantisation | same family (q4_K_M), no `-qat`/`-mlx` |
| Ollama | pinned version (record) |
| Context | `num_ctx: 8192` sent per request |
| Sampling | seed 7, temperature 0, `think:false`, `stream:false` |
| Prompt | identical packet(s) from real retrieval output, not hand-written gold text |
| Repeats | ≥5 per prompt per model; report p50/p95, min/max |
| Metrics | wall-clock, `prompt_eval_count`, `eval_count`, tokens/s if reliable, peak RSS/VRAM |
| Quality | same question set and validator, scored with the evaluation metrics in `EVALUATION.md` |

Hermes (`hermes3:8b`) is available as a second tag and may be compared with the same harness;
dense retrieval is not built and cannot be compared.

---

## 3. Results (to fill)

### 3.1 Day-0 smoke (3K-in / 300-out)

| Model | p50 wall (s) | p95 wall (s) | Prompt tokens | Output tokens | Peak memory | Notes |
|---|---:|---:|---:|---:|---|---|
| E4B | | | | | | |
| E2B | | | | | | |

Decision: ______________________ (default model, reason, date).

### 3.2 Evaluated answer quality

| Model | Fact acc. | Citation precision | Citation coverage | UCR | Answer rate | False refusals | p50 / p95 latency |
|---|---:|---:|---:|---:|---:|---:|---|
| E4B | | | | | | | |
| E2B | | | | | | | |

### 3.3 Deviation log

Record every failed call, format retry, context overflow, empty reply and outlier latency. A
benchmark with hidden failures is not a benchmark.

| # | Model | Symptom | Count | Handling |
|---|---|---|---:|---|
| | | | | |
