"""Independent raw-only audit for the synthetic sentinel-order probe."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parent
T3 = ROOT / "research/live_control/owner_keyup_keymap_witness_5156_t3_v1"
OUT = PACKAGE / "results/formal-01"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def canonical(row: dict) -> str:
    return json.dumps(row, sort_keys=True, separators=(",", ":"))


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def main() -> int:
    freeze = json.loads((PACKAGE / "FREEZE.json").read_text(encoding="utf-8"))
    candidate = json.loads((OUT / "CANDIDATE.json").read_text(encoding="utf-8"))
    errors = []
    if git("rev-parse", "HEAD") != freeze["main_commit"]:
        errors.append("source HEAD changed from frozen main")
    for relpath, identity in freeze["source_files"].items():
        if git("rev-parse", f"{freeze['main_commit']}:{relpath}") != identity["git_blob"]:
            errors.append(f"source Git blob changed: {relpath}")
        if sha256((ROOT / relpath).read_bytes()) != identity["sha256"]:
            errors.append(f"source bytes changed: {relpath}")

    raw_rows = {
        name: read_jsonl(OUT / name / "raw.jsonl")
        for name in ("control", "nonterminal")
    }
    markers = {}
    bodies = {}
    for name, rows in raw_rows.items():
        selected = [row for row in rows if row.get("event") == "runner_complete"]
        if len(selected) != 1:
            errors.append(f"{name}: expected exactly one completion row")
            continue
        markers[name] = selected[0]
        bodies[name] = [row for row in rows if row is not selected[0]]
        if type(selected[0].get("exit_code")) is not int or selected[0].get("exit_code") != 0:
            errors.append(f"{name}: completion code is not integer zero")
        if selected[0].get("raw_rows") != len(rows):
            errors.append(f"{name}: raw_rows count does not match the serialized input")
    if markers.get("control") != markers.get("nonterminal"):
        errors.append("completion row content differs between cases")
    if bodies.get("control") != bodies.get("nonterminal"):
        errors.append("non-completion rows or their relative order changed")
    if raw_rows["control"][-1] is not markers.get("control"):
        errors.append("positive control does not place completion last")
    if raw_rows["nonterminal"][0] is not markers.get("nonterminal"):
        errors.append("treatment does not place completion first")
    if Counter(map(canonical, raw_rows["control"])) != Counter(map(canonical, raw_rows["nonterminal"])):
        errors.append("the treatment changed the serialized row multiset")

    target_results = {}
    for name in ("control", "nonterminal"):
        case_dir = OUT / name
        raw_bytes = (case_dir / "raw.jsonl").read_bytes()
        stdout = (case_dir / "stdout.bin").read_bytes()
        stderr = (case_dir / "stderr.bin").read_bytes()
        result_bytes = (case_dir / "audit.json").read_bytes()
        result = json.loads(result_bytes)
        printed = json.loads(stdout)
        rc = int((case_dir / "exit_code.txt").read_text(encoding="ascii").strip())
        if stderr:
            errors.append(f"{name}: target stderr is non-empty")
        if printed != result:
            errors.append(f"{name}: stdout and saved target audit disagree")
        if result.get("raw_sha256") != sha256(raw_bytes):
            errors.append(f"{name}: target raw hash is incorrect")
        if result.get("raw_rows") != len(raw_rows[name]):
            errors.append(f"{name}: target row count is incorrect")
        if (rc == 0) != (result.get("status") == "PASS_SYNTHETIC_RAW_ONLY_CLI_BOUNDARY"):
            errors.append(f"{name}: target exit/status relation is inconsistent")
        target_results[name] = {"exit_code": rc, "status": result.get("status"),
                                "raw_sha256": sha256(raw_bytes),
                                "target_result_sha256": sha256(result_bytes)}
    if target_results.get("control", {}).get("exit_code") != 0:
        errors.append("positive control did not pass")
    treatment_rc = target_results.get("nonterminal", {}).get("exit_code")
    if treatment_rc not in (0, 1):
        errors.append("treatment exit is outside the frozen CLI result domain")
    if errors:
        status = "FAIL_INDEPENDENT_AUDIT"
        rc = 1
    elif treatment_rc == 0:
        status = "FINDING_NONTERMINAL_COMPLETION_ACCEPTED"
        rc = 0
    else:
        status = "TERMINALITY_GUARD_ENFORCED"
        rc = 0
    audit = {
        "status": status,
        "errors": errors,
        "source_commit": freeze["main_commit"],
        "control": target_results.get("control"),
        "nonterminal": target_results.get("nonterminal"),
        "independent_checks": [
            "exact source commit, Git blobs, and SHA-256 values",
            "control completion row is final",
            "treatment completion row is first",
            "same completion object in both cases",
            "same non-completion records in the same relative order",
            "identical serialized row multisets",
            "target stdout, saved audit, raw hash, row count, and exit/status agreement",
        ],
        "scope": "synthetic JSONL auditor ordering only; no X11, physical input, application effect, or task result",
    }
    (OUT / "INDEPENDENT_AUDIT.json").write_text(
        json.dumps(audit, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, sort_keys=True))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
