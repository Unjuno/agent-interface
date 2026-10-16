from __future__ import annotations
import copy
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent

def audit(row):
    errors = []
    def check(ok, label):
        if not ok:
            errors.append(label)
    check(row.get("candidate_invocations") == 1, "one candidate invocation")
    check(row.get("candidate_source") == "PR #7429 head e22e59732033438916415f71b53f86695b1c448a",
          "exact latest source head")
    cells = row.get("cells", [])
    check([c.get("executor") for c in cells] == ["ExecutorV12", "ExecutorV13"],
          "both versioned executor cells")
    for cell in cells:
        name = cell.get("executor")
        state = cell.get("before_close", {})
        check(state.get("exception") == {"type": "RuntimeError", "message": "injected scorer baseline failure"},
              f"{name} injected failure surfaced")
        check(state.get("active_id") == f"barrier-a02-{name.lower()}", f"{name} active slot retained")
        check(state.get("used_id_retained") is True and state.get("backend_lease_set") is True,
              f"{name} admission state fail-closed")
        check(state.get("admission_publication_error") == {
            "status": "delivery_unknown",
            "error": {"type": "RuntimeError", "message": "injected scorer baseline failure"}},
            f"{name} delivery uncertainty typed")
        check(state.get("worker_started") is False and state.get("worker_alive") is False,
              f"{name} worker never starts")
        check(state.get("execute_count") == 0, f"{name} sends no backend step")
        check(cell.get("close_error") is None and cell.get("closed_after_close") is True,
              f"{name} shutdown succeeds")
        check(cell.get("active_retained_after_close") is True,
              f"{name} slot remains conservatively retained")
        check(cell.get("worker_alive_after_close") is False,
              f"{name} no worker survives shutdown")
        if name == "ExecutorV13":
            check(state.get("watcher_registered") is False, "V13 failed submit removes unstarted release watcher")
    return errors

result = json.loads((ROOT / "RESULT.json").read_text())
errors = audit(result)
mutations = {}
for name, change in {
    "action_started": lambda x: x["cells"][0]["before_close"].update(execute_count=1),
    "active_cleared": lambda x: x["cells"][1].update(active_retained_after_close=False),
    "delivery_status_lost": lambda x: x["cells"][0]["before_close"].update(admission_publication_error=None),
}.items():
    altered = copy.deepcopy(result)
    change(altered)
    mutations[name] = bool(audit(altered))
if not all(mutations.values()):
    errors.append("negative control escaped")
summary = {
    "schema": "admission-baseline-barrier-a02-audit-v1",
    "scope": "latest PR #7429 ExecutorV12/V13 accepted-callback failure with fake backends",
    "errors": errors,
    "passed": not errors,
    "negative_controls_rejected": mutations,
    "classification": "FAIL_CLOSED_SHUTDOWN_CONFIRMED" if not errors else "STOP",
}
(ROOT / "AUDIT.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
print(json.dumps(summary, sort_keys=True))
raise SystemExit(bool(errors))
