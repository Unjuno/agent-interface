import hashlib
from pathlib import Path

root = Path(__file__).resolve().parent
repo = root.parents[3]
targeted = (root / "TARGETED_OUTPUT.txt").read_text(encoding="utf-8")
focused = (root / "FOCUSED_SUITE_OUTPUT.txt").read_text(encoding="utf-8")
red = (root / "RED_OUTPUT.txt").read_text(encoding="utf-8")
codes = (root / "EXIT_CODES.txt").read_text(encoding="utf-8-sig")

assert "Ran 1 test" in targeted and "OK" in targeted
assert any("test_cleanup_failure_preserves_prior_step_delivery_custody" in line
           and line.rstrip().endswith("... ok")
           for line in focused.splitlines())
assert "Ran 34 tests" in focused and "OK" in focused
assert "Frozen parent: 636f61941e3da887a1641e4399c2f0e3373a7974" in red
assert "AssertionError: None !=" in red
assert all(f"{name}=0" in codes for name in (
    "targeted_exit", "focused_suite_exit", "py_compile_exit", "diff_check_exit"))
for line in (root / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
    digest, relative = line.split("  ", 1)
    actual = hashlib.sha256((repo / relative).read_bytes()).hexdigest()
    assert actual == digest, relative
print("PASS: RED identifies the missing terminal custody; candidate targeted and 34-test focused outputs and all exit codes are consistent.")
