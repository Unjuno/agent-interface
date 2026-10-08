"""Read-only audit of retained PR8065 startup-selection probe outputs."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source-snapshots"
RUNS = ROOT / "startup-v5"
EXPECTED_ROUTES = {
    "v12-perkey": {
        "owner_file": "research/doom/map01_attack_onset_phase_allocation_02_v1/dependencies/v12/input_owner_v12.py",
        "cached_owner_file": "research/doom/map01_attack_onset_phase_allocation_02_v1/dependencies/v12/input_owner_v12.py",
        "matches_a01": True,
    },
    "v15-default": {
        "owner_file": "research/live_control/input_transition_owner_v4.py",
        "cached_owner_file": "research/live_control/input_owner_v12.py",
        "matches_a01": False,
    },
    "v15-perkey": {
        "owner_file": "research/live_control/input_owner_v12.py",
        "cached_owner_file": "research/live_control/input_owner_v12.py",
        "matches_a01": False,
    },
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    checks: list[dict] = []

    manifest = json.loads((ROOT / "source-manifest.json").read_text())
    manifest_failures = []
    for rel, pin in manifest["files"].items():
        path = SOURCE / (rel + ".txt")
        if not path.is_file() or sha(path) != pin["sha256"] or path.stat().st_size != pin["bytes"]:
            manifest_failures.append(rel)
    checks.append({"check": "all_56_source_manifest_entries_match", "pass": not manifest_failures,
                   "count": len(manifest["files"]), "failures": manifest_failures})

    probe_hash = sha(ROOT / "probe_startup.py")
    receipt_failures = []
    outcomes = {}
    for route, expected in EXPECTED_ROUTES.items():
        result_path = RUNS / route / "result.json"
        receipt_path = RUNS / f"{route}.receipt.json"
        stdout_path = RUNS / f"{route}.stdout.txt"
        stderr_path = RUNS / f"{route}.stderr.txt"
        result = json.loads(result_path.read_text())
        receipt = json.loads(receipt_path.read_text())
        out = json.loads(stdout_path.read_text())
        failures = []
        for name, ok in {
            "route_matches": result.get("route") == route == receipt.get("route") == out.get("route"),
            "probe_hash_matches": receipt.get("probe_sha256") == probe_hash,
            "stdout_hash_matches": receipt.get("stdout_sha256") == sha(stdout_path),
            "stderr_hash_matches": receipt.get("stderr_sha256") == sha(stderr_path),
            "stderr_empty": stderr_path.read_bytes() == b"",
            "exit_zero": receipt.get("exit_code") == 0,
            "stdout_result_matches": out == result,
            "startup_boundary_reached": result.get("source_selection_finished") is True,
            "session_not_started": result.get("session_started") is False,
            "owner_not_instantiated": result.get("owner_instantiated") is False,
            "forbidden_calls_empty": result.get("forbidden_calls") == [],
            "selected_owner_matches_expected": result.get("owner_file") == expected["owner_file"],
            "a01_identity_matches_expected": result.get("owner_matches_a01") is expected["matches_a01"],
            "cached_module_matches_expected": result.get("cached_owner_file") == expected["cached_owner_file"],
        }.items():
            if not ok:
                failures.append(name)
        if route == "v15-perkey":
            if result.get("owner_sha256") != "cbfe57373a029aa7d0ae9e70e6cf99806262f8565e27a4415d060bdf73702d9a":
                failures.append("perkey_actual_owner_hash")
            if result.get("recorded_a01_owner_sha256") != result.get("expected_a01_owner_sha256"):
                failures.append("perkey_source_manifest_records_archived_a01_hash")
            if result.get("owner_sha256") == result.get("recorded_a01_owner_sha256"):
                failures.append("perkey_expected_actual_hashes_should_differ")
        outcomes[route] = {
            "owner_file": result.get("owner_file"),
            "owner_sha256": result.get("owner_sha256"),
            "recorded_a01_owner_sha256": result.get("recorded_a01_owner_sha256"),
            "owner_matches_a01": result.get("owner_matches_a01"),
            "owner_instantiated": result.get("owner_instantiated"),
            "forbidden_calls": result.get("forbidden_calls"),
            "failures": failures,
        }
        receipt_failures.extend(f"{route}:{failure}" for failure in failures)
    checks.append({"check": "three_retained_route_receipts_and_results", "pass": not receipt_failures,
                   "count": len(EXPECTED_ROUTES), "failures": receipt_failures})

    # Route-level conclusion is explicitly limited to Python startup identity.
    v15 = outcomes["v15-perkey"]
    checks.append({
        "check": "v15_perkey_owner_identity_differs_from_recorded_a01_source",
        "pass": (v15["owner_sha256"] != v15["recorded_a01_owner_sha256"]
                 and not v15["owner_matches_a01"]),
        "observed_owner": v15["owner_file"],
        "observed_owner_sha256": v15["owner_sha256"],
        "sources_manifest_owner_sha256": v15["recorded_a01_owner_sha256"],
        "scope": "startup selection only; no owner construction or UP receipt execution",
    })
    result = {
        "schema": "v15-perkey-import-independent-audit-v1",
        "source_probe_sha256": probe_hash,
        "source_manifest_entry_count": len(manifest["files"]),
        "route_outcomes": outcomes,
        "checks": checks,
        "pass": all(check["pass"] for check in checks),
        "interpretation_limit": (
            "The route mismatch is observed at the suite.Session boundary. The missing "
            "per-key UP telemetry consequence is derived from source return contracts; "
            "these retained probes did not instantiate InputOwner or execute UP."
        ),
    }
    import sys
    output = Path(sys.argv[1])
    with output.open("x") as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"pass": result["pass"], "checks": checks}, sort_keys=True))
    if not result["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
