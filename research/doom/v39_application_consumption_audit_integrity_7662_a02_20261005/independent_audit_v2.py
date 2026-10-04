"""Independent recomputation of #7662 A01 interval labels and saved run."""
import argparse
import hashlib
import json
from pathlib import Path


PAIRED = "adapter_edge_brackets_paired"
INCOMPLETE = "adapter_edge_receipt_incomplete"
SWEEP_MUTATION = {"ordered_index": 4, "unordered_index": 15}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def apply_sweep_mutation(raw):
    """Swap one ordered/unordered reported label in each saved implementation."""
    mutated = json.loads(json.dumps(raw))
    for implementation in ("baseline", "candidate"):
        cases = mutated["interval_sweep"][implementation]["cases"]
        ordered = cases[SWEEP_MUTATION["ordered_index"]]
        unordered = cases[SWEEP_MUTATION["unordered_index"]]
        ordered["expected_ordered"] = False
        ordered["status"] = INCOMPLETE
        ordered["down_edge_interval_ns"] = None
        ordered["up_edge_interval_ns"] = None
        unordered["expected_ordered"] = True
        unordered["status"] = PAIRED
        unordered["down_edge_interval_ns"] = unordered["down"]
        unordered["up_edge_interval_ns"] = unordered["up"]
    return mutated


def audit_raw(raw):
    errors = []
    counts = {}
    sweep = raw.get("interval_sweep")
    if not isinstance(sweep, dict):
        return {"errors": ["interval_sweep_missing"], "counts": counts}
    for implementation in ("baseline", "candidate"):
        rows = sweep.get(implementation, {}).get("cases")
        if not isinstance(rows, list) or len(rows) != 100:
            errors.append(f"{implementation}:case_count")
            continue
        paired_count = 0
        incomplete_count = 0
        for index, row in enumerate(rows):
            down = row.get("down")
            up = row.get("up")
            valid = (
                isinstance(down, list) and len(down) == 2 and
                isinstance(up, list) and len(up) == 2 and
                all(type(value) is int for value in down + up)
            )
            actually_ordered = valid and down[1] < up[0]
            if row.get("expected_ordered") is not actually_ordered:
                errors.append(f"{implementation}:expected_ordered_mismatch:{index}")
            expected_status = PAIRED if actually_ordered else INCOMPLETE
            if row.get("status") != expected_status:
                errors.append(f"{implementation}:status_mismatch:{index}")
            if actually_ordered:
                paired_count += 1
                if row.get("down_edge_interval_ns") != down or row.get("up_edge_interval_ns") != up:
                    errors.append(f"{implementation}:paired_output_mismatch:{index}")
            else:
                incomplete_count += 1
                if row.get("down_edge_interval_ns") is not None or row.get("up_edge_interval_ns") is not None:
                    errors.append(f"{implementation}:unordered_interval_exposed:{index}")
        counts[implementation] = (paired_count, incomplete_count)
        if counts[implementation] != (15, 85):
            errors.append(f"{implementation}:recomputed_count_mismatch:{paired_count}/{incomplete_count}")
    return {"errors": errors, "counts": counts}


def audit(root):
    root = Path(root)
    errors = []
    try:
        freeze_path = root / "FREEZE.json"
        freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
        run = json.loads((root / "RUN.json").read_text(encoding="utf-8"))
        if run.get("freeze_sha256") != sha256(freeze_path):
            errors.append("freeze_hash")
        for name, expected in freeze["source_sha256"].items():
            if sha256(root / name) != expected:
                errors.append(f"source_hash:{name}")
        for name, expected in freeze["frozen_sha256"].items():
            source = root / "frozen" / name
            if not source.is_file() or sha256(source) != expected:
                errors.append(f"frozen_hash:{name}")

        frozen_raw_path = root / "frozen" / "raw" / "A01.json"
        frozen_raw = json.loads(frozen_raw_path.read_text(encoding="utf-8"))
        baseline_raw_path = root / "cases" / "baseline" / "raw" / "A01.json"
        mutated_raw_path = root / "cases" / "label_swap" / "raw" / "A01.json"
        baseline_raw = json.loads(baseline_raw_path.read_text(encoding="utf-8"))
        mutated_raw = json.loads(mutated_raw_path.read_text(encoding="utf-8"))
        if sha256(frozen_raw_path) != freeze["source_raw_sha256"]:
            errors.append("frozen_raw_hash")
        if sha256(baseline_raw_path) != run["baseline"]["raw_sha256"]:
            errors.append("baseline_raw_hash")
        if baseline_raw != frozen_raw:
            errors.append("baseline_raw_changed")
        if mutated_raw != apply_sweep_mutation(frozen_raw):
            errors.append("mutation_shape")

        baseline_recomputed = audit_raw(baseline_raw)
        mutated_recomputed = audit_raw(mutated_raw)
        if baseline_recomputed["errors"]:
            errors.append("baseline_recompute_errors")
        if len(mutated_recomputed["errors"]) != 4:
            errors.append("mutation_not_independently_rejected")
        if run.get("outcome") != "FAIL_AUDITOR_ACCEPTS_LABEL_SWAP":
            errors.append("run_outcome")

        for label in ("baseline", "mutated"):
            record = run[label]
            case_root = root / record["directory"]
            audit_file = case_root / "raw" / "AUDIT.json"
            saved_audit = json.loads(audit_file.read_text(encoding="utf-8"))
            if record["exit_code"] != 0 or saved_audit.get("status") != "PASS_SAVED_RESULT_AUDIT":
                errors.append(f"original_auditor_not_pass:{label}")
            if record.get("audit_status") != saved_audit.get("status"):
                errors.append(f"saved_audit_status_mismatch:{label}")
            if sha256(case_root / "raw" / "A01.json") != record["raw_sha256"]:
                errors.append(f"case_raw_hash:{label}")
            if sha256(case_root / "auditor.stdout") != record["stdout_sha256"]:
                errors.append(f"stdout_hash:{label}")
            if sha256(case_root / "auditor.stderr") != record["stderr_sha256"]:
                errors.append(f"stderr_hash:{label}")
            exit_file = (case_root / "auditor.exit.txt").read_text(encoding="utf-8").strip()
            if exit_file != str(record["exit_code"]):
                errors.append(f"exit_record_mismatch:{label}")
            if saved_audit.get("baseline_false_accept_count") != 4 or saved_audit.get("candidate_false_accept_count") != 0:
                errors.append(f"mutation_result_counts:{label}")
            expected_sweep = {"baseline": {"cases": 100, "paired": 15, "incomplete": 85},
                              "candidate": {"cases": 100, "paired": 15, "incomplete": 85}}
            if saved_audit.get("interval_sweep") != expected_sweep:
                errors.append(f"saved_sweep_summary:{label}")

        result = {
            "experiment_id": freeze["experiment_id"],
            "outcome": "PASS_REPRODUCED_AUDITOR_FALSE_PASS" if not errors else "FAIL_AUDIT_V2",
            "original_auditor_baseline_pass": run["baseline"]["exit_code"] == 0,
            "original_auditor_mutated_pass": run["mutated"]["exit_code"] == 0,
            "baseline_recomputed_errors": baseline_recomputed["errors"],
            "mutated_recomputed_errors": mutated_recomputed["errors"],
            "baseline_recomputed_counts": baseline_recomputed["counts"],
            "mutated_recomputed_counts": mutated_recomputed["counts"],
            "errors": errors,
            "scope": "Saved-result auditor integrity for the #7662 interval sweep only; no source candidate or live allocation rerun.",
        }
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        result = {"experiment_id": "v39-application-consumption-audit-integrity-7662-a02-20261005",
                  "outcome": "FAIL_AUDIT_V2", "errors": [f"audit_input:{type(exc).__name__}:{exc}"],
                  "scope": "Saved-result auditor integrity; no source candidate or live allocation rerun."}
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    result = audit(args.root)
    output = json.dumps(result, indent=2, sort_keys=True) + "\n"
    (args.root / "AUDIT_V2.json").write_text(output, encoding="utf-8")
    print(output, end="")
    raise SystemExit(0 if result["outcome"] == "PASS_REPRODUCED_AUDITOR_FALSE_PASS" else 1)


if __name__ == "__main__":
    main()
