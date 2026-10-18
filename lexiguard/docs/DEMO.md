# Demo script

A four-minute, honest walkthrough of the working local build. It works **with or without** a local
model; with no model, step 3 shows the fail-closed behaviour instead of an answer, and that is a
legitimate thing to demo.

Prepare once:

```bash
npm install && npm run build
pip install -e '.[dev]'
OLLAMA_NO_CLOUD=1 ollama serve      # optional; ollama pull gemma4:e4b-it-q4_K_M hermes3:8b
make demo                           # prints http://127.0.0.1:8765/#k=…
```

| Time | Action | Say | What the audience sees |
|---|---|---|---|
| 0:00 | Open the printed `#k=` URL | "The launch code is in the URL fragment, so it never reaches the server. It is single-use and expires in 60 seconds." | Session bootstraps; the fragment disappears from the address bar |
| 0:20 | Read the privacy banner | "Documents are parsed, indexed and searched on this machine. Questions go only to the local model on loopback. If it is not running, the app says so instead of guessing." | Banner with the same wording |
| 0:35 | Upload `fixtures/synthetic_rental_simple.txt` | "A synthetic agreement, not a real contract. Text is parsed locally and stored in this document's own SQLite file." | Document list; map appears |
| 0:50 | Point at the document map | "Eleven concept cards. Ten found. Lock-in is **not located** — that is a statement about the readable text, not permission. Pets is not mentioned at all." | `FOUND` cards with quotes; `NOT_LOCATED` cards |
| 1:10 | Click a quotation | "This opens the exact page. The quote is rendered by the backend from stored text, not by the model. For a PDF you also see the rendered page image." | Page viewer with highlighted sentence |
| 1:30 | Ask: "What is the monthly rent and when is it due?" | "The model may only propose points that cite stored sentence ids. The backend renders the quote, the page and the status." | Answer with a quoted sentence and page number |
| 1:50 | Switch the model picker to `hermes` and ask the same question | "Same adapter, same prompt, same validator — only the tag changes, and `run_meta.model_tag` records which model produced the answer." | Answer with a different `model_tag`, same citation rules |
| 2:00 | Ask: "Is this agreement valid and can my landlord evict me?" | "That is a legal conclusion, so it is refused. It shows the relevant passages and gives neutral questions for a lawyer." | `LEGAL_LIMIT` + escalation questions |
| 2:25 | Ask: "Does the agreement mention pets?" | "Absence is only claimed when the text was readable and the silence checks ran. Otherwise it would say 'not enough readable evidence'." | `NOT_LOCATED` |
| 2:45 | Open **Review** | "Ordered for reading, not scored. Conflicts first, then ambiguity tied to money or time, then money clauses, then jurisdiction cautions." | Review list, each item quoted |
| 3:10 | Upload `fixtures/synthetic_rental_conflict.pdf` | "Two clauses disagree about notice. Both are shown; the tool does not pick a winner." | Two `CONFLICT` items with both quotes |
| 3:30 | Delete the first document | "Type DELETE. It removes the stored copy, text, index and page images, then verifies absence with canary strings." | Deletion report: files purged, database unlinked, canary scan passed, explicit "not forensic erasure" |
| 3:50 | Stop | "No accuracy or privacy claim: no live model run and no packet capture exist yet. CUAD gave us 510 real contracts with zero quote-integrity failures; that is a pipeline result, not a quality result. The limitations page says exactly that." | `docs/LIMITATIONS.md`, `reports/cuad_evaluation.md` |

## If there is no local model

The ask step returns `ERROR_LOCAL_MODEL_UNAVAILABLE` with zero claims and `legal_verdict: null`.
Say: "This is the fail-closed path. Without the local model there is no answer at all, rather than
an unverified one." Then show the map and review, which are deterministic and need no model.

## If OCR is installed

Upload a scanned PDF, show the OCR warning banner on the answer and the extracted text labelled as
OCR. Say: "OCR text is labelled everywhere it appears because it is a machine reading of an image."

## Do not say

- "100% local" or "nothing leaves the machine" — no capture exists.
- "Secure erase" — the app deletes its files and verifies absence; that is not forensic erasure.
- "Accurate" — five synthetic fixtures are not evidence of accuracy on real contracts.
