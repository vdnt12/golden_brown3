
"""Bounded, nonce-delimited evidence packets (Guide 8.5, 8.3a).

Caps: 12 chunks and ~2,500 estimated tokens per packet. Oversized packets are
rejected (never truncated silently inside the model prompt).
"""
from __future__ import annotations

import secrets
from dataclasses import dataclass

from app.core.textmetrics import estimate_tokens

MAX_CHUNKS = 12
MAX_PACKET_TOKENS = 2500


class PacketTooLarge(ValueError):
    pass


@dataclass(frozen=True)
class PacketItem:
    ev_id: str
    sid: str
    page: int
    section: str | None
    text: str
    heading: str = ""


@dataclass
class EvidencePacket:
    items: list[PacketItem]
    nonce: str
    estimated_tokens: int
    dropped: int = 0

    def block(self) -> str:
        lines = [f"<<EVIDENCE-{self.nonce}>>"]
        for item in self.items:
            section = item.section or "-"
            heading = f" | {item.heading}" if item.heading else ""
            lines.append(f"[{item.sid}] p{item.page} s{section}{heading}: {item.text}")
        lines.append(f"<<END-EVIDENCE-{self.nonce}>>")
        return "\n".join(lines)


def build_packet(
    items: list[PacketItem], *, max_tokens: int = MAX_PACKET_TOKENS
) -> EvidencePacket:
    """Select the highest-ranked items that fit the packet budget.

    Selection is deterministic and reported (`dropped`), never a silent
    mid-sentence truncation: a quotation is either included whole or omitted.
    If even the first item cannot fit, the packet is genuinely too large and
    the call fails closed.
    """
    if len(items) > MAX_CHUNKS:
        raise PacketTooLarge(f"chunk cap is {MAX_CHUNKS}")
    nonce = secrets.token_hex(8)
    selected: list[PacketItem] = []
    used = 0
    for item in items:
        cost = estimate_tokens(item.text) + 1
        if selected and used + cost > max_tokens:
            continue
        if not selected and cost > max_tokens:
            raise PacketTooLarge(
                f"a single evidence passage exceeds {max_tokens} estimated tokens"
            )
        selected.append(item)
        used += cost
    if not selected:
        raise PacketTooLarge("no evidence fitted the packet budget")
    return EvidencePacket(
        items=selected,
        nonce=nonce,
        estimated_tokens=used,
        dropped=len(items) - len(selected),
    )
