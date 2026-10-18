#!/usr/bin/env python3
"""Independent, oracle-driven audit for Issue #8473 T0 raw output."""

import copy
import json
import sys
from pathlib import Path


SUMMARY = {
    ("occlusion_rearrangement", "NO_FEEDBACK"): (4, 1, 0, "EFFECT", "rearrange-then-save"),
    ("occlusion_rearrangement", "GLOBAL_BLACKLIST"): (1, 0, 2, "NO_PLAN", None),
    ("occlusion_rearrangement", "SCOPED_NOGOOD"): (3, 0, 1, "EFFECT", "rearrange-then-save"),
    ("focus_recovery", "NO_FEEDBACK"): (4, 1, 0, "EFFECT", "refocus-then-type"),
    ("focus_recovery", "GLOBAL_BLACKLIST"): (1, 0, 2, "NO_PLAN", None),
    ("focus_recovery", "SCOPED_NOGOOD"): (3, 0, 1, "EFFECT", "refocus-then-type"),
    ("no_alternative", "NO_FEEDBACK"): (2, 1, 0, "NO_PLAN", None),
    ("no_alternative", "GLOBAL_BLACKLIST"): (1, 0, 1, "NO_PLAN", None),
    ("no_alternative", "SCOPED_NOGOOD"): (1, 0, 1, "NO_PLAN", None),
    ("transient_blocker_clears", "NO_FEEDBACK"): (2, 0, 0, "EFFECT", "fresh-ready-snapshot"),
    ("transient_blocker_clears", "GLOBAL_BLACKLIST"): (1, 0, 1, "NO_PLAN", None),
    ("transient_blocker_clears", "SCOPED_NOGOOD"): (2, 0, 0, "EFFECT", "fresh-ready-snapshot"),
    ("constraint_expires", "NO_FEEDBACK"): (2, 0, 0, "EFFECT", "same-state-after-expiry"),
    ("constraint_expires", "GLOBAL_BLACKLIST"): (1, 0, 1, "NO_PLAN", None),
    ("constraint_expires", "SCOPED_NOGOOD"): (2, 0, 0, "EFFECT", "same-state-after-expiry"),
    ("unknown_then_recheck", "NO_FEEDBACK"): (2, 0, 0, "EFFECT", "recheck-after-unknown"),
    ("unknown_then_recheck", "GLOBAL_BLACKLIST"): (2, 0, 0, "EFFECT", "recheck-after-unknown"),
    ("unknown_then_recheck", "SCOPED_NOGOOD"): (2, 0, 0, "EFFECT", "recheck-after-unknown"),
    ("timeout_then_recheck", "NO_FEEDBACK"): (2, 0, 0, "EFFECT", "recheck-after-timeout"),
    ("timeout_then_recheck", "GLOBAL_BLACKLIST"): (2, 0, 0, "EFFECT", "recheck-after-timeout"),
    ("timeout_then_recheck", "SCOPED_NOGOOD"): (2, 0, 0, "EFFECT", "recheck-after-timeout"),
}


def _core(source, oracle, raw):
    errors = []
    if raw.get("schema") != "scoped-nogood-raw-v1":
        errors.append("raw_schema")
    scenarios = {case["id"]: case for case in source["scenarios"]}
    expected_keys = set(SUMMARY)
    seen = {}
    for row in raw.get("runs", []):
        key = (row.get("scenario"), row.get("policy"))
        if key in seen:
            errors.append("duplicate_run")
        seen[key] = row
    if set(seen) != expected_keys:
        errors.append("run_denominator")

    for key, expected in SUMMARY.items():
        row = seen.get(key)
        if row is None:
            continue
        sid, policy = key
        case = scenarios[sid]
        truth = oracle["scenarios"][sid]
        q, dup, pruned, terminal, selected = expected
        observed = (row.get("feasibility_queries"), row.get("duplicate_infeasible_queries"),
                    row.get("pruned_plans"), row.get("terminal"), row.get("selected_proposal"))
        if observed != expected:
            errors.append(f"summary:{sid}:{policy}")
        if row.get("authority") is not False:
            errors.append(f"authority:{sid}:{policy}")
        if row.get("proposal_ids") != [p["id"] for p in case["proposals"]]:
            errors.append(f"proposal_ledger:{sid}:{policy}")

        proposals = {p["id"]: p for p in case["proposals"]}
        attempts = row.get("attempts", [])
        infeasible_seen = []
        queried = 0
        for attempt in attempts:
            status = attempt.get("status")
            proposal = proposals.get(attempt.get("proposal"))
            if proposal is None:
                errors.append(f"unknown_proposal:{sid}:{policy}")
                continue
            if status == "PRUNED":
                if attempt.get("by") == "SCOPED_NOGOOD":
                    if policy != "SCOPED_NOGOOD":
                        errors.append(f"wrong_scoped_prune:{sid}:{policy}")
                    prior = [x for x in infeasible_seen
                             if x["operation"] == attempt.get("operation")
                             and x["generation"] == attempt.get("generation")
                             and x["target"] == attempt.get("target")
                             and x["surface"] == attempt.get("surface")
                             and x["evidence"] == attempt.get("evidence")
                             and x["expires_at"] == attempt.get("expires_at")
                             and attempt.get("tick", x["expires_at"]) < x["expires_at"]]
                    if not prior:
                        errors.append(f"ungrounded_scoped_prune:{sid}:{policy}")
                elif attempt.get("by") == "GLOBAL_BLACKLIST":
                    if policy != "GLOBAL_BLACKLIST":
                        errors.append(f"wrong_global_prune:{sid}:{policy}")
                    if not any(x["operation"] in proposal["steps"] for x in infeasible_seen):
                        errors.append(f"ungrounded_global_prune:{sid}:{policy}")
                else:
                    errors.append(f"unknown_prune_kind:{sid}:{policy}")
                continue

            op = attempt.get("operation")
            generation = attempt.get("generation")
            if op not in proposal["steps"]:
                errors.append(f"operation_not_in_plan:{sid}:{policy}")
            queried += 1
            reason = attempt.get("reason")
            if status == "INFEASIBLE":
                code = truth.get("infeasible", {}).get(f"{generation}|{op}")
                if code is None or not isinstance(reason, dict) or reason.get("code") != code:
                    errors.append(f"unsupported_infeasibility:{sid}:{policy}")
                elif reason.get("generation") != generation or not all(
                    reason.get(k) for k in ("target", "surface", "evidence")
                ) or not isinstance(reason.get("expires_at"), int) or attempt.get("tick", 0) >= reason["expires_at"]:
                    errors.append(f"incomplete_scope:{sid}:{policy}")
                else:
                    infeasible_seen.append({"operation": op, "generation": generation,
                                            "target": reason["target"], "surface": reason["surface"],
                                            "evidence": reason["evidence"],
                                            "expires_at": reason["expires_at"]})
            elif status == "TIMEOUT":
                if not truth.get("timeouts_are_not_infeasibility", False) or reason is not None:
                    errors.append(f"timeout_truth:{sid}:{policy}")
            elif status == "FEASIBLE":
                effect = truth.get("feasible_at", {}).get(f"{generation}|{attempt.get('tick')}|{op}")
                if effect is None or attempt.get("effect") != effect:
                    errors.append(f"oracle_infeasible_effect:{sid}:{policy}")
            elif status == "UNKNOWN":
                if not truth.get("unknown_is_not_infeasibility", False) or reason is not None:
                    errors.append(f"unknown_truth:{sid}:{policy}")
            else:
                errors.append(f"unknown_status:{sid}:{policy}")
        if queried != q:
            errors.append(f"query_count:{sid}:{policy}")

        if terminal == "EFFECT":
            plan = proposals.get(selected)
            accepted = [a["operation"] for a in attempts
                        if a.get("proposal") == selected and a.get("status") == "FEASIBLE"]
            accepted_effects = [a["effect"] for a in attempts
                                if a.get("proposal") == selected and a.get("status") == "FEASIBLE"]
            if plan is None or plan["steps"] not in truth.get("feasible_effect_paths", []):
                path = [] if plan is None else plan["steps"]
                if not any(all(op in path for op in feasible)
                           for feasible in truth.get("feasible_effect_paths", [])):
                    errors.append(f"selected_not_oracle_feasible:{sid}:{policy}")
            if plan is not None and (accepted != plan["steps"] or row.get("effects") != accepted_effects):
                errors.append(f"effect_trace:{sid}:{policy}")
        elif policy == "SCOPED_NOGOOD" and truth.get("feasible_effect_paths"):
            errors.append(f"scoped_lost_feasible_plan:{sid}")

    # Fixed-fixture discriminators: scoped feedback saves one duplicate check in the two
    # repeated-blocker cases and preserves alternatives after their dependency generation changes.
    for sid in ("occlusion_rearrangement", "focus_recovery"):
        a = seen.get((sid, "NO_FEEDBACK"), {})
        b = seen.get((sid, "SCOPED_NOGOOD"), {})
        if a.get("duplicate_infeasible_queries", 0) <= b.get("duplicate_infeasible_queries", 0):
            errors.append(f"no_duplicate_reduction:{sid}")
        if b.get("terminal") != "EFFECT":
            errors.append(f"alternative_lost:{sid}")
    expired = seen.get(("constraint_expires", "SCOPED_NOGOOD"), {})
    unknown = seen.get(("unknown_then_recheck", "SCOPED_NOGOOD"), {})
    for row, sid, expected_id in ((expired, "constraint_expires", "same-state-after-expiry"),
                                  (unknown, "unknown_then_recheck", "recheck-after-unknown")):
        if row.get("terminal") != "EFFECT" or row.get("selected_proposal") != expected_id:
            errors.append(f"recheck_lost:{sid}")
    return errors


def _mutate(raw, name):
    changed = copy.deepcopy(raw)
    runs = {(x["scenario"], x["policy"]): x for x in changed["runs"]}
    if name == "omit_blocker":
        x = runs[("occlusion_rearrangement", "SCOPED_NOGOOD")]
        next(a for a in x["attempts"] if a.get("status") == "INFEASIBLE").pop("reason")
    elif name == "globalize_scope":
        x = runs[("occlusion_rearrangement", "SCOPED_NOGOOD")]
        x["terminal"] = "NO_PLAN"
        x["selected_proposal"] = None
        x["pruned_plans"] = 2
        x["attempts"][-1] = {"proposal": "rearrange-then-save", "operation": "click_save",
                             "generation": 2, "tick": 2, "status": "PRUNED", "by": "SCOPED_NOGOOD",
                             "target": "save_button", "surface": "window_7", "evidence": "obs_occ_1",
                             "expires_at": 5}
        x["feasibility_queries"] -= 1
        x["effects"] = ["blocker_moved"]
    elif name == "reuse_after_generation_change":
        x = runs[("transient_blocker_clears", "SCOPED_NOGOOD")]
        x["terminal"] = "NO_PLAN"
        x["selected_proposal"] = None
        x["pruned_plans"] = 1
        x["attempts"][-1] = {"proposal": "fresh-ready-snapshot", "operation": "click_refresh",
                             "generation": 12, "tick": 1, "status": "PRUNED", "by": "SCOPED_NOGOOD",
                             "target": "refresh_button", "surface": "window_2", "evidence": "obs_busy_11",
                             "expires_at": 5}
        x["feasibility_queries"] -= 1
    elif name == "timeout_as_infeasible":
        x = runs[("timeout_then_recheck", "SCOPED_NOGOOD")]
        x["attempts"][0]["status"] = "INFEASIBLE"
        x["attempts"][0]["reason"] = {"code": "TIMEOUT", "target": "open_button",
                                      "surface": "window_4", "evidence": "timeout", "generation": 15}
        x["attempts"][1] = {"proposal": "recheck-after-timeout", "operation": "click_open",
                            "generation": 15, "tick": 1, "status": "PRUNED", "by": "SCOPED_NOGOOD",
                            "target": "open_button", "surface": "window_4", "evidence": "timeout",
                            "expires_at": 20}
        x["feasibility_queries"] -= 1
        x["pruned_plans"] += 1
        x["terminal"] = "NO_PLAN"
        x["selected_proposal"] = None
    elif name == "delete_available_alternative":
        x = runs[("focus_recovery", "SCOPED_NOGOOD")]
        x["proposal_ids"].remove("refocus-then-type")
    return changed


def audit(source, oracle, raw):
    errors = _core(source, oracle, raw)
    controls = {}
    for name in ("omit_blocker", "globalize_scope", "reuse_after_generation_change",
                 "timeout_as_infeasible", "delete_available_alternative"):
        controls[name] = bool(_core(source, oracle, _mutate(raw, name)))
    if not all(controls.values()):
        errors.append("ineffective_mutation_control")
    return {"status": "PASS_METHOD_SCOPED" if not errors else "FAIL_UNSOUND_PRUNING",
            "runs": len(raw.get("runs", [])), "errors": errors, "mutations_rejected": controls}


def main(argv):
    source = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    raw = json.loads(Path(argv[2]).read_text(encoding="utf-8"))
    oracle = json.loads(Path(argv[3]).read_text(encoding="utf-8"))
    result = audit(source, oracle, raw)
    Path(argv[4]).write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
                              encoding="utf-8")
    return 0 if result["status"] == "PASS_METHOD_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
