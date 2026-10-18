
from app.validation.literal import extract_literals, missing_literals, words_to_digits


def test_amount_formats_are_equivalent():
    assert extract_literals("Rs. 25,000/-") == extract_literals("INR 25000")
    assert extract_literals("₹25,000") == {"AMT:25000"}


def test_number_words_convert_to_digits():
    assert "60" in words_to_digits("sixty (60) days")
    assert words_to_digits("twenty five percent") == "25 percent"
    assert extract_literals("twenty five percent") == {"PCT:25"}
    assert extract_literals("one hundred and twenty days") == {"N:120"}


def test_dates_normalise_across_formats():
    assert extract_literals("01/11/2026") == {"DATE:2026-11-01"}
    assert extract_literals("1 November 2026") == {"DATE:2026-11-01"}
    assert extract_literals("November 1, 2026") == {"DATE:2026-11-01"}


def test_invented_amount_is_detected():
    violations = missing_literals(
        "The deposit is Rs. 30,000/- payable by 1 November 2026.",
        ["The deposit is Rs. 25,000/- payable by 01/11/2026."],
    )
    assert [v.literal for v in violations] == ["AMT:30000"]


def test_supported_restatement_has_no_violations():
    violations = missing_literals(
        "The tenant must give sixty (60) days' notice.",
        ["The Tenant shall give sixty (60) days' written notice."],
    )
    assert violations == []
