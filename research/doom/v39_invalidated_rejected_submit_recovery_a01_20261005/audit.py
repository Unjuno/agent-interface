"""Read-only audit of the retained rejection-recovery construction result."""
from hashlib import sha256
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parent
EXPECTED = {
    "candidate_controller.py":
        "ee966869d45f4b3f261c5f675e100edd9ed2f20fa9fc42b9523e2aeb7b065c14",
    "candidate_test.py":
        "da4628b61d255c4d53426e41c85b01665c26e3289bb3c4a587b75b5c3cdca827",
}
BASELINE_SHA256 = "091eebed4bee6d4f385fd6d0431bfbecae7f8778f1949e841df2edacdda8dfa1"

for relative, expected in EXPECTED.items():
    actual = sha256((PACKAGE / relative).read_bytes()).hexdigest()
    if actual != expected:
        raise SystemExit(f"FAIL source hash {relative}: {actual}")

source = (PACKAGE / "candidate_controller.py").read_text()
tests = (PACKAGE / "candidate_test.py").read_text()
integrated_source = (ROOT / "research/doom/map01_overlap_controller_v39.py").read_text()
raw = (PACKAGE / "candidate.stdout.txt").read_text()
integrated_raw = (PACKAGE / "integrated.stdout.txt").read_text()
integrated_opt_raw = (PACKAGE / "integrated_opt.stdout.txt").read_text()
controller_raw = (PACKAGE / "controller.stdout.txt").read_text()
controller_opt_raw = (PACKAGE / "controller_opt.stdout.txt").read_text()
source_refresh_raw = (PACKAGE / "source_refresh.stdout.txt").read_text()
source_refresh_opt_raw = (PACKAGE / "source_refresh_opt.stdout.txt").read_text()
baseline_source = (PACKAGE / "baseline_controller.py").read_bytes()
baseline_raw = __import__("json").loads((PACKAGE / "baseline.stdout.json").read_text())
assert sha256(baseline_source).hexdigest() == BASELINE_SHA256
assert baseline_raw["disposition"] == "BASELINE_REPRODUCED_RELEASE_TIMEOUT"
assert baseline_raw["consumed_events"] == ["observation", "rejected", "cancel_requested"]
assert baseline_raw["submitted_commands"][-1] == {"id": "cover-0", "op": "cancel"}
assert baseline_raw["release_event_available"] is False
assert "def resolve_invalidated_cover_submission(wait, cover_id):" in source
assert 'return {"status": "rejected", "response": response}' in source
assert 'if admission_resolution["status"] == "accepted":' in source
assert "def resolve_invalidated_cover_submission(wait, cover_id):" in integrated_source
assert "test_rejected_initial_submission_is_not_cancelled_as_an_admitted_program" in tests
assert '"initial_cover_admission_resolution"]["status"],\n                         "rejected"' in tests
assert "Ran 12 tests" in raw and "OK" in raw
assert "Ran 12 tests" in integrated_raw and "OK" in integrated_raw
assert "Ran 12 tests" in integrated_opt_raw and "OK" in integrated_opt_raw
assert "Ran 6 tests" in controller_raw and "OK" in controller_raw
assert "Ran 6 tests" in controller_opt_raw and "OK" in controller_opt_raw
assert "Ran 13 tests" in source_refresh_raw and "OK" in source_refresh_raw
assert "Ran 13 tests" in source_refresh_opt_raw and "OK" in source_refresh_opt_raw
print("PASS: baseline hash/rejection timeout, repaired source gate, regression assertions, and 12-test raw result")
