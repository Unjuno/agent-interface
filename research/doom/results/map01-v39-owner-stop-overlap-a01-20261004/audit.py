"""Independent source and saved-output checks for stop-overlap A01."""
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
checks = {}

manifest_path = HERE / "SHA256SUMS.txt"
manifest = {}
for line in manifest_path.read_text(encoding="utf-8").splitlines():
    digest, rel = line.split("  ", 1)
    manifest[rel] = digest
actual_files = sorted(
    path.relative_to(HERE).as_posix()
    for path in HERE.rglob("*")
    if path.is_file() and path.name not in {"AUDIT.json", "SHA256SUMS.txt"}
    and "__pycache__" not in path.parts
)
checks["manifest_covers_exact_package"] = sorted(manifest) == actual_files
checks["manifest_hashes_match"] = all(
    hashlib.sha256((HERE / rel).read_bytes()).hexdigest() == digest
    for rel, digest in manifest.items()
)

source = HERE / freeze["source"]["snapshot"]
source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
checks["frozen_source_sha256"] = source_sha == freeze["source"]["sha256"]
blob = subprocess.check_output(
    ["git", "rev-parse", f"{freeze['base_main']}:{freeze['source']['path']}"],
    cwd=ROOT, text=True,
).strip()
checks["frozen_source_git_blob"] = blob == freeze["source"]["git_blob"]

cases = {}
for case_id in ("baseline", "stop-overlap"):
    row = json.loads((HERE / "raw" / f"{case_id}.json").read_text(encoding="utf-8"))
    cases[case_id] = row
    prefix = case_id + ":"
    records = row["owner_release_records_at_boundary"]
    checks[prefix + "one_keypress_one_keyrelease"] = row["xtest_events"] == [[2, 38], [3, 38]]
    checks[prefix + "no_fake_key_remains_down"] = row["remaining_fake_keycodes_down"] == []
    checks[prefix + "release_call_returns_once"] = row["release_reply_count"] == 1 and row["release_errors"] == []
    checks[prefix + "all_captured_release_records_verify_empty"] = bool(records) and all(
        rec.get("verified") is True
        and rec.get("keys_down") == []
        and rec.get("buttons_down") == []
        and type(rec.get("verified_ns")) is int
        for rec in records
    )
    checks[prefix + "first_record_is_lease_bound_release"] = (
        bool(records)
        and records[0].get("reason") == "release"
        and records[0].get("valid_until_ns") == row["admission"]["valid_until_ns"]
    )

baseline = cases["baseline"]["owner_release_records_at_boundary"]
overlap = cases["stop-overlap"]["owner_release_records_at_boundary"]
checks["baseline_has_one_boundary_release_record"] = len(baseline) == 1
checks["stop_overlap_adds_one_shutdown_record"] = (
    len(overlap) == 2
    and overlap[1].get("reason") == "stop_requested"
    and overlap[1].get("valid_until_ns") is None
)
checks["record_count_changes_without_extra_key_event"] = (
    len(overlap) == len(baseline) + 1
    and cases["baseline"]["xtest_events"] == cases["stop-overlap"]["xtest_events"]
)
checks["stop_signal_was_set_after_dequeue"] = (
    cases["baseline"]["overlap_stop_after_dequeue"] is False
    and cases["stop-overlap"]["overlap_stop_after_dequeue"] is True
)

audit = {
    "schema": "map01-v39-owner-stop-overlap-audit-v1",
    "checks": checks,
    "pass": all(checks.values()),
    "scope": "deterministic fake-Xlib owner queue/record behavior only",
}
(HERE / "AUDIT.json").write_text(
    json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8"
)
for name, passed in checks.items():
    print(f"{'PASS' if passed else 'FAIL'} {name}")
print(f"{'PASS' if audit['pass'] else 'FAIL'} {sum(checks.values())}/{len(checks)} checks")
if not audit["pass"]:
    raise SystemExit(1)
