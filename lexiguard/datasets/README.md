# Public data used for validation

Raw downloads are **not committed** (the CUAD JSON alone is 40 MB and both
datasets have their own licences). `manifest.json` pins the source, licence,
size and SHA-256 of everything used, and `scripts/fetch_*.py` reproduces the
download exactly.

| Dataset | Licence | What it is | How LexiGuard uses it |
|---|---|---|---|
| [CUAD v1](https://huggingface.co/datasets/theatticusproject/cuad) | CC BY 4.0 | 510 commercial contracts with lawyer-annotated clause spans | Deterministic validation: ingestion at scale, quotation integrity, concept coverage and false-silence rates on real legal drafting |
| [PRS Legislative Brief — Model Tenancy Act, 2021](https://prsindia.org/billtrack/the-model-tenancy-act-2021) | PRS India public brief | Policy brief on the Indian Model Tenancy Act, 2021 | PDF path, language gate and concept matcher on Indian tenancy-law prose |

## Sources that were **not** usable from this environment

Recorded because a claim of "verified against IndiaCode / open-india-law" would
otherwise be false:

| Source | Observed | Consequence |
|---|---|---|
| `indiacode.nic.in` bitstream PDFs | HTTP error page from an edge bot filter, both with `curl` and a browser User-Agent | No IndiaCode document was parsed or evaluated here |
| `mohua.gov.in` Model Tenancy Act PDF | HTTP 404 at both known paths | Not downloaded |
| `huggingface.co/datasets/vaquill/open-india-law` | HTTP 401 — gated dataset without a token | No row from this dataset was read |

To use them, obtain access (IndiaCode: download from a normal browser;
open-india-law: accept the gate and export a token), place the files under
`datasets/india_law/`, and extend `scripts/evaluate_india_law.py`. The evaluator
will report hashes it actually saw, not hashes it expects.

## What these datasets are *not*

- CUAD is **commercial** contracts, not tenancy agreements. High scores there do
  not mean the tool is accurate on a rental agreement.
- The PRS brief is a **policy summary**, not a contract. It exercises the PDF
  parser and language gate; it is not evidence of rental-answer quality.
- No model was trained or fine-tuned on either dataset. LexiGuard's behaviour is
  deterministic code plus prompting; the datasets are used for verification.
