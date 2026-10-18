
import httpx
import pytest

from app.model.ollama_native import (
    ContextOverflowError,
    OllamaNativeProvider,
    assert_context_fits,
    build_chat_payload,
    parse_model_tags,
)


def test_payload_never_contains_tools_and_is_deterministic():
    payload = build_chat_payload(
        model="gemma4:e4b-it-q4_K_M",
        messages=[{"role": "user", "content": "hi"}],
        format_schema={"type": "object"},
    )
    assert "tools" not in payload
    assert payload["stream"] is False
    assert payload["think"] is False
    assert payload["options"] == {"seed": 42, "temperature": 0.0, "num_ctx": 8192}


def test_context_overflow_is_detected():
    payload = build_chat_payload(model="m", messages=[], format_schema={}, num_ctx=8192)
    with pytest.raises(ContextOverflowError):
        assert_context_fits(payload, {"prompt_eval_count": 8000, "eval_count": 300})


def test_tag_parsing_records_digest():
    tags = {"models": [{"name": "gemma4:e4b-it-q4_K_M", "digest": "dc35e8d9c606", "size": 6600000000}]}
    check = parse_model_tags(tags, "gemma4:e4b-it-q4_K_M")
    assert check is not None and check.digest == "dc35e8d9c606"
    assert parse_model_tags(tags, "gemma4:e2b-it-q4_K_M") is None


def test_non_loopback_ollama_url_is_rejected():
    with pytest.raises(ValueError):
        OllamaNativeProvider(base_url="http://10.0.0.5:11434")


def test_ollama_request_has_no_tools_key(monkeypatch):
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        import json

        body = json.loads(request.content)
        seen.update(body)
        return httpx.Response(
            200,
            json={
                "message": {
                    "content": '{"points":[{"point_id":"p1","kind":"STATED","text":"Rent is due.","sids":["s_0001"]}]}'
                },
                "prompt_eval_count": 100,
                "eval_count": 20,
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = OllamaNativeProvider(client=client)
    answer = provider.answer_from_evidence(messages=[{"role": "user", "content": "hi"}])
    assert answer.points[0].point_id == "p1"
    assert "tools" not in seen
    assert seen["think"] is False
