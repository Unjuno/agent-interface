from audit import CASES, audit_receipts


def row(case):
    return {
        "case": case,
        "replay_allowed": False,
        "authority_grants": 0,
        "input_ledger": [{"kind": "dispatch"}],
        "cleanup": {"releases": [{"verified": True, "keys_down": [], "buttons_down": []}]},
    }


def test_rejects_missing_stale_repair():
    rows = [row(case) for case in CASES]
    result = audit_receipts(
        rows,
        source_hashes={"runner": "a"},
        recomputed_hashes={"runner": "a"},
        immutable_provenance={"image_id": "sha256:x"},
    )
    assert result["decision"] == "STOP_RECEIPT_INTEGRITY"
    assert "stale_repair:missing" in result["reasons"]


def test_accepts_complete_scoped_receipts():
    rows = [row(case) for case in CASES]
    rows[5]["repair"] = {
        "original_revision": 1,
        "reacquired_revision": 2,
        "second_dispatch": True,
    }
    result = audit_receipts(
        rows,
        source_hashes={"runner": "a"},
        recomputed_hashes={"runner": "a"},
        immutable_provenance={"image_id": "sha256:x"},
    )
    assert result["decision"] == "PASS_FORMAL_RECEIPT_INTEGRITY_SCOPED"
