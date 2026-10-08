#!/usr/bin/env python3
"""Independent audit of the saved V39 queue-drain construction checks."""

import ast
import hashlib
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = "6ea1269defb6d48a607f13b08f1aa2d223ba06e9"


def check(condition, message):
    if not condition:
        raise SystemExit("AUDIT FAIL: " + message)


def git_blob(commit, path):
    return subprocess.check_output(
        ["git", "rev-parse", f"{commit}:{path}"], cwd=ROOT, text=True).strip()


controller_path = ROOT / "research/doom/map01_overlap_controller_v39.py"
test_path = ROOT / "research/doom/test_map01_completed_future_drain_v1.py"
tree = ast.parse(controller_path.read_text(encoding="utf-8"))
functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
check("drain_pending_observation_events" in functions, "drain helper missing")
check("require_completed_turn_drain_complete" in functions, "fail-closed helper missing")

constants = {node.targets[0].id: ast.literal_eval(node.value)
             for node in tree.body if isinstance(node, ast.Assign)
             and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
             and node.targets[0].id == "COMPLETED_TURN_DRAIN_EVENT_LIMIT"}
check(constants.get("COMPLETED_TURN_DRAIN_EVENT_LIMIT") == 256, "bounded event limit")
drain = functions["drain_pending_observation_events"]
bounded_loop = any(
    isinstance(node, ast.For) and isinstance(node.iter, ast.Call)
    and isinstance(node.iter.func, ast.Name) and node.iter.func.id == "range"
    and ast.unparse(node.iter.args[0]) == "COMPLETED_TURN_DRAIN_EVENT_LIMIT"
    for node in ast.walk(drain))
check(bounded_loop, "drain does not iterate within the fixed bound")
check("backlog_pending" in ast.unparse(drain) and "incoming.empty()" in ast.unparse(drain),
      "drain does not expose remaining backlog")
require = functions["require_completed_turn_drain_complete"]
check(any(isinstance(node, ast.If) and "backlog_pending" in ast.unparse(node.test)
          and any(isinstance(child, ast.Raise) for child in ast.walk(node))
          for node in ast.walk(require)), "backlog helper does not raise")

main = functions["main"]
calls = [node for node in ast.walk(main) if isinstance(node, ast.Call)
         and isinstance(node.func, ast.Name)
         and node.func.id == "require_completed_turn_drain_complete"]
future_result = [node for node in ast.walk(main) if isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "future" and node.func.attr == "result"]
check(len(calls) == 1 and future_result and calls[0].lineno < min(n.lineno for n in future_result),
      "backlog gate must precede planner answer consumption")
latest_assignments = [node for node in ast.walk(main) if isinstance(node, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == "latest" for t in node.targets)
                      and isinstance(node.value, ast.Subscript)
                      and isinstance(node.value.value, ast.Name) and node.value.value.id == "drained"
                      and isinstance(node.value.slice, ast.Constant) and node.value.slice.value == "latest"]
replan_branches = [node for node in ast.walk(main) if isinstance(node, ast.If)
                   and "invalidation" in ast.unparse(node.test)
                   and any(isinstance(child, ast.Continue) for child in ast.walk(node))]
check(latest_assignments and replan_branches
      and latest_assignments[0].lineno < min(n.lineno for n in replan_branches),
      "newest frame must be propagated before invalidation replan")

check(git_blob(BASE, "research/doom/map01_overlap_controller_v39.py")
      == "f7b66279d87ebc3704ccef1b6a5ce646611c890b", "base controller blob")
check(git_blob(BASE, "research/live_control/executor_v12.py")
      == "7e9bb6286d5f674108688ba092300a8ad2421ba9", "base ExecutorV12 blob")

baseline = (HERE / "results/baseline-01/baseline_failure.txt").read_text(encoding="utf-8")
baseline_report = json.loads((HERE / "results/baseline-01/report.json").read_text(encoding="utf-8"))
check("AssertionError: 11 != 12" in baseline and "KeyError: 'drained_event_count'" in baseline,
      "baseline counterexample output")
check(baseline_report["expected_failure_reproduced"] is True
      and baseline_report["exit_code"] == 1, "baseline failure replay")
report = json.loads((HERE / "results/postfix-01/report.json").read_text(encoding="utf-8"))
check(report["base_commit"] == BASE, "check report base commit")
check(report["all_passed"] is True and len(report["results"]) == 10,
      "normal/optimized suite outcomes")
counts = {"normal": 0, "optimized": 0}
for row in report["results"]:
    check(row["exit_code"] == 0, "nonzero test exit: " + row["output_file"])
    output = (HERE / "results/postfix-01" / row["output_file"]).read_text(encoding="utf-8")
    match = re.search(r"Ran (\d+) tests? in ", output)
    check(match is not None and "\nOK\n" in output,
          "test output not a unittest PASS: " + row["output_file"])
    counts[row["mode"]] += int(match.group(1))
    check("FAILED" not in output, "failure marker in " + row["output_file"])

manifest = {}
for line in (HERE / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
    digest, relpath = line.split("  ", 1)
    actual = hashlib.sha256((HERE / relpath).read_bytes()).hexdigest()
    check(actual == digest, "SHA-256 mismatch: " + relpath)
    manifest[relpath] = digest

result = {
    "schema": "v39_completed_future_drain_audit_v1",
    "base_commit": BASE,
    "base_controller_blob": git_blob(BASE, "research/doom/map01_overlap_controller_v39.py"),
    "base_executor_v12_blob": git_blob(BASE, "research/live_control/executor_v12.py"),
    "normal_test_count": counts["normal"],
    "optimized_test_count": counts["optimized"],
    "test_processes": len(report["results"]),
    "manifest_files_verified": len(manifest),
    "candidate_controller_sha256": hashlib.sha256(controller_path.read_bytes()).hexdigest(),
    "regression_test_sha256": hashlib.sha256(test_path.read_bytes()).hexdigest(),
    "auditor_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "status": "PASS_CONSTRUCTION_SOURCE_AND_OUTPUT_AUDIT",
}
(HERE / "audit_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                                         encoding="utf-8", newline="\n")
print(json.dumps(result, indent=2, sort_keys=True))
