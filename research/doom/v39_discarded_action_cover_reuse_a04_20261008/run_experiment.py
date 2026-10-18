"""Compare exact current-main and candidate cover-reuse predicates."""
import ast
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
FREEZE = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))


def pinned(commit, expected):
    path = FREEZE["source"]
    blob = subprocess.check_output(
        ["git", "-C", str(REPO), "rev-parse", f"{commit}:{path}"], text=True
    ).strip()
    data = subprocess.check_output(["git", "-C", str(REPO), "cat-file", "blob", blob])
    if blob != expected["blob"] or hashlib.sha256(data).hexdigest() != expected["sha256"]:
        raise ValueError(f"source mismatch at {commit}")
    tree = ast.parse(data.decode("utf-8"))
    node = next(item for item in tree.body if isinstance(item, ast.FunctionDef)
                and item.name == "reusable_cover")
    module = ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[]))
    scope = {}
    exec(compile(module, f"reusable_cover-{commit[:8]}.py", "exec"), scope)
    return scope["reusable_cover"]


def run():
    base = pinned(FREEZE["baseline_commit"], FREEZE["baseline"])
    candidate = pinned(FREEZE["candidate_commit"], FREEZE["candidate"])
    cover = [{"action": "fire", "extent": "short"}]
    validity = [{"signal_id": "health", "critical_health_minimum": 35}]
    partial_stale = {"iteration": 3, "model_action_discarded": False,
        "remaining_action_discarded": True,
        "executor_preacceptance_rejection": {"reason":
            "latest observation sequence required before input"},
        "action": {"state": "active", "next_cover": cover,
                   "next_cover_validity": validity}}
    completed = {"iteration": 4, "model_action_discarded": False,
        "remaining_action_discarded": False,
        "action": {"state": "active", "next_cover": cover,
                   "next_cover_validity": validity}}
    legacy = {"iteration": 5, "model_action_discarded": False,
        "action": {"state": "active", "next_cover": cover,
                   "next_cover_validity": validity}}

    base_partial = base([partial_stale])
    candidate_partial = candidate([partial_stale])
    candidate_complete = candidate([completed])
    candidate_legacy = candidate([legacy])
    if base_partial[0] != cover:
        raise AssertionError("baseline contrast not reproduced")
    if candidate_partial != ([], None, None):
        raise AssertionError("candidate reused cover from discarded remaining action")
    if candidate_complete != (cover, validity[0], 4):
        raise AssertionError("valid completed action reuse regressed")
    if candidate_legacy != (cover, validity[0], 5):
        raise AssertionError("legacy record behavior regressed")
    return {
        "schema": "v39-discarded-action-cover-reuse-comparison-v1",
        "baseline_commit": FREEZE["baseline_commit"],
        "candidate_commit": FREEZE["candidate_commit"],
        "partial_stale_action": {"baseline_reuses_cover": True,
                                  "candidate_reuses_cover": False},
        "completed_action_control": {"candidate_reuses_cover": True},
        "legacy_record_control": {"candidate_reuses_cover": True},
        "decision": "PASS; candidate suppresses stale cover reuse while preserving valid and legacy reuse",
        "scope": "Exact AST-extracted reusable_cover functions at the frozen main and PR #8643 commits with synthetic decision receipts. No controller, monitor, planner, app, model, OS input or live task is run.",
    }


if __name__ == "__main__":
    result = run()
    (ROOT / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n",
                                      encoding="utf-8")
    print(json.dumps(result, indent=2))
