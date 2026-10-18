
#!/usr/bin/env python3
"""Day-0 hardware gate / model benchmark helper (Guide 15.1).

Measures one ~3K-token prompt call against a local Ollama model. This is a
measurement tool, not test evidence: results must be recorded with hardware,
Ollama version and model digest in docs/MODEL_BENCHMARK.md.
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.request

OLLAMA = "http://127.0.0.1:11434"


def call(model: str, prompt_tokens_target: int) -> dict:
    filler = ("The tenant shall pay the rent on the fifth day of each month. " * 200)
    prompt = filler[: max(1000, prompt_tokens_target * 3)]
    payload = {
        "model": model,
        "stream": False,
        "think": False,
        "messages": [{"role": "user", "content": prompt + "\nReturn the JSON object with ok=true."}],
        "format": {"type": "object", "properties": {"ok": {"type": "boolean"}}, "required": ["ok"]},
        "options": {"seed": 7, "temperature": 0, "num_ctx": 8192},
    }
    request = urllib.request.Request(
        f"{OLLAMA}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    with urllib.request.urlopen(request, timeout=600) as response:
        body = json.loads(response.read().decode("utf-8"))
    wall = time.perf_counter() - started
    return {
        "model": model,
        "wall_s": round(wall, 2),
        "prompt_eval_count": body.get("prompt_eval_count"),
        "eval_count": body.get("eval_count"),
        "content": (body.get("message") or {}).get("content", "")[:200],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", default=["gemma4:e4b-it-q4_K_M", "gemma4:e2b-it-q4_K_M"])
    parser.add_argument("--prompt-tokens", type=int, default=3000)
    parser.add_argument("--out", default="reports/model_benchmark.json")
    args = parser.parse_args()

    results = []
    for model in args.models:
        try:
            results.append(call(model, args.prompt_tokens))
            print(json.dumps(results[-1]))
        except Exception as exc:  # noqa: BLE001
            results.append({"model": model, "error": str(exc)})
            print(f"ERROR {model}: {exc}")
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2)
    print(f"Wrote {args.out}. Record hardware, Ollama version and digests in docs/MODEL_BENCHMARK.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
