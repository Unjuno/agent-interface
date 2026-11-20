"""Read-only source and claim audit for the mutable owner-record successor."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise SystemExit("AUDIT_FAIL: " + message)


lock = json.loads((PACKAGE / "SOURCE_LOCK.json").read_text())
result = json.loads((PACKAGE / "RESULT.json").read_text())
for filename, expected in lock["candidate_files_sha256"].items():
    actual = hashlib.sha256((PACKAGE / filename).read_bytes()).hexdigest()
    require(actual == expected, f"candidate hash mismatch: {filename}")

for line in (PACKAGE / "SHA256SUMS").read_text().splitlines():
    if not line.strip():
        continue
    expected, filename = line.split(None, 1)
    filename = filename.lstrip(" *")
    actual = hashlib.sha256((PACKAGE / filename).read_bytes()).hexdigest()
    require(actual == expected, f"package checksum mismatch: {filename}")

main = lock["current_main"]["commit"]
for path, expected in lock["current_main"]["dependencies"].items():
    actual = subprocess.run(
        ["git", "rev-parse", f"{main}:{path}"], cwd=ROOT,
        check=True, text=True, capture_output=True).stdout.strip()
    require(actual == expected, f"pinned main dependency mismatch: {path}")

require(result["disposition"] == "PASS_CANDIDATE_MECHANICS", "unexpected disposition")
require(result["baseline"]["tdd_red"] is True, "missing baseline RED")
require(result["candidate"]["same_record_verified_empty_clears_held"] is True,
        "missing same-record reconciliation claim")
require(result["candidate"]["published_rows_deduplicated_by_record_and_row"] is True,
        "missing duplicate-publication guard")
require(result["validation"]["candidate_normal"] == "14/14", "normal suite claim mismatch")
require(result["validation"]["candidate_optimized"] == "14/14", "optimized suite claim mismatch")
require(result["validation"]["py_compile"] == "PASS", "compile claim mismatch")
require(len(result["unverified"]) >= 5, "scope limits missing")
print("AUDIT_PASS_SOURCE_LOCK_AND_RESULT_CONTRACT")
