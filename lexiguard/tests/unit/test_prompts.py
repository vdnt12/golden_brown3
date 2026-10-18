
from app.agent.prompts import PromptRecord, build_answer_messages, build_evidence_block, new_nonce


def test_evidence_block_is_nonce_delimited_and_has_no_filename():
    nonce = new_nonce()
    block = build_evidence_block(
        [PromptRecord(sid="s_0001", page=2, section="3", text="The rent is due monthly.")],
        nonce,
    )
    assert block.startswith(f"<<EVIDENCE-{nonce}>>")
    assert "s_0001" in block
    assert "filename" not in block.lower()


def test_prompt_budget_guard_rejects_oversized_prompt():
    records = [PromptRecord(sid=f"s_{i:04d}", page=1, section="1", text="word " * 500) for i in range(10)]
    try:
        build_answer_messages("What is the rent?", records, max_prompt_tokens=1000)
    except ValueError as exc:
        assert "token budget" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("oversized prompt was accepted")
