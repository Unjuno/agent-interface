"""Independent structural audit for the cross-process property probe."""
import json
from pathlib import Path

root = Path(__file__).resolve().parent
conditions = json.loads((root / "conditions.json").read_text(encoding="utf-8"))
raw = json.loads((root / "raw.json").read_text(encoding="utf-8"))
checks = []


def check(name, passed):
    checks.append({"check": name, "passed": bool(passed)})


check("attempt_and_source_match", raw["attempt_id"] == conditions["attempt_id"]
      and raw["source_commit"] == conditions["source_commit"])
check("no_input_or_activation", raw["input_sent"] is False
      and raw["window_activated"] is False)
check("spawned_window_pid_matches", raw["events"][0]["pid"] == raw["child_process_pid"]
      and (raw["status"] == "PROPERTY_COOKIE_UNAVAILABLE_FOR_THIS_TARGET"
           or raw["events"][2]["pid"] == raw["child_process_pid"]))
check("production_owner_identity_matches_child", raw["first_identity"]["pid"]
      == raw["child_process_pid"])
if raw["status"] == "PROPERTY_COOKIE_UNAVAILABLE_FOR_THIS_TARGET":
    check("setprop_refusal_is_retained", raw["set_property_succeeded"] is False
          and type(raw["set_last_error"]) is int)
    check("refusal_child_clean_exit", raw["events"][-1].get("event") == "exited"
          and raw["child_exit_code"] == 0)
else:
    check("setprop_readback_succeeded", raw["set_property_succeeded"] is True
          and raw["first_readback_matches"] is True
          and raw["first_readback"] == raw["property_token"])
    check("destroy_confirmed", raw["events"][1].get("event") == "destroyed"
          and raw["events"][1].get("before") is True
          and raw["events"][1].get("destroy_succeeded") is True
          and raw["events"][1].get("after") is False
          and raw["destroyed_handle_is_window"] is False)
    check("same_process_and_thread_recreated", raw["same_pid"] is True
          and raw["same_thread"] is True and raw["same_creation_identity"] is True)
    check("status_matches_observed_reuse", (
        raw["status"] == "PROPERTY_COOKIE_ALIAS_COUNTEREXAMPLE"
        if raw["same_hwnd"] and raw["second_handle_property_value"] == raw["property_token"]
        else raw["status"] == "REUSED_HWND_COOKIE_CLEARED"
        if raw["same_hwnd"] and raw["second_handle_property_value"] == 0
        else raw["status"] == "CROSS_PROCESS_PROPERTY_WORKS_NO_REUSE_OBSERVED"
        if not raw["same_hwnd"] and raw["second_handle_property_value"] == 0
        else False))
    check("child_clean_exit", raw["events"][-1].get("event") == "exited"
          and raw["child_exit_code"] == 0
      and raw["child_still_alive_after_join"] is False
      and raw.get("owned_child_terminated_for_cleanup") is not True)

result = {"schema": "win32-cross-process-window-property-audit-v1",
          "attempt_id": raw["attempt_id"], "status": raw["status"],
          "checks": checks, "passed": sum(c["passed"] for c in checks),
          "total": len(checks)}
(root / "audit.json").write_text(json.dumps(result, indent=2) + "\n",
                                encoding="utf-8")
print(json.dumps(result, indent=2))
if result["passed"] != result["total"]:
    raise SystemExit(1)
