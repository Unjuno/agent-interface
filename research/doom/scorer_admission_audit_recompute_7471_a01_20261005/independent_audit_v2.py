"""Post-hoc, independent validation of the frozen A01 saved run."""
import argparse
import hashlib
import json
from pathlib import Path


EXPECTED_IDS = {
    "same_observation_pre_or_during_recovery",
    "bracketed_bounded_positive",
    "missing_pre_input_baseline",
    "positive_sample_gap_exceeded",
    "missed_poll_period",
}
BASELINE_DECISION = "POST_CANCELLATION_COOCCURRENCE"
BRACKETED_DECISION = "ADMISSION_BRACKETED_PROGRESS"


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def recompute(row):
    """Rebuild the policy decision from samples and timing metadata only."""
    samples = row.get("samples")
    if not isinstance(samples, list) or not all(
        isinstance(s, list) and len(s) == 2 and all(isinstance(x, int) for x in s)
        for s in samples
    ):
        raise ValueError("invalid_samples")
    admitted = row["admitted_ns"]
    first_input = row["first_input_ns"]
    baseline = [s for s in samples if admitted < s[0] < first_input and s[1] == 0]
    if not baseline or row.get("missed_periods") != 0:
        return {"decision": BASELINE_DECISION, "reason": "no_post_admission_pre_input_baseline"}
    b = max(baseline, key=lambda sample: sample[0])
    positives = [s for s in samples if s[0] > b[0] and s[1] == 1]
    if not positives:
        return {"decision": BASELINE_DECISION, "reason": "no_positive_sample_after_baseline"}
    p = min(positives, key=lambda sample: sample[0])
    gap = p[0] - b[0]
    if gap > row["max_gap_ns"]:
        return {"decision": BASELINE_DECISION, "reason": "positive_sample_gap_exceeded"}
    return {"baseline_ns": b[0], "decision": BRACKETED_DECISION,
            "gap_ns": gap, "positive_sample_ns": p[0]}


def _recompute_file(path):
    raw = _read_json(path)
    if raw.get("schema") != "scorer-admission-attribution-t0-raw-v1":
        raise ValueError("raw_schema")
    if raw.get("clock_domain") != "synthetic_single_monotonic_ns" or raw.get("live_game_model_or_input_launched") is not False:
        raise ValueError("raw_scope")
    rows = raw.get("rows")
    if not isinstance(rows, list) or {r.get("id") for r in rows} != EXPECTED_IDS or len(rows) != len(EXPECTED_IDS):
        raise ValueError("row_set")
    by_id = {row["id"]: row for row in rows}
    return raw, {key: recompute(by_id[key]) for key in sorted(by_id)}


def audit(root):
    root = Path(root)
    errors = []
    try:
        freeze_path = root / "FREEZE.json"
        run_path = root / "RUN.json"
        freeze = _read_json(freeze_path)
        run = _read_json(run_path)
        if freeze.get("schema") != "scorer-admission-audit-mutation-freeze-v1":
            errors.append("freeze_schema")
        if freeze.get("source_commit") != "decefbd53240cdac21633e0d3e66c7e3bec76722":
            errors.append("source_commit")
        if run.get("freeze_sha256") != _sha(freeze_path):
            errors.append("freeze_hash")
        for name, meta in freeze.get("frozen_sources", {}).items():
            path = root / "frozen" / name
            if not path.is_file() or _sha(path) != meta.get("sha256"):
                errors.append(f"frozen_source:{name}")
        if _sha(root / "experiment.py") != freeze.get("runner_sha256"):
            errors.append("runner_hash")
        if _sha(root / "independent_audit.py") != freeze.get("independent_auditor_sha256"):
            errors.append("first_auditor_hash")

        base_path = root / "cases" / "baseline" / "raw.json"
        mutated_path = root / "cases" / "positive_sample_removed" / "raw.json"
        baseline_raw, baseline = _recompute_file(base_path)
        mutated_raw, mutated = _recompute_file(mutated_path)
        if _sha(base_path) != freeze["frozen_sources"]["raw.json"]["sha256"]:
            errors.append("baseline_raw_hash")
        mutation = freeze["mutation"]
        target = next(row for row in mutated_raw["rows"] if row.get("id") == mutation["row_id"])
        baseline_target = next(row for row in baseline_raw["rows"] if row.get("id") == mutation["row_id"])
        expected_samples = [list(sample) for sample in baseline_target["samples"]]
        index = mutation["sample_index"]
        if expected_samples[index][1] != mutation["from"]:
            errors.append("mutation_source_value")
        expected_samples[index][1] = mutation["to"]
        comparison = dict(target)
        comparison["samples"] = baseline_target["samples"]
        if comparison != baseline_target or target["samples"] != expected_samples:
            errors.append("mutation_shape")

        base_record = run["baseline"]
        mutated_record = run["mutated"]
        if not base_record["audit"]["audit_pass"] or base_record["audit"]["exit_code"] != 0:
            errors.append("baseline_old_auditor")
        if not mutated_record["audit"]["audit_pass"] or mutated_record["audit"]["exit_code"] != 0:
            errors.append("mutated_old_auditor")
        if base_record["audit"]["stdout_sha256"] != mutated_record["audit"]["stdout_sha256"]:
            errors.append("old_auditor_output_changed")
        if _sha(base_path) != base_record["audit"]["raw_sha256"] or _sha(mutated_path) != mutated_record["audit"]["raw_sha256"]:
            errors.append("mutated_raw_hash")

        baseline_decision = baseline["bracketed_bounded_positive"]["decision"]
        mutated_decision = mutated["bracketed_bounded_positive"]["decision"]
        retained = target["observed"]
        if baseline_decision != BRACKETED_DECISION:
            errors.append("baseline_recompute:bracketed_case")
        if retained != baseline_target["observed"]:
            errors.append("retained_observed_changed")
        if retained.get("decision") != BRACKETED_DECISION or mutated_decision == retained.get("decision"):
            errors.append("mutated_recompute_disagrees")
        if run.get("outcome") != "FAIL_AUDITOR_ACCEPTS_RAW_MUTATION":
            errors.append("run_outcome")
        result = {
            "experiment_id": freeze.get("experiment_id"),
            "outcome": "FAIL_AUDIT_V2" if errors else "PASS_REPRODUCED_AUDITOR_FALSE_PASS",
            "baseline_recomputed": baseline_decision,
            "mutated_recomputed": mutated_decision,
            "mutated_retained": retained.get("decision"),
            "old_auditor_baseline_pass": base_record["audit"]["audit_pass"],
            "old_auditor_mutated_pass": mutated_record["audit"]["audit_pass"],
            "errors": errors,
            "scope": "Post-hoc independent audit of preserved synthetic raw mutation; experiment not rerun.",
        }
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        result = {"experiment_id": "scorer-admission-audit-recompute-7471-a01",
                  "outcome": "FAIL_AUDIT_V2", "errors": [f"audit_input:{type(exc).__name__}:{exc}"],
                  "scope": "Post-hoc independent audit of preserved synthetic raw mutation; experiment not rerun."}
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    result = audit(args.root)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    (args.root / "AUDIT_V2.json").write_text(text, encoding="utf-8")
    print(text, end="")
    raise SystemExit(0 if result["outcome"] == "PASS_REPRODUCED_AUDITOR_FALSE_PASS" else 1)


if __name__ == "__main__":
    main()
