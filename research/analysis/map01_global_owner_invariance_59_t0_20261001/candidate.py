"""Exercise the frozen workflow's run-query scope against its owner helper."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import parse_qs

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixture.json"
CASES = HERE / "cases.json"
OUT = HERE / "candidate.raw.json"


def repo_root() -> Path:
    return Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=HERE, text=True).strip())


def blob(root: Path, commit: str, path: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(root), "show", f"{commit}:{path}"], stderr=subprocess.PIPE)


def query_contract(workflow: bytes) -> tuple[str, dict[str, list[str]]]:
    match = re.search(rb"actions/workflows/([^/\s\"']+\.yml)/runs\?([^\s\"']+)", workflow)
    if not match:
        raise ValueError("workflow-run API query not found")
    return match.group(1).decode(), parse_qs(match.group(2).decode(), keep_blank_values=True)


def load_owner_helper(source: bytes):
    namespace = {"__name__": "frozen_global_owner_helper"}
    exec(compile(source, "frozen-global-owner-helper.py", "exec"), namespace)
    return namespace["select_global_owner"]


def run_case(owner, case: dict, *, workflow_path: str, allocation_id: str, required_branch: str, event_filter: bool) -> dict:
    current_event = case["current_event"]
    current_id = 2000 + case["ordinal"]
    current_sha = "a" * 40
    current = {"id": current_id, "run_number": 2, "path": workflow_path, "event": current_event,
               "head_branch": required_branch, "head_sha": current_sha, "status": "in_progress"}
    rows = [current]
    prior = None
    if case.get("prior_event"):
        prior_sha = current_sha if case["prior_head"] == "same" else "b" * 40
        prior = {"id": 1000 + case["ordinal"], "run_number": 1, "path": workflow_path,
                 "event": case["prior_event"], "head_branch": required_branch,
                 "head_sha": prior_sha, "status": "completed"}
        rows.insert(0, prior)
    visible = [r for r in rows if not event_filter or r["event"] == current_event]
    scoped = owner({"workflow_runs": visible, "total_count": len(visible)}, current_run_id=current_id,
                   workflow_path=workflow_path, allocation_id=allocation_id, required_branch=required_branch)
    complete = owner({"workflow_runs": rows, "total_count": len(rows)}, current_run_id=current_id,
                     workflow_path=workflow_path, allocation_id=allocation_id, required_branch=required_branch)
    return {"case_id": case["case_id"], "current_event": current_event,
            "prior_event": case.get("prior_event"), "prior_head": case.get("prior_head"),
            "complete_run_ids": [r["id"] for r in rows], "event_scoped_visible_ids": [r["id"] for r in visible],
            "scoped_result": scoped["result_class"], "scoped_may_enter": scoped["may_enter_formal_step"],
            "complete_result": complete["result_class"], "complete_may_enter": complete["may_enter_formal_step"]}


def main() -> None:
    if OUT.exists():
        raise SystemExit("STOP_OUTPUT_ALREADY_EXISTS")
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    case_spec = json.loads(CASES.read_text(encoding="utf-8"))
    root = repo_root()
    workflow = blob(root, fixture["source_commit"], fixture["workflow_path"])
    helper_source = blob(root, fixture["source_commit"], fixture["helper_path"])
    workflow_file, params = query_contract(workflow)
    if workflow_file != Path(fixture["workflow_path"]).name:
        raise ValueError("workflow path in API query does not match frozen workflow")
    event_filter = "event" in params
    owner = load_owner_helper(helper_source)
    rows = []
    for i, case in enumerate(case_spec["matrix"]):
        rows.append(run_case(owner, {**case, "ordinal": i}, workflow_path=fixture["workflow_path"],
                             allocation_id=fixture["allocation_id"], required_branch=fixture["required_branch"],
                             event_filter=event_filter))
    first_case = {"case_id":"first_run_no_prior_owner","ordinal":len(rows),"current_event":"push"}
    first = run_case(owner, first_case, workflow_path=fixture["workflow_path"], allocation_id=fixture["allocation_id"],
                     required_branch=fixture["required_branch"], event_filter=event_filter)
    truncated_owner = owner({"workflow_runs":[{"id":9999,"run_number":1,"path":fixture["workflow_path"],
        "event":"push","head_branch":"main","head_sha":"c"*40}],"total_count":2},
        current_run_id=9999,workflow_path=fixture["workflow_path"],allocation_id=fixture["allocation_id"],required_branch="main")
    report = {
        "schema":"map01-global-owner-event-head-candidate-v1",
        "source_commit":fixture["source_commit"],
        "workflow_blob_oid":subprocess.check_output(["git","-C",str(root),"rev-parse",f"{fixture['source_commit']}:{fixture['workflow_path']}"],text=True).strip(),
        "workflow_sha256":hashlib.sha256(workflow).hexdigest(),
        "helper_blob_oid":subprocess.check_output(["git","-C",str(root),"rev-parse",f"{fixture['source_commit']}:{fixture['helper_path']}"],text=True).strip(),
        "helper_sha256":hashlib.sha256(helper_source).hexdigest(),
        "api_workflow_file":workflow_file,"api_query_params":params,"event_filter_applied":event_filter,
        "matrix":rows,"first_run_control":first,
        "truncated_control":{"result_class":truncated_owner["result_class"],"may_enter":truncated_owner["may_enter_formal_step"]}
    }
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(report,sort_keys=True))


if __name__ == "__main__":
    main()
