"""Independent, provenance-bound recount of integrated-efficiency-live-01."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path


EVIDENCE = Path("research/live_control/results/integrated-efficiency-live-01")
V1_AUDIT = Path("research/live_control/integrated_efficiency_live_audit_20260928/FREEZE.json")
ARMS = ("plain", "ephemeral", "persistent")
USAGE = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens",
         "output_tokens", "reasoning_output_tokens")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def validate_path_inventory(expected: set[str], actual: list[str], label: str) -> None:
    require(len(actual) == len(set(actual)), f"duplicate {label} path")
    actual_set = set(actual)
    require(actual_set == expected,
            f"{label} path inventory mismatch: missing={sorted(expected-actual_set)}; "
            f"extra={sorted(actual_set-expected)}")


def validate_sha256(data: bytes, expected: str, name: str) -> None:
    require(hashlib.sha256(data).hexdigest() == expected, f"input bytes differ from manifest: {name}")


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def is_commit_ancestor(root: Path, base: str, head: str) -> bool:
    return subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", base, head],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                          check=False).returncode == 0


def expected_input_paths(root: Path) -> set[str]:
    paths = {V1_AUDIT.as_posix()}
    paths.update((EVIDENCE / name).as_posix() for name in
                 ("preregistration.json", "trace.json", "report.json", "audit.json"))
    for arm in ARMS:
        paths.add((EVIDENCE / "preflight" / arm / "gate" / "gate-report.json").as_posix())
        paths.add((EVIDENCE / "arms" / arm / "task-details.json").as_posix())
        paths.add((EVIDENCE / "arms" / arm / "runtime" / "submission-history.jsonl").as_posix())
        model_root = root / EVIDENCE / "model-calls" / arm
        paths.update(p.relative_to(root).as_posix() for p in model_root.rglob("result.json"))
    return paths


def validate_manifest(root: Path, freeze: dict, manifest: dict) -> dict[str, dict]:
    base = freeze["input_main_commit"]
    require(manifest["schema"] == "integrated-efficiency-recount-v2-input-manifest-v1",
            "input manifest schema mismatch")
    require(manifest["input_main_commit"] == base, "manifest/base commit mismatch")
    require(sha256(root / freeze["input_manifest_path"]) == freeze["input_manifest_sha256"],
            "input manifest digest mismatch")
    require(git(root, "rev-parse", "--verify", f"{base}^{{commit}}") == base,
            "pinned input commit unavailable")
    head = git(root, "rev-parse", "HEAD")
    require(is_commit_ancestor(root, base, head),
            "checkout does not descend from frozen input commit")

    entries = manifest["files"]
    by_path = {entry["path"]: entry for entry in entries}
    require(len(by_path) == len(entries), "duplicate manifest path")
    expected = expected_input_paths(root)
    validate_path_inventory(expected, list(by_path), "input")
    for name, entry in by_path.items():
        path = root / name
        require(path.is_file(), f"missing frozen input: {name}")
        validate_sha256(path.read_bytes(), entry["sha256"], name)
        blob = git(root, "rev-parse", f"{base}:{name}")
        require(blob == entry["git_blob"], f"Git blob differs from frozen input tree: {name}")

    v1 = read_json(root / V1_AUDIT)
    original_hashes = {
        "preregistration.json": v1["preregistration_sha256"],
        "trace.json": v1["trace_sha256"],
        "report.json": v1["report_sha256"],
        "audit.json": v1["existing_audit_sha256"],
    }
    for name, expected_sha in original_hashes.items():
        require(by_path[(EVIDENCE / name).as_posix()]["sha256"] == expected_sha,
                f"historical v1 freeze mismatch: {name}")
    return by_path


def index_raw_calls(paths: list[Path]) -> dict[str, dict]:
    indexed = {}
    for path in sorted(paths):
        data = read_json(path)
        call_id = data.get("call_id")
        require(isinstance(call_id, str) and bool(call_id), f"raw result missing call_id: {path}")
        require(call_id not in indexed, f"duplicate raw result call_id: {call_id}")
        require(isinstance(data.get("usage"), dict), f"raw result missing usage: {path}")
        indexed[call_id] = data["usage"]
    return indexed


def validate_history(history: list[dict], details: list[dict], arm: str) -> int:
    require(len(history) == 6 and len(details) == 6, f"submission population mismatch: {arm}")
    for index, (row, detail) in enumerate(zip(history, details), 1):
        validate_submission_row(row, detail, arm, f"task-{index}")
    return len(history)


def validate_submission_row(row: dict, detail: dict, arm: str, task_id: str) -> None:
    detail_trace = detail["trace"]
    records = detail["submission_records"]
    require(detail_trace["arm"] == arm and detail_trace["task_id"] == task_id,
            f"task-detail identity mismatch: {arm}/{task_id}")
    require(len(records) == 1, f"task-detail submission count mismatch: {arm}/{task_id}")
    oracle = records[0]
    expected = oracle.get("expected_token")
    values = oracle.get("submitted_values")
    require(isinstance(expected, str) and values == [expected],
            f"task-detail raw effect is not exact: {arm}/{task_id}")
    require(row.get("task_id") == task_id and row.get("task_id") == detail_trace["task_id"],
            f"history task identity mismatch: {arm}/{task_id}")
    require(row.get("expected_token") == expected, f"history oracle mismatch: {arm}/{task_id}")
    require(row.get("submitted_values") == values,
            f"history raw submitted values mismatch: {arm}/{task_id}")
    computed_exact = row.get("submitted_values") == [row.get("expected_token")]
    require(row.get("exact") is computed_exact and computed_exact,
            f"history exact flag/value disagreement: {arm}/{task_id}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("freeze", type=Path)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    root, out = args.root.resolve(), args.out.resolve()
    require(not out.exists(), f"output path already exists: {out}")
    freeze = read_json(args.freeze)
    manifest = read_json(args.manifest)
    by_path = validate_manifest(root, freeze, manifest)

    files = {name: root / EVIDENCE / name for name in
             ("preregistration.json", "trace.json", "report.json", "audit.json")}
    prereg, trace, report, stored = (read_json(files[n]) for n in
                                     ("preregistration.json", "trace.json", "report.json", "audit.json"))
    require(prereg["study"] == "integrated-efficiency-live-01", "study identity mismatch")

    result_paths = [
        p for arm in ARMS for p in (root / EVIDENCE / "model-calls" / arm).rglob("result.json")
    ]
    validate_path_inventory({p.relative_to(root).as_posix() for p in result_paths},
                            [p.relative_to(root).as_posix() for p in result_paths], "raw result")
    require(len(result_paths) == 14, f"expected 14 raw result paths, got {len(result_paths)}")
    raw_calls = index_raw_calls(result_paths)
    require(len(raw_calls) == len(result_paths), "raw paths were overwritten during indexing")

    class_totals = {arm: {field: 0 for field in USAGE} for arm in ARMS}
    trace_calls = {}
    preflight_by_arm = {}
    task_counts, submission_counts = {}, {}
    cumulative_input, cumulative_generations = {}, {}
    details_by_arm = {}
    histories_by_arm = {}
    for arm in ARMS:
        gate_path = root / EVIDENCE / "preflight" / arm / "gate" / "gate-report.json"
        gate = read_json(gate_path)
        require(gate["accepted"] is True and gate["model_calls"] == 1,
                f"preflight gate invalid: {arm}")
        pf_result = gate["results"][0]["result"]
        require(pf_result["cache_hit"] is False and pf_result["model_call_performed"] is True,
                f"preflight not fresh: {arm}")
        preflight_by_arm[arm] = pf_result["usage"]
        require(trace["preflight_calls"][arm]["usage"] == pf_result["usage"],
                f"preflight usage mismatch: {arm}")

        rows = trace["arms"][arm]
        details = read_json(root / EVIDENCE / "arms" / arm / "task-details.json")
        history_path = root / EVIDENCE / "arms" / arm / "runtime" / "submission-history.jsonl"
        history = [json.loads(line) for line in history_path.read_text(encoding="utf-8").splitlines()
                   if line.strip()]
        require(len(rows) == 6 and len(details) == 6, f"task count mismatch: {arm}")
        for task, detail in zip(rows, details):
            require(task == detail["trace"], f"trace/task-detail row mismatch: {arm}/{task['task_id']}")
        task_counts[arm] = len(rows)
        submission_counts[arm] = validate_history(history, details, arm)
        details_by_arm[arm] = details
        histories_by_arm[arm] = history

        cumulative_input[arm] = []
        cumulative_generations[arm] = []
        used_input = 0
        generations = 1
        for index, task in enumerate(rows, 1):
            require(task["task_id"] == f"task-{index}", f"task order mismatch: {arm}/{index}")
            require(task["releases_verified"] is True, f"release missing: {arm}/{index}")
            used_input += sum(call["usage"]["input_tokens"] for call in task["model_calls"])
            generations += task["planner_generations"]
            cumulative_input[arm].append(used_input + preflight_by_arm[arm]["input_tokens"])
            cumulative_generations[arm].append(generations)
            for call in task["model_calls"]:
                call_id = call["call_id"]
                require(call_id not in trace_calls, f"duplicate trace call ID: {call_id}")
                trace_calls[call_id] = call["usage"]
                for field in USAGE:
                    class_totals[arm][field] += call["usage"][field]

    require(len(trace_calls) == 14, f"expected 14 trace calls, got {len(trace_calls)}")
    require(set(trace_calls) == set(raw_calls), "trace/raw call ID population mismatch")
    for call_id, usage in trace_calls.items():
        require(usage == raw_calls[call_id], f"raw usage mismatch: {call_id}")

    preflight_totals = {field: sum(preflight_by_arm[a][field] for a in ARMS) for field in USAGE}
    totals = {field: preflight_totals[field] + sum(v[field] for v in class_totals.values())
              for field in USAGE}
    require(totals == stored["actual_usage_totals"], "aggregate usage differs from frozen v1 audit")
    report_eval = report["evaluation"]
    for arm in ARMS:
        require(cumulative_input[arm][-1] == stored["final_input_tokens"][arm],
                f"arm final input mismatch: {arm}")
        require(report_eval["arms"][arm]["cumulative_input_tokens"] == cumulative_input[arm],
                f"task cumulative input mismatch: {arm}")
        require(report_eval["arms"][arm]["cumulative_planner_generations"] == cumulative_generations[arm],
                f"task generation mismatch: {arm}")

    require(cumulative_input["persistent"][-1] < cumulative_input["plain"][-1]
            and cumulative_input["persistent"][-1] < cumulative_input["ephemeral"][-1],
            "token threshold fails")
    require(cumulative_generations["persistent"][-1] < cumulative_generations["plain"][-1]
            and cumulative_generations["persistent"][-1] < cumulative_generations["ephemeral"][-1],
            "generation threshold fails")
    break_even = next((i for i in range(6)
                       if cumulative_input["persistent"][i] < cumulative_input["plain"][i]
                       and cumulative_input["persistent"][i] < cumulative_input["ephemeral"][i]), None)
    require(break_even == 1, f"unexpected first break-even index: {break_even}")
    repair = trace["arms"]["persistent"][3]["repair"]
    require(repair["required"] and repair["old_reference_status"] == "missing"
            and repair["old_reference_pointer_admissions"] == 0
            and repair["attempted"] and repair["succeeded"], "task-4 repair mismatch")
    require(all(t["old_target_pointer_admissions"] == 0
                for arm in ARMS for t in trace["arms"][arm]), "stale pointer admission present")

    result = {
        "schema": "integrated-efficiency-recount-v2-result-v1",
        "status": "PASS_RECOUNT_PROVENANCE_AND_ACCOUNTING_SCOPED",
        "scope": freeze["scope"],
        "historical_source_main_commit": read_json(root / V1_AUDIT)["source_main_commit"],
        "input_main_commit": freeze["input_main_commit"],
        "input_manifest_sha256": sha256(args.manifest),
        "input_file_count": len(by_path),
        "raw_image_result_paths": len(result_paths),
        "raw_image_call_ids": len(raw_calls),
        "fresh_preflight_calls": 3,
        "task_rows": task_counts,
        "exact_submission_rows_reconstructed_from_raw_values": submission_counts,
        "usage_totals": totals,
        "final_input_tokens": {a: cumulative_input[a][-1] for a in ARMS},
        "cumulative_input_tokens": cumulative_input,
        "cumulative_planner_generations": cumulative_generations,
        "first_break_even_task": break_even + 1,
        "persistent_task4_repair": repair,
        "historical_disposition": "PASS_SCOPED",
        "new_sample": False,
        "efficiency_claim": False,
        "errors": [],
    }
    out.mkdir(parents=True, exist_ok=False)
    (out / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"status": "FAIL_RECOUNT_AUDIT", "error": str(exc)}))
        raise
