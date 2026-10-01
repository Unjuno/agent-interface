#!/usr/bin/env python3
"""Reproduce a finite set of defects in the immutable Issue #3675 auditor."""

import copy
import hashlib
import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile


ROOT = pathlib.Path(__file__).resolve().parent
FROZEN = ROOT / "frozen"
AUDIT_PATH = FROZEN / "audit.py"
RAW_PATH = FROZEN / "raw.json"
FREEZE_PATH = FROZEN / "FREEZE.json"
ORIGINAL_AUDIT_PATH = FROZEN / "audit.json"

EXPECTED_SHA256 = {
    "raw": "ccb9a75eefb7df73cb13dbc9191d33334fb672c2fd58fcc5fa32be998e182807",
    "freeze": "f40494b1be99fb1e68d7b09c498297df35a72c043740b5f09d3faec7e059acfe",
    "audit_source": "464e2a8dc14f41760639e37bbe6c0cfca2e8adb66d2fe0c007cb4c74b33136e6",
    "original_audit": "fdce1b10b7c46381d41d1e0151476b548658de0354bd4ef3db0af3d33200e4dc",
}
EXPECTED_ACCEPTED = {
    "unexpected_event",
    "duplicate_stale",
    "contradictory_bridge",
    "reordered_transitions",
    "unsupported_field",
}
EXPECTED_REJECTED = {"mutate_xid", "admit_stale", "hide_emission", "missing_transition"}
EXPECTED_CLI_STDERR = "usage: audit.py RAW_JSON [--freeze FREEZE_JSON --output AUDIT_JSON]\n"


def errors_for_frozen_auditor(raw):
    spec = importlib.util.spec_from_file_location("frozen_audit", AUDIT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.errors_for(raw)


def build_variants(raw):
    variants = {}

    def add(name, change):
        changed = copy.deepcopy(raw)
        change(changed)
        variants[name] = changed

    add("mutate_xid", lambda item: item["events"][1]["identity"].__setitem__("xid", -1))
    add("admit_stale", lambda item: next(event for event in item["events"]
                                           if event.get("event") == "stale_admission").__setitem__("admitted", True))
    add("hide_emission", lambda item: next(event for event in item["events"]
                                            if event.get("event") == "fresh_positive_control")["click"].__setitem__("emissions", 0))
    add("unexpected_event", lambda item: item["events"].append({"event": "unexpected"}))
    add("duplicate_stale", lambda item: item["events"].insert(
        4, copy.deepcopy(next(event for event in item["events"] if event.get("event") == "stale_admission"))))
    add("contradictory_bridge", lambda item: next(event for event in item["events"]
                                                   if event.get("event") == "stale_admission").__setitem__("would_call_bridge", True))
    add("reordered_transitions", lambda item: item["events"].__setitem__(
        slice(2, 4), list(reversed(item["events"][2:4]))))
    add("missing_transition", lambda item: item["events"].__delitem__(2))
    add("unsupported_field", lambda item: item["events"][0].__setitem__("unexpected_field", True))
    return variants


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    actual_sha256 = {
        "raw": sha256(RAW_PATH),
        "freeze": sha256(FREEZE_PATH),
        "audit_source": sha256(AUDIT_PATH),
        "original_audit": sha256(ORIGINAL_AUDIT_PATH),
    }
    raw = json.loads(RAW_PATH.read_text(encoding="utf-8"))
    variants = build_variants(raw)
    baseline_errors = errors_for_frozen_auditor(raw)
    mutations = {name: errors_for_frozen_auditor(value) for name, value in variants.items()}

    with tempfile.TemporaryDirectory(prefix="issue3676-frozen-probe-") as temp:
        cli_output = pathlib.Path(temp) / "audit.json"
        cli = subprocess.run(
            [sys.executable, str(AUDIT_PATH), str(RAW_PATH), "--freeze", str(FREEZE_PATH),
             "--output", str(cli_output)],
            capture_output=True,
            text=True,
            check=False,
        )

    accepted = sorted(name for name, errors in mutations.items() if not errors)
    rejected = sorted(name for name, errors in mutations.items() if errors)
    failures = []
    if actual_sha256 != EXPECTED_SHA256:
        failures.append("frozen input/source hashes differ from the recorded probe")
    if baseline_errors:
        failures.append("baseline raw no longer passes the frozen auditor")
    if set(accepted) != EXPECTED_ACCEPTED:
        failures.append("accepted mutation set differs from the recorded weakness set")
    if set(rejected) != EXPECTED_REJECTED:
        failures.append("rejected control set differs from the recorded control set")
    if cli.returncode != 1 or cli.stdout or cli.stderr != EXPECTED_CLI_STDERR:
        failures.append("documented frozen-auditor CLI usage failure differs")

    result = {
        "decision": "PASS_REPRODUCED_FROZEN_AUDIT_WEAKNESSES" if not failures else "FAIL_PROBE_REPRODUCTION_CHANGED",
        "scope": "finite offline audit/tooling reproduction only; no formal X11 rerun",
        "sha256": actual_sha256,
        "baseline_errors": baseline_errors,
        "mutations": mutations,
        "expected_accepted": sorted(EXPECTED_ACCEPTED),
        "observed_accepted": accepted,
        "expected_rejected": sorted(EXPECTED_REJECTED),
        "observed_rejected": rejected,
        "cli": {"exit_code": cli.returncode, "stdout": cli.stdout, "stderr": cli.stderr},
        "failures": failures,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
