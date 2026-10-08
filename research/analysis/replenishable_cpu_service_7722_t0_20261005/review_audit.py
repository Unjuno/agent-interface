"""Supplemental read-only policy reconstruction for the retained #7722 T0 raw."""

from __future__ import annotations

import importlib.util
import copy
import hashlib
import json
import argparse
from collections import deque
from pathlib import Path


ROOT = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("frozen_t0_auditor", ROOT / "auditor.py")
_frozen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_frozen)


def _dispatch_errors(run: dict, cfg: dict, case: dict) -> list[str]:
    """Rebuild FIFO queues and verify every emitted service event's dispatch choice."""
    jobs = _frozen.expected_jobs(cfg, case)
    pending = {jid: spec["required_ticks"] for jid, spec in jobs.items()}
    control, best_effort = deque(), deque()
    arrivals = sorted(jobs.items(), key=lambda item: item[1]["release_tick"])
    arrival_index = 0
    rejected = []
    errors = []

    if run.get("policy") not in _frozen.POLICIES:
        return ["dispatch_unknown_policy"]

    for event in run.get("events", []):
        if not isinstance(event, dict) or type(event.get("tick")) is not int:
            continue
        tick = event["tick"]
        while arrival_index < len(arrivals) and arrivals[arrival_index][1]["release_tick"] <= tick:
            job_id, spec = arrivals[arrival_index]
            arrival_index += 1
            if spec["job_class"] == "control":
                control.append(job_id)
            elif run["policy"] == "shared_backpressure" and len(best_effort) >= cfg["backpressure_queue_jobs"]:
                rejected.append(job_id)
            else:
                best_effort.append(job_id)

        selected = control[0] if control else (best_effort[0] if best_effort else None)
        if selected is None or event.get("job_id") != selected:
            errors.append("dispatch_order")
            continue
        if pending[selected] <= 0:
            errors.append("dispatch_after_completion")
            continue
        pending[selected] -= 1
        if pending[selected] == 0:
            (control if jobs[selected]["job_class"] == "control" else best_effort).popleft()

    recorded = run.get("rejected_best_effort")
    if recorded != rejected:
        errors.append("invalid_backpressure_admission")
    return errors


def check_run(run: dict, cfg: dict, case: dict) -> list[str]:
    """Run the frozen structural checks plus the missing dispatch/admission replay."""
    return _frozen.check_run(run, cfg, case) + _dispatch_errors(run, cfg, case)


def mutation_rejected(run: dict, cfg: dict, case: dict) -> bool:
    """A mutation is rejected only when the checker returns at least one error."""
    return bool(check_run(run, cfg, case))


def _raw_errors(raw: dict, cfg: dict) -> list[str]:
    errors = []
    if raw.get("schema") != "cpu-control-7722-raw-v1":
        errors.append("raw_schema_mismatch")
    if raw.get("allocation_id") != cfg.get("allocation_id"):
        errors.append("allocation_mismatch")
    budget_keys = _frozen.BUDGET_KEYS
    if raw.get("declared_budgets") != {key: cfg[key] for key in budget_keys}:
        errors.append("budget_or_deadline_declaration_mismatch")
    cases = {case["case_id"]: case for case in cfg["cases"]}
    expected = {(case["case_id"], policy) for case in cfg["cases"] for policy in _frozen.POLICIES}
    seen = set()
    runs = raw.get("runs")
    if not isinstance(runs, list):
        return errors + ["runs_missing"]
    for run in runs:
        if not isinstance(run, dict):
            errors.append("malformed_run")
            continue
        key = (run.get("case_id"), run.get("policy"))
        if key in seen:
            errors.append("duplicate_run")
        seen.add(key)
        case = cases.get(key[0])
        if case is None:
            errors.append("unknown_case")
            continue
        errors.extend(f"{key[0]}/{key[1]}:{error}" for error in check_run(run, cfg, case))
    if seen != expected:
        errors.append("run_matrix_incomplete")
    return errors


def _swap_control_and_best_effort(run: dict, case_id: str) -> None:
    first = next(event for event in run["events"] if event["tick"] == 1000)
    second = next(event for event in run["events"] if event["tick"] == 1004)
    first["job_id"], second["job_id"] = second["job_id"], first["job_id"]
    first["job_class"], second["job_class"] = second["job_class"], first["job_class"]
    rows = {row["job_id"]: row for row in run["jobs"]}
    rows[f"{case_id}-c0"]["finish_tick"] = 1005
    rows[f"{case_id}-b1-0"]["finish_tick"] = 1009


def audit_retained_raw(raw: dict, cfg: dict) -> dict:
    cases = {case["case_id"]: case for case in cfg["cases"]}
    errors = _raw_errors(raw, cfg)
    for field, name in (
        ("cases_sha256", "cases.json"),
        ("candidate_sha256", "candidate.py"),
        ("protocol_sha256", "PROTOCOL.md"),
        ("freeze_sha256", "freeze.json"),
    ):
        actual = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        if raw.get(field) != actual:
            errors.append(f"frozen_identity_mismatch:{field}")

    dispatch = copy.deepcopy(next(
        run for run in raw["runs"]
        if run["case_id"] == "sched_seed_7722" and run["policy"] == "shared_priority"
    ))
    _swap_control_and_best_effort(dispatch, "sched_seed_7722")
    backpressure = copy.deepcopy(next(
        run for run in raw["runs"]
        if run["case_id"] == "sched_seed_7722" and run["policy"] == "shared_backpressure"
    ))
    rejected_id = "sched_seed_7722-b9-13"
    next(row for row in backpressure["jobs"] if row["job_id"] == rejected_id)["status"] = "rejected_backpressure"
    backpressure["rejected_best_effort"].append(rejected_id)

    def mutate_raw(mutator):
        changed = copy.deepcopy(raw)
        mutator(changed)
        return _raw_errors(changed, cfg)

    def change_run(policy, mutator):
        changed = copy.deepcopy(raw)
        run = next(r for r in changed["runs"] if r["case_id"] == "sched_seed_7722" and r["policy"] == policy)
        mutator(run)
        return _raw_errors(changed, cfg)

    def lose_obligation(run):
        run["jobs"] = [row for row in run["jobs"] if row["job_class"] != "control"]

    def double_charge(run):
        run["events"].append(copy.deepcopy(run["events"][0]))

    def uncharged_service(run):
        run["events"][0]["channels"] = []

    def false_completion(run):
        run["jobs"][0]["finish_tick"] = -1

    controls = {
        "budget_mutation": mutate_raw(lambda data: data["declared_budgets"].update(total_budget_ticks=99)),
        "deadline_mutation": mutate_raw(lambda data: data["declared_budgets"].update(control_deadline_ticks=99)),
        "lost_obligation": change_run("shared_priority", lose_obligation),
        "early_replenishment_or_double_charge": change_run("shared_priority", double_charge),
        "uncharged_service": change_run("shared_priority", uncharged_service),
        "false_completion": change_run("shared_priority", false_completion),
        "control_priority_fifo_violation": check_run(dispatch, cfg, cases["sched_seed_7722"]),
        "backpressure_rejection_before_capacity": check_run(backpressure, cfg, cases["sched_seed_7722"]),
    }
    mutation_controls = {
        name: {
            "rejected": bool(found),
            "error_count": len(found),
            "error_examples": found[:5],
        }
        for name, found in controls.items()
    }
    baseline = next(
        run for run in raw["runs"]
        if run["case_id"] == "sched_seed_7722" and run["policy"] == "shared_priority"
    )
    unchanged_accepted = not mutation_rejected(baseline, cfg, cases["sched_seed_7722"])

    accepted = not errors and all(result["rejected"] for result in mutation_controls.values()) and unchanged_accepted
    return {
        "classification": "SUPPLEMENTAL_READ_ONLY_AUDIT; does not replace or upgrade the frozen formal allocation",
        "status": "PASS_SUPPLEMENTAL_RAW_RECONSTRUCTION" if accepted else "FAIL_SUPPLEMENTAL_RAW_RECONSTRUCTION",
        "raw_run_count": len(raw.get("runs", [])),
        "raw_reconstruction_errors": errors,
        "mutation_controls": mutation_controls,
        "unchanged_trace_control": {"accepted": unchanged_accepted},
        "candidate_invocations": 0,
        "frozen_auditor_invocations": 0,
        "retries": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    package = Path(__file__).resolve().parent
    raw_path = package / "output/candidate/candidate.raw.json"
    cfg_path = package / "cases.json"
    result = audit_retained_raw(json.loads(raw_path.read_text()), json.loads(cfg_path.read_text()))
    result["sha256"] = {
        "raw": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
        "cases": hashlib.sha256(cfg_path.read_bytes()).hexdigest(),
        "frozen_candidate": hashlib.sha256((package / "candidate.py").read_bytes()).hexdigest(),
        "frozen_auditor": hashlib.sha256((package / "auditor.py").read_bytes()).hexdigest(),
        "supplemental_auditor": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "raw_run_count": result["raw_run_count"], "output": str(output)}))
    return 0 if result["status"] == "PASS_SUPPLEMENTAL_RAW_RECONSTRUCTION" else 1


if __name__ == "__main__":
    raise SystemExit(main())
