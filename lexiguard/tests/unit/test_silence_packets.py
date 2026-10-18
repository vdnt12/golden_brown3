
import pytest

from app.core.enums import ResponseStatus
from app.retrieval.packets import PacketItem, PacketTooLarge, build_packet
from app.retrieval.silence import SilenceEvidence, evaluate_silence

FULL = dict(
    page_count=5,
    lexicon_checked=True,
    lexical_checked=True,
    headings_checked=True,
    crossrefs_checked=True,
    incorporated_material_checked=True,
)


def test_not_located_requires_every_check():
    decision = evaluate_silence(SilenceEvidence(**FULL))
    assert decision.allowed
    assert decision.status is ResponseStatus.NOT_LOCATED


def test_unread_pages_forbid_not_located():
    decision = evaluate_silence(SilenceEvidence(**FULL, unread_pages=1))
    assert not decision.allowed
    assert decision.status is ResponseStatus.INSUFFICIENT_EVIDENCE


def test_missing_crossref_check_blocks_absence_claim():
    evidence = dict(FULL)
    evidence["crossrefs_checked"] = False
    decision = evaluate_silence(SilenceEvidence(**evidence))
    assert decision.status is ResponseStatus.INSUFFICIENT_EVIDENCE


def test_packet_cap_is_twelve_chunks():
    items = [PacketItem(f"ev_{i:04d}", f"s_{i:04d}", 1, "1", "text") for i in range(13)]
    with pytest.raises(PacketTooLarge):
        build_packet(items)


def test_packet_block_is_nonce_delimited():
    packet = build_packet([PacketItem("ev_0001", "s_0001", 1, "1", "The rent is Rs. 25,000.")])
    block = packet.block()
    assert block.startswith(f"<<EVIDENCE-{packet.nonce}>>")
    assert block.endswith(f"<<END-EVIDENCE-{packet.nonce}>>")
