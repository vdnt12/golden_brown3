
from app.ingest.normalize import normalize_text
from app.ingest.segment import segment_page, split_sentences_with_spans


def test_normalisation_is_nfc_and_lf():
    text = normalize_text("Rent\r\nPayable by 5th.\r\n\r\n\r\nCaf\u0065\u0301")
    assert "\r" not in text
    assert "Caf\u00e9" in text
    assert "\n\n\n" not in text


def test_sentence_offsets_round_trip(sample_page: str):
    records = segment_page(1, sample_page)
    assert records
    for record in records:
        assert sample_page[record.char_start:record.char_end] == record.text


def test_abbreviations_and_decimals_do_not_split():
    spans = split_sentences_with_spans("The rent is Rs. 25,000/- per month. It is due on 5.5.2026.")
    assert [s for _, _, s in spans] == [
        "The rent is Rs. 25,000/- per month.",
        "It is due on 5.5.2026.",
    ]


def test_sections_are_tracked_from_numbered_headings(sample_page: str):
    records = segment_page(1, sample_page)
    sections = {r.section for r in records}
    assert {"1", "2", "3"} <= sections
    rent = [r for r in records if "25,000" in r.text][0]
    assert rent.section == "2"


def test_sids_are_deterministic_and_sequential(sample_page: str):
    first = segment_page(1, sample_page)
    again = segment_page(1, sample_page)
    assert [r.sid for r in first] == [r.sid for r in again]
    assert first[0].sid == "s_0001"
