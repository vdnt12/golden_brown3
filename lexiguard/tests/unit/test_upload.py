
import pytest

from app.config import Settings
from app.ingest.upload import UploadRejected, UploadRejection, inspect_upload, sanitise_display_name


def test_valid_txt_is_accepted():
    result = inspect_upload("tenancy.txt", b"The Tenant shall pay rent.", Settings())
    assert result.kind == "txt"


def test_pdf_requires_magic_bytes():
    with pytest.raises(UploadRejected) as excinfo:
        inspect_upload("fake.pdf", b"not a pdf", Settings())
    assert excinfo.value.code is UploadRejection.BAD_MAGIC


def test_size_cap_is_enforced():
    settings = Settings(max_upload_bytes=10)
    with pytest.raises(UploadRejected) as excinfo:
        inspect_upload("big.txt", b"x" * 11, settings)
    assert excinfo.value.code is UploadRejection.TOO_LARGE


def test_extension_allowlist():
    with pytest.raises(UploadRejected) as excinfo:
        inspect_upload("notes.docx", b"PK", Settings())
    assert excinfo.value.code is UploadRejection.BAD_EXTENSION


def test_bad_utf8_txt_is_rejected():
    with pytest.raises(UploadRejected) as excinfo:
        inspect_upload("bad.txt", b"\xff\xfe", Settings())
    assert excinfo.value.code is UploadRejection.BAD_ENCODING


def test_display_name_never_contains_a_path():
    assert sanitise_display_name("../../etc/passwd") == "passwd"
    assert chr(0) not in sanitise_display_name("a" + chr(0) + "b.txt")
