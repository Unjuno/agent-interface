#!/usr/bin/env python3
"""Read-only revalidation of the retained A01 packet; starts no formal command."""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
import audit


ROOT = Path(__file__).resolve().parent


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(relative: str):
    return json.loads((ROOT / relative).read_bytes())


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> int:
    freeze, run = load("FREEZE.json"), load("RUN.json")
    freeze_hash = sha(ROOT / "FREEZE.json")
    require(run["freeze_sha256"] == freeze_hash, "run/freeze binding")
    require(run["allocation_id"] == freeze["allocation_id"], "run/allocation binding")
    require(run["base_main_sha"] == freeze["base_main_sha"], "run/main binding")
    require(run["status"] == "PASS_METHOD_SCOPED", "run status")
    require((run["candidate_invocations"], run["auditor_invocations"], run["formal_retries"]) == (1, 1, 0), "one-shot receipt")
    for name, expected in freeze["sha256"].items():
        require(sha(ROOT / name) == expected, "frozen source changed: " + name)

    receipts = {}
    for role in ("candidate", "auditor"):
        directory = ROOT / "results" / role
        receipt = load("results/" + role + "/receipt.json")
        attempt = load("results/" + role + "/attempt.json")
        receipts[role] = receipt
        require(receipt["role"] == role, "role binding")
        require(receipt["argv"] == freeze["commands"][role], "argv binding")
        require(receipt["source_commit"] == run["source_freeze_commit"], "source commit binding")
        require(receipt["source_sha256"] == freeze["sha256"], "receipt source hashes")
        require(receipt["freeze_sha256"] == freeze_hash, "receipt freeze binding")
        require(receipt["exit_code"] == 0 and receipt["launch_error"] is None, "first invocation failed")
        require(all(attempt[key] == receipt[key] for key in attempt), "attempt/receipt binding")
        for name, expected in receipt["output_sha256"].items():
            require(sha(directory / name) == expected, "raw receipt mismatch: " + role + "/" + name)
        require({p.name for p in directory.iterdir()} == set(receipt["output_sha256"]) | {"receipt.json"}, "unexpected role artifact")
        require(datetime.fromisoformat(freeze["freeze_time_utc"]) <= datetime.fromisoformat(receipt["started_utc"]) <= datetime.fromisoformat(receipt["finished_utc"]), "freeze/receipt chronology")
        require(sha(ROOT / run[role]["result"]) == run[role]["raw_sha256"], "raw result binding")
    require(datetime.fromisoformat(receipts["candidate"]["finished_utc"]) <= datetime.fromisoformat(receipts["auditor"]["started_utc"]), "candidate/auditor chronology")
    require({p.name for p in (ROOT / "results").iterdir()} == {"candidate", "auditor"}, "unexpected result role")

    fixture, candidate = load("fixture.json"), load(run["candidate"]["result"])
    result_audit = load(run["auditor"]["result"])
    errors = audit.semantic_errors(fixture, candidate, freeze_hash, sha(ROOT / "fixture.json"), sha(ROOT / "candidate.py"), freeze)
    require(not errors, "raw table/gate reconstruction: " + repr(errors))
    controls = audit.corruption_controls(fixture, candidate, freeze_hash, sha(ROOT / "fixture.json"), sha(ROOT / "candidate.py"), freeze)
    require(result_audit["mutation_controls"] == controls, "original corruption results")
    require(len(controls) == 8 and all(c["rejected"] for c in controls), "corruption rejection gate")
    require(result_audit["status"] == "PASS_METHOD_SCOPED" and result_audit["errors"] == [], "original audit classification")
    require(result_audit["primary_selectors_reconstructed"] is True, "original reconstruction flag")
    require(result_audit["freeze_sha256"] == freeze_hash, "audit freeze binding")
    for field, file in (("fixture_sha256", "fixture.json"), ("candidate_sha256", "candidate.py"), ("auditor_sha256", "audit.py")):
        require(result_audit[field] == sha(ROOT / file), "audit source binding: " + field)
    tables = (candidate["graph_audit"]["trial_details"], candidate["controls"]["null_trial_details"], candidate["controls"]["disjoint_trial_details"])
    rows = sum(len(test["outcomes"]) for table in tables for test in table.values())
    require(rows == run["outcome_rows_reconstructed"] == 72, "outcome coverage")

    manifest = {}
    for line in (ROOT / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        expected, name = line.split("  ", 1)
        path = Path(name)
        require(not path.is_absolute() and ".." not in path.parts and name not in manifest, "unsafe/duplicate manifest path")
        require(sha(ROOT / name) == expected, "manifest digest: " + name)
        manifest[name] = expected
    actual_files = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file() and p.name != "SHA256SUMS.txt"}
    require(set(manifest) == actual_files, "manifest coverage")
    print(json.dumps({"status": "PASS_RETAINED_PACKET", "manifest_files": len(manifest), "outcome_rows": rows, "corruptions_rejected": len(controls), "formal_commands_invoked": 0}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
