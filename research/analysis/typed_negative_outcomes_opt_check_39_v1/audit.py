"""Independent stdlib-only raw audit for Issue #4990."""
import hashlib
import itertools
import json
import sys
from pathlib import Path

EXPECTED_DIGEST = "c9e0871ce3272c99f91db2596fd02ffd3ba941ca10bf8a21662a45a5c302d68a"
EXPECTED_COUNTS = {"SUCCEEDED":3,"BLOCKED":3,"AUTHORITY_REQUIRED":96,"TARGET_NOT_FOUND":6,"CAPABILITY_UNSUPPORTED":24,"CONFLICT":48,"IMPOSSIBLE_UNDER_CONSTRAINTS":12,"FAILED_UNKNOWN":192}
MODES = ("normal", "opt_flag", "env_opt")
CONTROL_NAMES = ("stale_success", "authority_success", "retry_nonblocked", "budget_monotonicity", "row_count", "outcome_count", "oracle")


def check(condition, label, errors):
    if not condition:
        errors.append(label)


def independent_replay():
    """Reconstruct the frozen finite table without importing candidate code."""
    fields = ("fresh", "authority", "conflict", "capability", "impossible", "target", "blocked")
    rows = []
    counts = {key: 0 for key in EXPECTED_COUNTS}
    for bits in itertools.product((False, True), repeat=len(fields)):
        e = dict(zip(fields, bits))
        for budget in range(3):
            if e["fresh"] is not True:
                expected = ("FAILED_UNKNOWN", False, "NEW_OBSERVATION")
            elif e["authority"] is not True:
                expected = ("AUTHORITY_REQUIRED", False, "FOCUS_OR_LEASE")
            elif e["conflict"]:
                expected = ("CONFLICT", False, "FRESH_RECONCILIATION")
            elif e["capability"] is not True:
                expected = ("CAPABILITY_UNSUPPORTED", False, "ALTERNATIVE_CAPABILITY")
            elif e["impossible"]:
                expected = ("IMPOSSIBLE_UNDER_CONSTRAINTS", False, "PLANNER_RECONSIDERATION")
            elif e["target"] is not True:
                expected = ("TARGET_NOT_FOUND", False, "DIFFERENT_TARGET_OR_OBSERVATION")
            elif e["blocked"]:
                expected = ("BLOCKED", budget != 0, "UNBLOCK_OR_WAIT")
            else:
                expected = ("SUCCEEDED", False, "NONE")
            result = {"outcome": expected[0], "retryable": expected[1],
                      "required_change": expected[2], "authority": False}
            counts[result["outcome"]] += 1
            rows.append({"evidence": e, "budget": budget, "result": result})
    encoded = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return len(rows), counts, hashlib.sha256(encoded).hexdigest()


def audit(root):
    errors = []
    rows, counts, replay_digest = independent_replay()
    check(rows == 384, "oracle_row_count", errors)
    check(counts == EXPECTED_COUNTS, "oracle_counts", errors)
    check(replay_digest == EXPECTED_DIGEST, "oracle_digest", errors)
    for mode in MODES:
        raw = (root / (mode + ".stdout")).read_bytes()
        receipt = json.loads(raw)
        check(receipt.get("decision") == "PASS_OPTIMIZATION_RESILIENT_CONTRACT_SCOPED", mode + ":decision", errors)
        check(receipt.get("rows") == rows, mode + ":rows", errors)
        check(receipt.get("counts") == counts, mode + ":counts", errors)
        check(receipt.get("digest") == replay_digest, mode + ":digest", errors)
        check(receipt.get("authority_grants") == 0, mode + ":authority", errors)
        expected_opt = {"normal": 0, "opt_flag": 1, "env_opt": 1}[mode]
        check(receipt.get("optimize") == expected_opt, mode + ":optimization_mode", errors)
        check((root / (mode + ".exit")).read_text(encoding="ascii").strip() == "0", mode + ":exit", errors)
        check((root / (mode + ".stderr")).read_bytes() == b"", mode + ":stderr", errors)
        check((root / (mode + "-tests.exit")).read_text(encoding="ascii").strip() == "0", mode + ":tests_exit", errors)
        check(b"Ran 5 tests" in (root / (mode + "-tests.stderr")).read_bytes(), mode + ":tests_ran", errors)
        check((root / (mode + "-tests.stdout")).read_bytes() == b"", mode + ":tests_stdout", errors)
    for mode in MODES:
        for control in CONTROL_NAMES:
            stem = mode + "-" + control
            receipt = json.loads((root / (stem + ".control")).read_text(encoding="utf-8"))
            check(receipt.get("passed") is False, stem + ":must_reject", errors)
            check(receipt.get("pass_marker_seen") is False, stem + ":pass_marker", errors)
            check(receipt.get("exit") != 0, stem + ":exit_nonzero", errors)
            check(isinstance(receipt.get("error"), str) and bool(receipt["error"]), stem + ":error", errors)
            check((root / (stem + ".exit")).read_text(encoding="ascii").strip() != "0", stem + ":raw_exit", errors)
            out = (root / (stem + ".stdout")).read_bytes()
            check(b"PASS_OPTIMIZATION_RESILIENT_CONTRACT_SCOPED" not in out, stem + ":raw_pass_marker", errors)
    report = {"schema": "issue-4990-raw-audit-v1", "errors": errors, "pass": not errors,
              "replayed_rows": rows, "replayed_counts": counts, "replayed_digest": replay_digest,
              "modes": list(MODES), "corruption_controls_per_mode": len(CONTROL_NAMES)}
    return report


if __name__ == "__main__":
    report = audit(Path(sys.argv[1]))
    print(json.dumps(report, sort_keys=True))
    if not report["pass"]:
        raise SystemExit(1)
