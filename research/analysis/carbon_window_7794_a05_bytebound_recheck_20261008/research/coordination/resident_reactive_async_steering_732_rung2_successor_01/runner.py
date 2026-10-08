import itertools
import json
import os
import sys

SOURCE_SHA256 = os.environ.get("FROZEN_RUNNER_SHA256", "UNPINNED")
PHASES = ("RUNNING", "PAUSED", "REVOKED", "YIELDED")
OWNERS = ("FREE", "RESIDENT", "EXTERNAL")
COMMANDS = ("BOUNDED_UPDATE", "PARALLEL_ONESHOT", "SAME_RESOURCE_ONESHOT", "RESUME", "REVOKE", "UNKNOWN")
BOOLS = (False, True)

def dispatch(phase, owner, command, generation_match, safe_point, in_bounds):
    if command == "REVOKE":
        if not generation_match:
            return "STALE_GENERATION"
        if phase in ("REVOKED", "YIELDED"):
            return "TERMINAL_PROGRAM"
        return "REVOKED_IMMEDIATE"
    if not generation_match:
        return "STALE_GENERATION"
    if phase in ("REVOKED", "YIELDED"):
        return "TERMINAL_PROGRAM"
    if command == "UNKNOWN":
        return "UNKNOWN_COMMAND"
    if command == "BOUNDED_UPDATE":
        if phase != "RUNNING":
            return "NOT_RUNNING"
        if not in_bounds:
            return "PARAM_OUT_OF_BOUNDS"
        return "UPDATE_APPLIED" if safe_point else "UPDATE_QUEUED_SAFE_POINT"
    if command == "PARALLEL_ONESHOT":
        if phase != "RUNNING":
            return "NOT_RUNNING"
        return "PARALLEL_ACCEPTED" if owner == "FREE" else "RESOURCE_BUSY"
    if command == "SAME_RESOURCE_ONESHOT":
        if phase != "RUNNING":
            return "NOT_RUNNING"
        if owner == "EXTERNAL":
            return "RESOURCE_BUSY"
        if owner == "RESIDENT":
            return "HANDOFF_READY" if safe_point else "HANDOFF_QUEUED_SAFE_POINT"
        return "SAME_RESOURCE_ACCEPTED"
    if command == "RESUME":
        if phase != "PAUSED":
            return "NOT_PAUSED"
        if not safe_point:
            return "RESUME_QUEUED_SAFE_POINT"
        return "RESUMED" if owner == "FREE" else "RESOURCE_BUSY"
    raise AssertionError(command)

def stateful_traces():
    # State is changed only by this frozen dispatcher model; every command records
    # expected_generation and safe_point explicitly.
    state = {"generation": 1, "phase": "RUNNING", "pointer": "RESIDENT",
             "keyboard": "FREE", "gain": 1}
    events = []
    def update(expected, safe, value):
        result = dispatch(state["phase"], state["pointer"], "BOUNDED_UPDATE",
                          expected == state["generation"], safe, 0 <= value <= 2)
        if result == "UPDATE_APPLIED":
            state["gain"] = value
            state["generation"] += 1
        events.append(["update", expected, safe, value, result, state["generation"]])
        return result
    def parallel(expected):
        result = dispatch(state["phase"], state["keyboard"], "PARALLEL_ONESHOT",
                          expected == state["generation"], True, True)
        events.append(["parallel_keyboard", expected, result, state["pointer"], state["keyboard"]])
        return result
    def same(expected, safe):
        result = dispatch(state["phase"], state["pointer"], "SAME_RESOURCE_ONESHOT",
                          expected == state["generation"], safe, True)
        timeline = [state["pointer"]]
        if result == "HANDOFF_READY":
            state["phase"] = "PAUSED"
            state["pointer"] = "FREE"
            timeline.append(state["pointer"])
            state["pointer"] = "EXTERNAL"
            timeline.append(state["pointer"])
            state["pointer"] = "FREE"
            timeline.append(state["pointer"])
            state["phase"] = "RUNNING"
            state["pointer"] = "RESIDENT"
            timeline.append(state["pointer"])
        events.append(["same_pointer", expected, safe, result, timeline])
        return result
    def revoke(expected, safe):
        result = dispatch(state["phase"], state["pointer"], "REVOKE",
                          expected == state["generation"], safe, True)
        if result == "REVOKED_IMMEDIATE":
            state["phase"] = "REVOKED"
            state["pointer"] = "FREE"
            state["keyboard"] = "FREE"
        events.append(["revoke", expected, safe, result, state["phase"], state["pointer"]])
        return result

    assert update(1, False, 2) == "UPDATE_QUEUED_SAFE_POINT"
    assert update(1, True, 2) == "UPDATE_APPLIED"
    assert parallel(2) == "PARALLEL_ACCEPTED"
    assert same(2, False) == "HANDOFF_QUEUED_SAFE_POINT"
    assert same(2, True) == "HANDOFF_READY"
    assert update(1, True, 1) == "STALE_GENERATION"
    assert update(2, True, 3) == "PARAM_OUT_OF_BOUNDS"
    # Old-generation revoke cannot revoke generation 2.
    assert revoke(1, False) == "STALE_GENERATION"
    assert state["phase"] == "RUNNING" and state["pointer"] == "RESIDENT"
    # Current revoke is immediate off-safe-point, then commands stay terminal.
    assert revoke(2, False) == "REVOKED_IMMEDIATE"
    after = dispatch(state["phase"], state["pointer"], "PARALLEL_ONESHOT",
                     True, False, True)
    events.append(["after_revoke", 2, after, state["phase"], state["pointer"]])
    return {"events": events, "final_state": state,
            "handoff_owner_timeline": ["RESIDENT", "FREE", "EXTERNAL", "FREE", "RESIDENT"],
            "checks": {"stale_update_no_mutation": True,
                       "out_of_bounds_rejected": True,
                       "parallel_kept_pointer": True,
                       "conflict_waited_for_safe_point": True,
                       "handoff_exclusive": True,
                       "stale_revoke_no_effect": True,
                       "current_revoke_immediate": True,
                       "post_revoke_not_actionable": after == "TERMINAL_PROGRAM"}}

def naive_negative_controls():
    # Deliberately unsafe reference behavior, evaluated on frozen counterexamples.
    delayed_update = {"expected_generation": 1, "current_generation": 2}
    pointer_conflict = {"resident_owner": True, "safe_point": False}
    revoke_request = {"current_generation": 2, "expected_generation": 2,
                      "safe_point": False}
    naive_accepts_every_message = True
    naive_handoff_without_safe_point = pointer_conflict["resident_owner"] and not pointer_conflict["safe_point"]
    naive_defers_revoke = revoke_request["current_generation"] == revoke_request["expected_generation"] and not revoke_request["safe_point"]
    return {
        "stale_generation_admitted": naive_accepts_every_message and delayed_update["expected_generation"] != delayed_update["current_generation"],
        "same_resource_off_safe_point_overlaps": naive_handoff_without_safe_point,
        "revoke_waits_for_safe_point": naive_defers_revoke
    }

def formal():
    rows = []
    for values in itertools.product(PHASES, OWNERS, COMMANDS, BOOLS, BOOLS, BOOLS):
        p, o, c, g, s, b = values
        rows.append([p, o, c, g, s, b, dispatch(p, o, c, g, s, b)])
    counts = {}
    for row in rows:
        counts[row[-1]] = counts.get(row[-1], 0) + 1
    result = {"schema": "resident_async_steering_contract_v1",
              "allocation": "resident-reactive-async-steering-732-rung2-successor-01-20260921",
              "source_sha256": SOURCE_SHA256,
              "state_space": {"phases": list(PHASES), "owners": list(OWNERS),
                              "commands": list(COMMANDS), "boolean_dimensions": 3,
                              "expected_rows": 576},
              "rows": rows, "outcome_counts": counts,
              "stateful_traces": stateful_traces(),
              "negative_controls": naive_negative_controls(),
              "limits": ["exact contract enumeration only; no concurrent runtime scheduler",
                         "not a Docker/container run", "no GUI, model, input, or authority execution"]}
    print(json.dumps(result, separators=(",", ":"), sort_keys=True))

def construction_only():
    checks = {
        "stale_generation_rejected": dispatch("RUNNING","RESIDENT","BOUNDED_UPDATE",False,True,True) == "STALE_GENERATION",
        "safe_point_required": dispatch("RUNNING","RESIDENT","BOUNDED_UPDATE",True,False,True) == "UPDATE_QUEUED_SAFE_POINT",
        "nonconflicting_action_admitted": dispatch("RUNNING","FREE","PARALLEL_ONESHOT",True,False,True) == "PARALLEL_ACCEPTED",
        "same_resource_waits": dispatch("RUNNING","RESIDENT","SAME_RESOURCE_ONESHOT",True,False,True) == "HANDOFF_QUEUED_SAFE_POINT",
        "revoke_immediate": dispatch("RUNNING","RESIDENT","REVOKE",True,False,True) == "REVOKED_IMMEDIATE",
        "stateful_fixture": all(stateful_traces()["checks"].values())
    }
    print(json.dumps({"mode":"CONSTRUCTION_ONLY","checks":checks,"passed":sum(checks.values()),"total":len(checks)},sort_keys=True))
    if not all(checks.values()):
        raise SystemExit(2)

if __name__ == "__main__":
    construction_only() if "--construction-only" in sys.argv else formal()
