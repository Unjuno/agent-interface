"""Independent audit of the one-field admission-keycode candidate probe."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import probe


HERE = Path(__file__).resolve().parent
OLD = (
    b"result = dict(event='input_admission', key=key, admitted_ns=admitted,\r\n"
    b"                                          input_ack_ns=time.perf_counter_ns(), valid_until_ns=lease.deadline)"
)
NEW = (
    b"result = dict(event='input_admission', key=key, keycode=code, admitted_ns=admitted,\r\n"
    b"                                          input_ack_ns=time.perf_counter_ns(), valid_until_ns=lease.deadline)"
)


def audit():
    freeze = json.loads((HERE / "REPAIR_FREEZE.json").read_text(encoding="utf-8"))
    for line in (HERE / "REPAIR_FILES.sha256").read_text(encoding="utf-8").splitlines():
        expected, name = line.split("  ", 1)
        actual = hashlib.sha256((HERE / name).read_bytes()).hexdigest()
        assert actual == expected, (name, actual, expected)
    source = probe.candidate_source()
    assert source.count(OLD) == 1
    patched = source.replace(OLD, NEW, 1)
    patched_sha256 = hashlib.sha256(patched).hexdigest()

    result = json.loads((HERE / "REPAIR_RESULT.json").read_text(encoding="utf-8-sig"))
    assert result["baseline_git_blob"] == freeze["source_git_blob"]
    assert result["candidate_source_sha256"] == patched_sha256
    assert result["mutation"] == freeze["candidate_mutation"]
    control, alias = result["arms"]
    for arm in (control, alias):
        assert arm["release_verified"] is True
        assert arm["reason"] == "cancelled"
        assert arm["admission_keycodes"] == [row["keycode"] for row in arm["admissions"]]
        assert [row["key"] for row in arm["admissions"]] == ["W", "A"]
    assert control["admission_keycodes"] == control["release_keycodes"] == [87, 65]
    assert alias["admission_keycodes"] == [77, 77]
    assert alias["release_keycodes"] == [77]
    return {
        "schema": "map01-cancel-keycode-identity-repair-audit-v1",
        "status": "PASS_SCOPED",
        "candidate_source_sha256": patched_sha256,
        "checks": [
            "pinned baseline source blob",
            "repair artifact SHA256 inventory",
            "unique one-line source mutation",
            "candidate source digest",
            "injective physical-key identity join",
            "aliased symbols explicitly share one physical-key interval",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
