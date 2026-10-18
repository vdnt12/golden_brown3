
"""Live model tests are opt-in. They are skipped unless LEXIGUARD_OLLAMA_LIVE=1.

These do not run in ordinary CI and are not a substitute for Phase 2's
T-MODEL-* acceptance run (which records version, digest and thresholds).
"""
import os

import pytest

pytestmark = pytest.mark.requires_ollama


@pytest.mark.skipif(os.environ.get("LEXIGUARD_OLLAMA_LIVE") != "1", reason="live Ollama not enabled")
def test_model_answers_with_valid_schema():
    from app.model.ollama_native import OllamaNativeProvider

    provider = OllamaNativeProvider()
    answer = provider.answer_from_evidence(
        messages=[{"role": "user", "content": "Return one STATED point with sids [s_0001] using this text: The rent is due on the fifth."}]
    )
    assert answer.points
