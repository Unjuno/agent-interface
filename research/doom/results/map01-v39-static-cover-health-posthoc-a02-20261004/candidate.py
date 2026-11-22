import hashlib
import json
import sys
from pathlib import Path

raw_path = Path(sys.argv[1])
rows = [json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines() if line.strip()]

def events(kind, identifier=None):
    return [r for r in rows if r.get("event") == kind and (identifier is None or r.get("id") == identifier)]

commands = [r["command"] for r in events("command") if r.get("command", {}).get("id") == "cover-5" and r.get("command", {}).get("op") == "submit"]
accepted = events("accepted", "cover-5")
steps = commands[0]["steps"] if len(commands) == 1 else []
cover_samples = [r for r in events("typed_observation", "cover-5") if isinstance(r.get("signals", {}).get("health", {}).get("value"), int)]
prior = [r for r in events("typed_observation", "plan-4-primary-0-1") if r.get("capture_ns", 0) < (accepted[0].get("accepted_ns", 0) if accepted else 0)]
prior.sort(key=lambda r: r["capture_ns"])
starts = sorted(events("step_started", "cover-5"), key=lambda r: r.get("step", -1))
completes = sorted(events("step_completed", "cover-5"), key=lambda r: r.get("step", -1))
held = sorted(events("keys_held", "cover-5"), key=lambda r: r.get("step", -1))
requests = sorted(events("cancel_requested", "cover-5"), key=lambda r: r.get("requested_ns", 0))
terminals = events("terminal", "cover-5")
revocation_rows = [r for r in rows if r.get("id") == "cover-5" and r.get("event") in ("revoked", "input_released")]
health = [r["signals"]["health"]["value"] for r in cover_samples]
result = {
    "schema": "v39-static-cover-health-posthoc-a01-v1",
    "source_events_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
    "scope": {"program_id": "cover-5", "preceding_program_id": "plan-4-primary-0-1"},
    "accepted_program": {
        "count": len(accepted), "step_count": len(steps), "program_sha256": accepted[0].get("program_sha256") if accepted else None,
        "steps": steps,
    },
    "preceding_sample": ({"sequence": prior[-1].get("sequence"), "health": prior[-1]["signals"]["health"].get("value"),
                          "ammo": prior[-1]["signals"]["ammo"].get("value"), "capture_ns": prior[-1].get("capture_ns")} if prior else None),
    "cover_samples": {"count": len(cover_samples), "first": ({"sequence": cover_samples[0].get("sequence"), "health": health[0], "capture_ns": cover_samples[0].get("capture_ns")} if cover_samples else None),
                      "last": ({"sequence": cover_samples[-1].get("sequence"), "health": health[-1], "capture_ns": cover_samples[-1].get("capture_ns")} if cover_samples else None),
                      "min_health": min(health) if health else None, "max_health": max(health) if health else None},
    "execution": {"started_steps": [r.get("step") for r in starts], "completed_steps": [r.get("step") for r in completes],
                  "keys_held_steps": [r.get("step") for r in held], "keys_held": [{"step": r.get("step"), "keys": r.get("keys")} for r in held]},
    "response_order": {"program_accept_ns": accepted[0].get("accepted_ns") if accepted else None,
                       "first_step_started_ns": starts[0].get("issued_ns") if starts else None,
                       "first_lower_health_capture_ns": next((r.get("capture_ns") for r in cover_samples if prior and r["signals"]["health"].get("value") < prior[-1]["signals"]["health"].get("value")), None),
                       "cancel_requests": [{"requested_ns": r.get("requested_ns"), "matched": r.get("matched")} for r in requests],
                       "recorded_revocation_or_early_release_count": len(revocation_rows),
                       "terminal": ([{"status": r.get("status"), "release_verified": r.get("release", {}).get("verified"),
                                      "release_verified_ns": r.get("release", {}).get("verified_ns"), "terminal_ns": r.get("terminal_ns")} for r in terminals])},
}
print(json.dumps(result, indent=2, sort_keys=True))

