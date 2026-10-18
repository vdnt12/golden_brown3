# LexiGuard

**Private, evidence-backed triage of rental and leave-and-licence agreements — design stage.**

> **Status: pre-implementation.** This repository currently contains a design specification and licence only. There is no application, no tests, no benchmark and no privacy report yet. Nothing below describes software you can run today.

## What LexiGuard is meant to do

Help a non-lawyer read an English rental or leave-and-licence agreement (PDF or TXT):

- explain what the readable document says and point to the exact passage;
- keep quoted source text visibly separate from LexiGuard's own explanation;
- say plainly when a topic could not be located, or when the text is ambiguous or inconsistent;
- explain common rental terms from a small curated glossary (not lawyer-reviewed);
- say when a question needs a qualified professional.

LexiGuard is **not a lawyer** and is designed never to give a legal verdict, such as whether a clause is valid or enforceable.

## Planned approach (not yet built)

- Local inference with a Gemma 4 model through Ollama, on the user's own machine.
- Lexical-first retrieval (SQLite FTS5) with a rental-topic lexicon. No vector database.
- The model proposes points that cite sentence IDs; deterministic code checks them and renders the quotes, pages and sections itself.
- Fail closed: if a point cannot be supported, it is limited or withheld rather than guessed.

## What is and is not verified

| Claim | Status |
|---|---|
| Runs on-device / no data leaves the machine | **Design goal. Not verified.** No isolated-network test has been run. |
| Citations are verbatim | **Design goal. Not verified.** No code exists. |
| Accuracy or answer quality | **Not measured.** |
| Legal review of the glossary | **None.** |

These rows will change only when a committed report supports them.

## Documents

- [`docs/SOLUTION_GUIDE_v3.md`](docs/SOLUTION_GUIDE_v3.md): design specification
- [`docs/MASTER_IMPLEMENTATION_PROMPT_v3.txt`](docs/MASTER_IMPLEMENTATION_PROMPT_v3.txt): build instructions for the coding agent
- [`docs/REVIEW_FINDINGS_v3.md`](docs/REVIEW_FINDINGS_v3.md): independent review of the specification

## Context

Built for ZeroDay OSS Hacktoberfest 2026, Problem Statement 2 (Private Legal Document Triage Agent).

## Licence

Apache-2.0. See [`LICENSE`](LICENSE).

## Not legal advice

LexiGuard output, once it exists, will be general information about a document's wording. It is not legal advice. For decisions about signing, disputes or rights, consult a qualified lawyer.
