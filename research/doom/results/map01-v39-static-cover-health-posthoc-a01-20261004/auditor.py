import json
import sys
from pathlib import Path

raw_path = Path(sys.argv[1])
candidate_path = Path(sys.argv[2])
r = [json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines() if line.strip()]
c = json.loads(candidate_path.read_text(encoding="utf-8"))

def select(kind, identifier=None):
    return [x for x in r if x.get("event") == kind and (identifier is None or x.get("id") == identifier)]

cmds = [x.get("command") for x in select("command") if x.get("command", {}).get("id") == "cover-5" and x.get("command", {}).get("op") == "submit"]
acc = select("accepted", "cover-5")
obs = [x for x in select("typed_observation", "cover-5") if isinstance(x.get("signals", {}).get("health", {}).get("value"), int)]
prior = [x for x in select("typed_observation", "plan-4-primary-0-1") if acc and x.get("capture_ns", 0) < acc[0].get("accepted_ns", 0)]
prior.sort(key=lambda x: x["capture_ns"])
started = sorted(select("step_started", "cover-5"), key=lambda x: x.get("step", -1))
completed = sorted(select("step_completed", "cover-5"), key=lambda x: x.get("step", -1))
held = sorted(select("keys_held", "cover-5"), key=lambda x: x.get("step", -1))
cancel = sorted(select("cancel_requested", "cover-5"), key=lambda x: x.get("requested_ns", 0))
terminal = select("terminal", "cover-5")
first_drop = next((x for x in obs if prior and x["signals"]["health"].get("value") < prior[-1]["signals"]["health"].get("value")), None)
checks = {
  "single_accepted_static_cover": len(cmds) == len(acc) == 1 and len(cmds[0].get("steps", [])) == 16 and c["accepted_program"]["steps"] == cmds[0]["steps"],
  "prior_health_is_61": bool(prior) and prior[-1]["signals"]["health"].get("value") == 61 and c["preceding_sample"]["health"] == 61,
  "cover_health_decreases_55_to_48": bool(obs) and obs[0]["signals"]["health"].get("value") == 55 and obs[-1]["signals"]["health"].get("value") == 48 and c["cover_samples"]["first"]["health"] == 55 and c["cover_samples"]["last"]["health"] == 48,
  "started_steps_match_recorded_candidate": c["execution"]["started_steps"] == [x.get("step") for x in started] and len(started) >= 12,
  "step_completion_sequence_recorded": c["execution"]["completed_steps"] == [x.get("step") for x in completed] and [x.get("step") for x in completed] == list(range(11)),
  "hold_events_match_command_steps": c["execution"]["keys_held"] == [{"step": x.get("step"), "keys": x.get("keys")} for x in held],
  "no_early_cancel_or_revocation_record": len(cancel) == 1 and len(terminal) == 1 and not [x for x in r if x.get("id") == "cover-5" and x.get("event") in ("revoked", "input_released")] and first_drop is not None and cancel[0].get("requested_ns", 0) > obs[-1].get("capture_ns", 0),
  "eventual_verified_release_after_cancel": bool(terminal) and terminal[0].get("release", {}).get("verified") is True and terminal[0].get("release", {}).get("verified_ns", 0) >= cancel[0].get("requested_ns", 0) and terminal[0].get("terminal_ns", 0) >= terminal[0].get("release", {}).get("verified_ns", 0),
  "candidate_time_bounds_match_raw": c["response_order"]["first_lower_health_capture_ns"] == first_drop.get("capture_ns") and c["cover_samples"]["min_health"] == min(x["signals"]["health"]["value"] for x in obs),
}
result = {"schema": "v39-static-cover-health-posthoc-audit-a01-v1", "pass": all(checks.values()), "checks": checks,
          "derived": {"preceding_health": prior[-1]["signals"]["health"].get("value") if prior else None,
                      "cover_first_health": obs[0]["signals"]["health"].get("value") if obs else None,
                      "cover_last_health": obs[-1]["signals"]["health"].get("value") if obs else None,
                      "cover_min_health": min((x["signals"]["health"]["value"] for x in obs), default=None),
                      "first_drop_sequence": first_drop.get("sequence") if first_drop else None,
                      "last_cover_sequence": obs[-1].get("sequence") if obs else None,
                      "cancel_ns": cancel[0].get("requested_ns") if cancel else None,
                      "terminal_status": terminal[0].get("status") if terminal else None}}
print(json.dumps(result, indent=2, sort_keys=True))
raise SystemExit(0 if result["pass"] else 1)

