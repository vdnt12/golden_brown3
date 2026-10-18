
"""Hermes *Agent framework* gateway -- NOT BUILT (ADR-0010, ADR-0011).

This guards the agent framework, not the Hermes model family: Hermes models are
served through the same `OllamaNativeProvider` as Gemma and selected explicitly.
A second, tool-calling agent runtime is deliberately absent; constructing this
class fails closed so no code path can quietly invent one.
"""
from __future__ import annotations


class HermesNotBuiltError(RuntimeError):
    pass


class HermesModelGateway:
    def __init__(self) -> None:
        raise HermesNotBuiltError(
            "The Hermes Agent framework is not built (ADR-0010). Hermes models are served "
            "through OllamaNativeProvider; the bounded runtime is the only agent runtime."
        )
