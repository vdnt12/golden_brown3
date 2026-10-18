"""Deterministic query expansion (Guide 7.1, T6).

Synonyms come from the versioned rental-topic lexicon and cross-references come
from the document itself. The model is not consulted; expansion is reproducible
and cannot invent evidence.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.retrieval.crossrefs import extract_crossrefs
from app.retrieval.topics import classify_topics

MAX_TERMS = 6


@dataclass(frozen=True)
class ExpandedQuery:
    base: str
    terms: list[str]
    topics: list[str]


def expand_query(
    question: str,
    *,
    topics: dict[str, list[str]],
    document_text: str = "",
) -> ExpandedQuery:
    matched = classify_topics(question, topics)
    terms: list[str] = []
    lowered = question.lower()
    for topic in matched[:3]:
        for synonym in topics.get(topic, []):
            if synonym and synonym not in lowered and len(synonym) > 2:
                terms.append(synonym)
            if len(terms) >= MAX_TERMS:
                break
    refs = extract_crossrefs(document_text) if document_text else []
    for ref in refs[:2]:
        phrase = ref.phrase.lower()
        if phrase not in lowered:
            terms.append(phrase)
    return ExpandedQuery(base=question, terms=terms[:MAX_TERMS], topics=matched)


def expanded_queries(expanded: ExpandedQuery) -> list[str]:
    """Two bounded attempts: the question, then question + expansion terms."""
    queries = [expanded.base]
    if expanded.terms:
        queries.append(" ".join([expanded.base, *expanded.terms]))
    return queries
