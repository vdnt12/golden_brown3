
"""Conservative token estimation (Guide 8.3a).

Characters / 3.2 is deliberately pessimistic. Every evidence packet and prompt
is pre-budgeted with this estimate AND post-checked against
prompt_eval_count + eval_count from Ollama (T-MODEL-CTX-01).
"""
from __future__ import annotations

import math

CHARS_PER_TOKEN = 3.2


def estimate_tokens(text: str) -> int:
    return math.ceil(len(text) / CHARS_PER_TOKEN)


def fits_context(
    prompt_tokens: int,
    output_tokens: int,
    num_ctx: int,
    safety_margin: int = 256,
) -> bool:
    return prompt_tokens + output_tokens + safety_margin < num_ctx
