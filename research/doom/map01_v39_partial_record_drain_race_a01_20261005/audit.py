import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
errors = []

def sha256(path):
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()

lock = json.loads((ROOT / "SOURCE_LOCK.json").read_text(encoding="utf-8"))
for relative, expected in lock["packaged_sha256"].items():
    if sha256(ROOT.parents[2] / relative) != expected:
        errors.append(f"source hash mismatch: {relative}")

upstream = (ROOT.parents[2] / "upstream_sources" / "test_cancel_release.py").read_text(encoding="utf-8")
adapted = (ROOT.parents[2] / "research" / "doom" / "map01_v39_cancel_release_fix_a01_20261005" / "test_cancel_release.py").read_text(encoding="utf-8")
old = 'FIX_PATH = DOOM / "map01_v39_cancel_release_fix_a01_20261005"'
new = 'FIX_PATH = Path(__file__).resolve().parent'
if upstream.count(old) != 1 or upstream.replace(old, new) != adapted:
    errors.append("test_cancel_release.py adaptation differs beyond its path redirect")

run = json.loads((ROOT / "RUN.json").read_text(encoding="utf-8"))
raw = (ROOT / run["raw_output"]).read_text(encoding="utf-8")
if run["exit_code"] != 0:
    errors.append("probe exit code was not zero")
tests = (
    "test_confirmed_per_key_up_clears_bridge_hold_before_aggregate_returns",
    "test_unavailable_per_key_sample_leaves_stale_bridge_hold_after_owner_verifies_empty",
    "test_v3_completion_barrier_clears_bridge_hold_after_empty_verification",
    "test_v3_cancellation_keeps_one_contextual_release_receipt",
)
for name in tests:
    if not re.search(rf"^{re.escape(name)} \(.*\) \.\.\. ok$", raw, re.MULTILINE):
        errors.append(f"missing passing test receipt: {name}")
if not re.search(r"Ran 4 tests in [0-9.]+s\s+OK", raw):
    errors.append("four-test unittest summary missing")

manifest = ROOT / "SHA256SUMS"
for line in manifest.read_text(encoding="utf-8").splitlines():
    expected, relative = line.split("  ", 1)
    if sha256(ROOT.parents[2] / relative) != expected:
        errors.append(f"package checksum mismatch: {relative}")

print(json.dumps({"status": "PASS" if not errors else "FAIL",
                  "locked_sources_verified": len(lock["packaged_sha256"]),
                  "test_receipts_verified": len(tests),
                  "errors": errors}, indent=2))
raise SystemExit(1 if errors else 0)
