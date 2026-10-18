from app.ingest.worker import limits_report


def test_platform_matrix_reports_honest_capabilities():
    limits = limits_report()
    assert limits["wall_clock_timeout"] is True
    assert limits["output_cap"] is True
    assert limits["page_cap"] is True
    assert limits["child_process"] is True
    assert isinstance(limits["address_space_limit"], bool)
    assert isinstance(limits["cpu_limit"], bool)


def test_startup_notice_is_empty_or_explains_reduced_isolation():
    notice = limits_report()["startup_notice"]
    assert isinstance(notice, str)
    if notice:
        lowered = notice.lower()
        assert "limit" in lowered or "isolation" in lowered
