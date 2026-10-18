"""Read-only checks for the retained soft-observation rejection result."""
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parent
EXPECTED = {
    "baseline_controller.py": "0ced693d82ff38a80963adc54ff241e4d4abdbb3835d55a12856529c49c91e00",
    "candidate_controller.py": "77ad1c74cb9071628d2329cee0049466b9e93e9117cbca568a2ed68240d7fdce",
    "candidate_test.py": "59ac0e3ff754b58bce6d405cf8ce4320b30a64905d1bf98203831d30e24e4f4f",
}
for name, digest in EXPECTED.items():
    actual = sha256((PACKAGE / name).read_bytes()).hexdigest()
    assert actual == digest, (name, actual)

baseline = (PACKAGE / "baseline-RED.stdout.txt").read_text()
assert "RuntimeError: {'event': 'rejected'" in baseline
assert "FAILED (errors=1)" in baseline

candidate_source = (PACKAGE / "candidate_controller.py").read_text()
candidate_test = (PACKAGE / "candidate_test.py").read_text()
assert "if accepted[\"event\"] == \"rejected\" and allow_rejection:" in candidate_source
assert 'initial_cover_admission = submit_cover(cover, allow_rejection=True)' in candidate_source
assert 'if initial_cover_admission["event"] in ("policy_invalidation", "rejected"):' in candidate_source
assert "test_soft_observation_stale_submit_is_recorded_without_aborting_controller" in candidate_test

checks = {
    "wait.stdout.txt": (13, "OK"),
    "wait_opt.stdout.txt": (13, "OK"),
    "controller.stdout.txt": (6, "OK"),
    "controller_opt.stdout.txt": (6, "OK"),
    "source_refresh.stdout.txt": (13, "OK"),
    "source_refresh_opt.stdout.txt": (13, "OK"),
}
for name, (count, ending) in checks.items():
    raw = (PACKAGE / name).read_text()
    assert f"Ran {count} tests" in raw and ending in raw, name
    assert "FAILED" not in raw, name

assert (PACKAGE / "compile.stdout.txt").read_text() == ""
assert (PACKAGE / "diff-check.stdout.txt").read_text() == ""
print("PASS_AUDIT_SYNTHETIC_SOFT_REJECTION: hashes, preserved baseline RED, scoped source guard, and six retained suite outputs")
