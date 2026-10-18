
import pytest

from app.ingest.errors import PdfMalformedError
from app.ingest.language import PageLanguage, classify_page
from app.ingest.parser import DecodeError, parse_pdf_bytes, parse_txt_bytes
from app.ingest.quality import assess_pages

ENGLISH = (
    "The Tenant shall pay the rent of Rs. 25,000 on the fifth day of each month. "
    "The Landlord shall refund the security deposit within thirty days after the "
    "Tenant vacates the premises and returns the keys. The Tenant shall not sublet "
    "the premises without the prior written consent of the Landlord. Notice must be "
    "given in writing and delivered to the address stated in this agreement."
)

DEVANAGARI = (
    "यह एक किराया समझौता है। मकान मालिक और किरायेदार के बीच यह समझौता हुआ है। "
    "किरायेदार हर महीने पांच तारीख तक किराया देगा। जमा राशि तीस दिनों में वापस की जाएगी।"
)

ROMANISED = (
    "yeh kiraya anubandh hai makaan malik aur kirayedar ke beech samjhauta hua hai "
    "kirayedar har mahine paanch tareekh tak kiraya dega jama rashi tees dinon mein "
    "wapas ki jayegi koi bhi paksha likhit soochna ke bina samjhauta khatam nahi kar "
    "sakta kirayedar bina anumati ke makaan kisi anya vyakti ko nahi dega"
)


def test_english_page_is_supported():
    verdict = classify_page(1, ENGLISH)
    assert verdict.language is PageLanguage.ENGLISH


def test_non_latin_script_page_is_unread():
    verdict = classify_page(2, DEVANAGARI)
    assert verdict.language is PageLanguage.UNREAD_LANGUAGE
    assert verdict.non_latin_ratio > 0.15


def test_romanised_non_english_is_flagged():
    verdict = classify_page(3, ROMANISED)
    assert verdict.language is PageLanguage.UNREAD_LANGUAGE


def test_low_text_page_is_an_ocr_candidate():
    report = assess_pages([(1, ENGLISH), (2, "   ")])
    assert report.ocr_candidates() == [2]
    assert report.coverage < 0.95
    assert report.coverage_ok is False


def test_txt_parsing_creates_virtual_pages():
    text = ("Paragraph one. " * 150 + "\n\n" + "Paragraph two. " * 150).encode()
    parsed = parse_txt_bytes(text)
    assert parsed.source_kind == "txt"
    assert len(parsed.pages) >= 2
    assert all(page.virtual for page in parsed.pages)
    assert "virtual pages" in parsed.warnings[0]


def test_invalid_utf8_is_rejected():
    with pytest.raises(DecodeError):
        parse_txt_bytes(b"\xff\xfe\x00bad")


def test_malformed_pdf_fails_closed():
    """A file with PDF magic but no valid structure must raise, not guess."""
    with pytest.raises(PdfMalformedError):
        parse_pdf_bytes(b"%PDF-1.7 not really a pdf")
