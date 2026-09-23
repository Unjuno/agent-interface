"""Audit the first frozen schema-v6/v38 integrated MAP01 live allocation."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PLAN = HERE / "map01_v38_integrated_live_v1_prereg.json"


def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def result(plan, root):
    checks = {"sources": all(sha(REPO / name) == digest
                             for name, digest in plan["source_sha256"].items()),
              "first_outcome_exists": root.is_dir()}
    report_path = root / "report.json"
    if not report_path.is_file():
        value = {"schema": "map01-v38-integrated-live-audit-v1", "formal_pass": False,
                 "completed": False, "decision": "INCOMPLETE_RETAIN_FIRST_OUTCOME",
                 "checks": checks, "retained_files": sum(path.is_file() for path in root.rglob("*")),
                 "scope": plan["scope"]}
        return value
    report = read(report_path)
    runtime = root / "runtime"
    events = [json.loads(line) for line in (runtime / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    accepted = [row for row in events if row.get("event") == "accepted"]
    terminals = [row for row in events if row.get("event") == "terminal"]
    observations = [row for row in events if row.get("event") == "observation"]
    typed = [row for row in events if row.get("event") == "typed_observation"]
    released = [row for row in events if row.get("event") == "input_released"]
    plan_accepted = [row for row in accepted if row["id"].startswith("plan-")]
    checks.update({
        "model_and_effort": report["model"] == plan["requested_model"] and
                            report["effort"] == plan["requested_effort"],
        "bounded_decisions": 1 <= report["iterations"] == len(report["decisions"]) <= plan["iterations_max"],
        "continuous_game": report["game_continued_during_model_calls"] is True,
        "exact_frames": len(observations) == len(list(runtime.glob("[0-9][0-9][0-9].png"))),
        "typed_reconciled": report["typed_observations"] == len(typed) ==
                            len(report["typed_artifact_reconciliations"]) and
                            report["typed_artifact_reconciliation_failures"] == 0 and
                            all(row["matched"] for row in report["typed_artifact_reconciliations"]),
        "matched_terminals": len(accepted) == len(terminals) and
                             {row["id"] for row in accepted} == {row["id"] for row in terminals},
        "empty_release": all(row.get("release", {}).get("verified") is True and
                             row["release"]["keys_down"] == [] and
                             row["release"]["buttons_down"] == [] for row in terminals),
        "plan_admissions_count": report["program_admissions"] == len(plan_accepted),
        "independent_score": report["score"] == next((row for row in events
                              if row.get("event") == "post_control_score"), None),
        "no_current_authority_at_close": report["current_input_authority_true_at_decision_close"] == 0,
    })
    statuses = {}
    no_input = True; running_bound = True; receipt_order = True
    for decision in report["decisions"]:
        index = decision["iteration"]
        receipt = decision["final_action_admission"]
        statuses[receipt["status"]] = statuses.get(receipt["status"], 0) + 1
        if sha(root / f"decision-{index}/temporal-sheet.png") != decision["model_image_sha256"]:
            running_bound = False
        terminal = receipt["planner_terminal"]
        if (terminal["turn_id"] != decision["planner_turn_id"] or
                terminal["status"] != decision["planner_turn_status"] or
                terminal["answer_eligible"] != decision["planner_answer_eligible"] or
                terminal["terminal_observed_ns"] > receipt["controller_decided_ns"]):
            receipt_order = False
        ids = [row["id"] for row in plan_accepted if row["id"].startswith(f"plan-{index}-")]
        guard = decision.get("running_action_guard")
        if guard is None:
            if ids: no_input = False
        else:
            bindings = guard.get("program_bindings", [])
            if not bindings or guard.get("current_input_authority") is not False:
                running_bound = False
            bound_ids = {row["submit"]["command"]["id"] for row in bindings}
            if not bound_ids.issubset(set(ids)):
                running_bound = False
            for binding in bindings:
                raw = next((row for row in plan_accepted
                            if row["id"] == binding["submit"]["command"]["id"]), None)
                if raw is None or raw.get("program_sha256") != binding["accepted"].get("program_sha256"):
                    running_bound = False
    checks["receipt_order"] = receipt_order
    checks["rejected_no_input"] = no_input
    checks["running_program_binding"] = running_bound
    checks["status_counts"] = statuses == report["historical_final_action_admission_statuses"]
    early_release = True
    for event in released:
        owner = event.get("owner_release", {})
        terminal = next((row for row in terminals if row["id"] == event.get("id")), None)
        if not (owner.get("verified") is True and owner.get("keys_down") == [] and
                owner.get("buttons_down") == [] and terminal is not None and
                owner["verified_ns"] <= terminal["terminal_ns"] and
                event.get("grants_input_authority") is False):
            early_release = False
    checks["early_release_causally_closed"] = early_release
    formal = all(checks.values())
    exposed = any(decision.get("running_action_guard") is not None
                  for decision in report["decisions"])
    return {"schema": "map01-v38-integrated-live-audit-v1", "formal_pass": formal,
            "completed": True, "integrated_running_path_exposed": exposed,
            "dynamic_revocation_exposed": bool(released),
            "decision": ("INTEGRATED_PATH_EXPOSED_RETAIN_LIMITED" if formal and exposed
                         else "INTEGRATED_PATH_UNEXPOSED_HOLD" if formal
                         else "FAILED_MECHANICS_RETAIN_FIRST_OUTCOME"),
            "checks": checks, "statuses": statuses,
            "counts": {"accepted": len(accepted), "plan_accepted": len(plan_accepted),
                       "exact_observations": len(observations), "typed": len(typed),
                       "early_releases": len(released)},
            "score": report["score"], "scope": plan["scope"]}


def main():
    plan = read(PLAN)
    root = REPO / plan["output"]
    if not root.is_dir(): raise FileNotFoundError(root)
    value = result(plan, root)
    (root / "audit.json").write_text(json.dumps(value, indent=2) + "\n",
                                      encoding="utf-8", newline="\n")
    print(json.dumps(value, indent=2))
    return 0 if value["formal_pass"] else 1


if __name__ == "__main__": raise SystemExit(main())
