"""Independent raw-only claim-boundary auditor; does not import candidate.py."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def audit_raw(screen, confirmatory, oracle, result):
    errors = []
    expected_survivors = []
    expected_screened = []
    expected_screen_rows = []
    for arm, row in sorted(screen["arms"].items()):
        survived = arm == screen["baseline"] or (
            row["correct"] >= screen["selection"]["minimum_correct"]
            and not (screen["selection"]["exclude_hard_safety_violation"] and row["hard_safety_violation"])
        )
        if arm != screen["baseline"]:
            (expected_survivors if survived else expected_screened).append(arm)
        expected_screen_rows.append((f"screen:{arm}:0", arm, survived, row))
    if result.get("survivors") != expected_survivors or result.get("screened_out") != expected_screened:
        errors.append("screen partition mismatch")

    screen_rows = result.get("screen_attempts", [])
    screen_ids = [row.get("attempt_id") for row in screen_rows]
    if len(screen_ids) != len(set(screen_ids)) or set(screen_ids) != {item[0] for item in expected_screen_rows}:
        errors.append("screen attempt inventory mismatch")
    for attempt_id, arm, survived, expected in expected_screen_rows:
        rows = [row for row in screen_rows if row.get("attempt_id") == attempt_id]
        if len(rows) != 1:
            continue
        row = rows[0]
        for key, value in (("arm", arm), ("survived", survived), ("correct", expected["correct"]),
                           ("opportunities", expected["opportunities"]),
                           ("hard_safety_violation", expected["hard_safety_violation"])):
            if row.get(key) != value:
                errors.append(f"screen row mismatch: {attempt_id}:{key}")

    expected_confirm = {}
    baseline = confirmatory["baseline"]
    base_by_variant = {item["variant"]: item for item in confirmatory["arms"][baseline]}
    for arm in expected_survivors:
        for observed in confirmatory["arms"][arm]:
            variant = observed["variant"]
            attempt_id = f"confirm:{screen['family_id']}:{arm}:{variant}"
            expected_confirm[attempt_id] = (arm, variant, observed, base_by_variant[variant])
    actual = result.get("confirm_attempts", [])
    actual_ids = [row.get("attempt_id") for row in actual]
    if len(actual_ids) != len(set(actual_ids)) or set(actual_ids) != set(expected_confirm):
        errors.append("confirm attempt inventory mismatch")
    for attempt_id, (arm, variant, candidate, base) in expected_confirm.items():
        rows = [row for row in actual if row.get("attempt_id") == attempt_id]
        if len(rows) != 1:
            continue
        row = rows[0]
        expected_fields = {
            "phase": "confirm", "family_id": screen["family_id"], "arm": arm, "baseline": baseline,
            "variant": variant, "candidate_latency_ms": candidate["latency_ms"],
            "baseline_latency_ms": base["latency_ms"],
            "hard_safety_violation": candidate["hard_safety_violation"],
        }
        for key, value in expected_fields.items():
            if row.get(key) != value:
                errors.append(f"confirmation mismatch: {attempt_id}:{key}")

    if confirmatory["family_id"] != screen["family_id"] or confirmatory["variants"] != oracle["variants"]:
        errors.append("sealed family/variant identity mismatch")
    family = result.get("family", {})
    family_members = [arm for arm in expected_survivors if arm != baseline]
    if (family.get("family_id") != screen["family_id"] or family.get("members") != family_members
            or family.get("rule") != screen["survivor_family_rule"]
            or family.get("claim") != "WITHHELD_NO_FAMILYWISE_INFERENCE"):
        errors.append("unsupported or altered family claim")
    if result.get("global_best_claim") != "NOT_ESTABLISHED_SCREENED_ARM_NOT_CONFIRMED":
        errors.append("unsupported global-best claim")
    if result.get("promotion") != "WITHHELD":
        errors.append("promotion was not withheld")

    per_arm = result.get("per_arm", {})
    for arm in expected_survivors:
        rows = [item for item in confirmatory["arms"][arm]]
        deltas = [base_by_variant[item["variant"]]["latency_ms"] - item["latency_ms"] for item in rows]
        hard_fail = any(item["hard_safety_violation"] for item in rows)
        expected_disposition = "WITHHOLD_HARD_SAFETY_FAILURE" if hard_fail else "DESCRIPTIVE_ONLY_NO_PROMOTION"
        summary = per_arm.get(arm, {})
        if summary.get("finite_descriptive_deltas_ms") != deltas:
            errors.append(f"descriptive deltas mismatch: {arm}")
        if summary.get("mean_descriptive_delta_ms") != sum(deltas) / len(deltas):
            errors.append(f"descriptive mean mismatch: {arm}")
        if summary.get("disposition") != expected_disposition:
            errors.append(f"safety disposition mismatch: {arm}")

    # Oracle-only negative control: D was excluded, yet it is the lowest-latency
    # arm among all hard-safety-feasible arms on the sealed finite table.
    safe_arms = [arm for arm, failed in oracle["hard_safety_violation"].items() if not failed]
    means = {arm: sum(oracle["arms"][arm]) / len(oracle["arms"][arm]) for arm in safe_arms}
    oracle_best = min(means, key=means.get)
    if oracle_best != "D" or oracle_best not in expected_screened:
        errors.append("false-elimination oracle control not established")
    if oracle_best in result.get("survivors", []):
        errors.append("oracle-best screened arm unexpectedly survived")
    # E is the fastest survivor but has a frozen hard-safety violation.
    survivor_safe = [arm for arm in expected_survivors if arm != baseline and not any(
        row["hard_safety_violation"] for row in confirmatory["arms"][arm]
    )]
    safe_survivor_means = {
        arm: sum(row["latency_ms"] for row in confirmatory["arms"][arm]) / len(confirmatory["arms"][arm])
        for arm in survivor_safe
    }
    e_mean = sum(row["latency_ms"] for row in confirmatory["arms"]["E"]) / len(confirmatory["arms"]["E"])
    if e_mean >= min(safe_survivor_means.values()) or result.get("per_arm", {}).get("E", {}).get("disposition") != "WITHHOLD_HARD_SAFETY_FAILURE":
        errors.append("fast unsafe survivor control not established")
    return errors


def audit_path(root=ROOT):
    freeze = json.loads((root / "FREEZE.json").read_text(encoding="utf-8"))
    source_errors = []
    for name, expected in freeze["source_sha256"].items():
        try:
            actual = sha((root / name).read_bytes())
        except OSError:
            actual = None
        if actual != expected:
            source_errors.append(f"source digest mismatch: {name}")
    screen_raw = (root / "screen.json").read_bytes()
    confirm_raw = (root / "confirmatory.json").read_bytes()
    oracle_raw = (root / "sealed_oracle.json").read_bytes()
    candidate_raw = (root / "CANDIDATE.json").read_bytes()
    stdout = (root / "STDOUT.bin").read_bytes()
    stderr = (root / "STDERR.bin").read_bytes()
    execution = json.loads((root / "EXECUTION.json").read_text(encoding="utf-8"))
    run_errors = audit_raw(json.loads(screen_raw), json.loads(confirm_raw), json.loads(oracle_raw),
                           json.loads(candidate_raw))
    if candidate_raw != stdout:
        run_errors.append("candidate/stdout byte mismatch")
    if stderr:
        run_errors.append("unexpected candidate stderr")
    if execution.get("exit_code") != 0 or execution.get("candidate_invocations") != 1:
        run_errors.append("candidate execution receipt invalid")
    if execution.get("candidate_sha256") != sha(candidate_raw) or execution.get("stdout_sha256") != sha(stdout):
        run_errors.append("candidate/stdout SHA mismatch")
    if execution.get("stderr_sha256") != sha(stderr):
        run_errors.append("stderr SHA mismatch")
    if freeze.get("base_main") != "24f6b7d5f9395105807f981d48db212e6692a6f4":
        source_errors.append("base main SHA mismatch")
    all_errors = source_errors + run_errors
    return {
        "auditor": "audit.py separate raw-only implementation",
        "result": "PASS_CLAIM_BOUNDARY_SCOPED" if not all_errors else "FAIL_AUDIT_OR_CLAIM_BOUNDARY",
        "candidate_sha256": sha(candidate_raw),
        "source_hashes_match": not source_errors,
        "screen_attempts": len(json.loads(candidate_raw).get("screen_attempts", [])),
        "confirm_attempts": len(json.loads(candidate_raw).get("confirm_attempts", [])),
        "errors": all_errors,
        "oracle_best_safe_arm": "D",
        "family_claim": json.loads(candidate_raw).get("family", {}).get("claim"),
        "scope": "analyst-authored finite construction only; no empirical/runtime/user/performance inference",
    }


def main():
    result = audit_path()
    raw = (json.dumps(result, sort_keys=True, indent=2) + "\n").encode("utf-8")
    (ROOT / "AUDIT.json").write_bytes(raw)
    (ROOT / "AUDIT_STDOUT.bin").write_bytes(raw)
    (ROOT / "AUDIT_STDERR.bin").write_bytes(b"")
    (ROOT / "AUDIT_EXECUTION.json").write_text(json.dumps({
        "command": "python -B audit.py", "exit_code": 0 if not result["errors"] else 1,
        "stdout_sha256": sha(raw), "stderr_sha256": sha(b""),
        "audit_sha256": sha(raw), "candidate_invocations": 0,
    }, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(raw.decode("utf-8"), end="")
    return 0 if not result["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
