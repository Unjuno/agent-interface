from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
V38 = REPO / "research/doom/results/map01-v38-integrated-threat-live-01/runtime/events.jsonl"
V39 = REPO / "research/doom/results/map01-v39-coast-liveness-live-01/runtime/events.jsonl"


class StopAudit(ValueError):
    pass


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def verify_sources(freeze: dict) -> list[str]:
    errors = []
    for rel, expected in freeze["source_sha256"].items():
        path = REPO / rel
        if not path.is_file() or sha(path) != expected:
            errors.append("source_sha256:" + rel)
    for rel, expected in freeze["package_sha256"].items():
        path = HERE / rel
        if not path.is_file() or sha(path) != expected:
            errors.append("package_sha256:" + rel)
    return errors


def derive(v38: list[dict], v39: list[dict]) -> dict:
    cmd_rows = [row for row in v39 if row.get("event") == "command"
                and row.get("command", {}).get("id") == "cover-1"
                and row.get("command", {}).get("op") == "submit"]
    if len(cmd_rows) != 1:
        raise StopAudit("cover-1 command not unique")
    steps = cmd_rows[0]["command"].get("steps", [])
    if len(steps) <= 0 or steps[0] != {"op": "hold", "keys": ["d"], "duration_ms": 350}:
        raise StopAudit("selected hold command differs")

    held_rows = [row for row in v39 if row.get("event") == "keys_held"
                 and row.get("id") == "cover-1" and row.get("step") == 0]
    complete_rows = [row for row in v39 if row.get("event") == "step_completed"
                     and row.get("id") == "cover-1" and row.get("step") == 0]
    if len(held_rows) != 1 or len(complete_rows) != 1:
        raise StopAudit("selected hold acknowledgement/completion not unique")
    held, complete = held_rows[0], complete_rows[0]
    if held.get("keys") != ["d"] or type(held.get("input_ack_ns")) is not int:
        raise StopAudit("selected held-state acknowledgement differs")
    if type(complete.get("completed_ns")) is not int:
        raise StopAudit("selected outer completion timestamp missing")

    ack = held["input_ack_ns"]
    completed = complete["completed_ns"]
    duration_ns = steps[0]["duration_ms"] * 1_000_000
    earliest_candidate = ack + duration_ns
    latest_candidate = ack + 500_000_000
    if not earliest_candidate < latest_candidate < completed:
        raise StopAudit("frozen timing interval does not admit two candidate releases")

    direct_keyup_events = [row for row in v39
                           if row.get("event") in {"input_up", "key_up", "key_release",
                                                   "input_release_transition", "owner_keyup"}
                           and row.get("key") == "d"]
    if direct_keyup_events:
        raise StopAudit("selected trace unexpectedly contains a direct key-up event")

    return {
        "schema": "map01-v38-v39-release-observability-v1",
        "status": "NON_IDENTIFIABLE_FROM_RETAINED_RELEASE_TELEMETRY",
        "hypothesis": "two distinct compliant hypothetical key-up timestamps fit the selected explicit telemetry",
        "fixture": {"run": "map01-v39-coast-liveness-live-01", "program_id": "cover-1",
                    "step": 0, "keys": ["d"], "declared_duration_ms": 350},
        "observed": {"keys_held_input_ack_ns": ack,
                     "step_completed_ns": completed,
                     "ack_to_outer_completion_ms": (completed - ack) / 1_000_000},
        "hypothetical_keyup_times_not_observed": [
            {"ns": earliest_candidate, "occupancy_after_ack_ms": duration_ns / 1_000_000,
             "outer_completion_after_keyup_ms": (completed - earliest_candidate) / 1_000_000},
            {"ns": latest_candidate, "occupancy_after_ack_ms":
             (latest_candidate - ack) / 1_000_000,
             "outer_completion_after_keyup_ms": (completed - latest_candidate) / 1_000_000},
        ],
        "distinct_candidate_separation_ms": (latest_candidate - earliest_candidate) / 1_000_000,
        "v38_event_count": len(v38),
        "v39_event_count": len(v39),
        "scope": "explicit event-timestamp construction only; does not prove counterfactual pixel/game-trace invariance or actual physical key-up time",
        "errors": [],
    }


def main() -> int:
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    errors = verify_sources(freeze)
    if errors:
        result = {"schema": "map01-v38-v39-release-observability-v1",
                  "status": "STOP_SOURCE_IDENTITY", "errors": errors}
    else:
        try:
            result = derive(read_jsonl(V38), read_jsonl(V39))
        except (KeyError, TypeError, ValueError) as exc:
            result = {"schema": "map01-v38-v39-release-observability-v1",
                      "status": "STOP_AUDIT", "errors": [type(exc).__name__ + ":" + str(exc)]}
    (HERE / "RESULT.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                                       encoding="utf-8")
    print(json.dumps({"status": result["status"], "errors": result.get("errors", [])}))
    return 0 if not result.get("status", "").startswith("STOP") else 1


if __name__ == "__main__":
    raise SystemExit(main())
