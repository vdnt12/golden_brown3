
from app.retrieval.crossrefs import extract_crossrefs
from app.retrieval.topics import classify_topics, load_topics


def test_topic_lexicon_classifies_deposit_question(repo_root):
    topics = load_topics(repo_root / "lexicons" / "rental_topics.yaml")
    matched = classify_topics("How much is the security deposit?", topics)
    assert matched[0] == "deposit"


def test_crossrefs_find_clause_schedule_and_subject_to():
    refs = extract_crossrefs(
        "Subject to clause 7.2, the deposit is refundable per Schedule B; "
        "in accordance with clause 4, notice must be written."
    )
    kinds = {(ref.kind, ref.ref.lower()) for ref in refs}
    assert ("subject_to", "7.2") in kinds
    assert ("schedule", "b") in kinds
    assert ("in_accordance", "4") in kinds


def test_dates_are_not_cross_references():
    assert extract_crossrefs("The term starts on 01.11.2026.") == []
