
from app.config import Settings
from app.security.hosts import is_allowed_host
from app.security.origin import is_allowed_origin
from app.security.tokens import LaunchSessionStore


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_launch_code_is_single_use():
    clock = FakeClock()
    store = LaunchSessionStore(clock=clock, code_ttl_s=60)
    code = store.issue_code()
    session = store.redeem_code(code)
    assert session is not None
    assert store.redeem_code(code) is None
    assert store.validate(session.token)


def test_expired_code_is_rejected():
    clock = FakeClock()
    store = LaunchSessionStore(clock=clock, code_ttl_s=60)
    code = store.issue_code()
    clock.now += 61
    assert store.redeem_code(code) is None


def test_tokens_are_not_valid_after_revoke():
    store = LaunchSessionStore()
    session = store.redeem_code(store.issue_code())
    store.revoke_all()
    assert session is not None
    assert not store.validate(session.token)


def test_host_allowlist_is_exact():
    settings = Settings(port=8765)
    assert is_allowed_host("127.0.0.1:8765", settings)
    assert is_allowed_host("localhost:8765", settings)
    assert not is_allowed_host("evil.example:8765", settings)
    assert not is_allowed_host("127.0.0.1:9999", settings)
    assert not is_allowed_host("127.0.0.1:8765.evil.example", settings)


def test_origin_allowlist():
    settings = Settings(port=8765)
    assert is_allowed_origin("http://127.0.0.1:8765", settings)
    assert not is_allowed_origin("http://evil.example", settings)
    assert is_allowed_origin(None, settings)
