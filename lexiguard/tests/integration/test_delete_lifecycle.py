
import pytest

from app.services.lifecycle import InvalidDocumentId, delete_document, document_dir
from app.services.privacy import canary_present, scan_for_canaries


def test_canary_detection_finds_planted_string(tmp_path):
    log = tmp_path / "app.log"
    log.write_text("clean line")
    with open(log, "a", encoding="utf-8") as handle:
        handle.write(" CANARY-LG-0001")
    assert canary_present(log.read_bytes(), ["CANARY-LG-0001"])
    assert scan_for_canaries([tmp_path], ["CANARY-LG-0001"]) == [str(log)]


def test_document_dir_rejects_traversal(tmp_path):
    with pytest.raises(InvalidDocumentId):
        document_dir(tmp_path, "../../etc")
    with pytest.raises(InvalidDocumentId):
        document_dir(tmp_path, "A" * 32)


def test_delete_removes_directory_and_reports_canary_hits(tmp_path):
    data_root = tmp_path / "data"
    doc_id = "b" * 32
    target = document_dir(data_root, doc_id)
    target.mkdir(parents=True)
    (target / "doc.sqlite3").write_bytes(b"db")
    (target / "source.txt").write_text("CANARY-LG-0002")
    log = tmp_path / "logs"
    log.mkdir()
    (log / "app.log").write_text("canary CANARY-LG-0002 present")

    report = delete_document(
        data_root=data_root,
        doc_id=doc_id,
        canaries=["CANARY-LG-0002"],
        scan_paths=[log],
    )
    assert report.directory_removed is True
    assert not target.exists()
    assert str(log / "app.log") in report.canary_hits
    assert report.forensic_erasure is False

    (log / "app.log").unlink()
    assert scan_for_canaries([log], ["CANARY-LG-0002"]) == []
