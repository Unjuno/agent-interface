"""Independent raw-only audit for the current-main V39 health boundary."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOOM = HERE.parent


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def audit_payload(raw, freeze, current_controller_sha):
    checks = []

    def check(name, ok):
        if not ok:
            raise ValueError("audit failed: " + name)
        checks.append(name)

    frozen_sha = freeze["files"]["research/doom/map01_overlap_controller_v39.py"]
    check("raw source identity equals frozen controller", raw.get("source_sha256") == frozen_sha)
    check("frozen controller equals inspected source", current_controller_sha == frozen_sha)
    check("base main identity", freeze.get("base_commit") ==
          "a6343bb76e4dc0a4afa32a29c8a485a617faeff8")
    check("source health and effective floor", raw.get("source_health") == 100 and
          raw.get("hard_minimum") == max(35, 100 - 12) == 88)
    observations = raw.get("observations")
    check("ordered boundary observations", observations == [
        {"sequence": 11, "health": 89, "expected": "SOFT_CHANGED"},
        {"sequence": 12, "health": 88, "expected": "SOFT_CHANGED"},
        {"sequence": 13, "health": 87, "expected": "HARD_INVALIDATED"},
    ])
    check("strict below-floor invalidation", raw.get("soft_event_count") == 2 and
          raw.get("invalidation_reason") == "health:below_hard_minimum")
    check("planner pending before samples", raw.get("planner_started_before_observations") is True)
    check("executor cancel precedes planner interrupt", raw.get("event_order") ==
          ["executor_cancel", "planner_interrupt"])
    check("exact cover cancellation", raw.get("cancel_request") ==
          {"id": "cover-0", "op": "cancel"})
    terminal = raw.get("cover_terminal", {})
    release = terminal.get("release", {})
    check("matching terminal and verified empty release", terminal.get("event") == "terminal" and
          terminal.get("id") == "cover-0" and terminal.get("status") == "cancelled" and
          release.get("verified") is True and release.get("keys_down") == [] and
          release.get("buttons_down") == [])
    check("adversarial answer returned after invalidation",
          raw.get("planner_answer_eligible_after_interrupt") is True and
          type(raw.get("answer_return_ns")) is int and
          type(raw.get("invalidation_evaluated_ns")) is int and
          raw["answer_return_ns"] >= raw["invalidation_evaluated_ns"])
    final = raw.get("final_admission", {})
    check("final gate rejects invalidated answer", final.get("status") ==
          "REJECTED_POLICY_INVALIDATED" and final.get("executor_admission") is None and
          final.get("input_authority_admitted") is False and
          final.get("grants_input_authority") is False)
    check("no live or formal allocation", raw.get("formal_allocation_invocations") == 0 and
          raw.get("game_model_gui_os_input") is False and
          raw.get("threat_present_is_synthetic_metadata") is True)
    return {"audit": "PASS_METHOD_SCOPED", "checks_passed": len(checks),
            "checks": checks, "controller_sha256": frozen_sha,
            "live_effects": False}


def main(path):
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    controller_path = DOOM / "map01_overlap_controller_v39.py"
    result = audit_payload(raw, freeze, sha256(controller_path))
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python audit.py PATH_TO_RAW_JSON")
    main(sys.argv[1])
