
from app.services.privacy import canary_present


def test_canary_matching_is_byte_based():
    assert canary_present(b"prefix CANARY-XYZ suffix", ["CANARY-XYZ"])
    assert not canary_present(b"prefix", ["CANARY-XYZ"])
