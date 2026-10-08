"""Independent raw-only replay oracle for #5531 T6-E1; imports no candidate code."""
import hashlib
import argparse
import json
from collections import defaultdict
from pathlib import Path


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _expected_state(policy, world, event):
    if event == "START" or event == "NO_HEARTBEAT":
        return "AVAILABLE", True, False, 1
    if event == "TIMEOUT_DECISION":
        return (("FAILED", False, True, 2) if policy == "timeout_as_failure"
                else ("SUSPECTED_UNAVAILABLE", False, False, 1))
    if world == "healthy_slow" and event == "FRESH_AUTHENTICATED_HEARTBEAT":
        return (("FAILED", False, True, 2) if policy == "timeout_as_failure"
                else ("AVAILABLE", True, False, 1))
    if world == "crashed" and event == "INDEPENDENT_CRASH_WITNESS":
        return "FAILED", False, True, 2
    if world == "crashed" and event == "LATE_OLD_GENERATION_RESPONSE":
        return "FAILED", False, True, 2
    if world == "invalid_response" and event == "INVALID_UNAUTHENTICATED_RESPONSE":
        return (("FAILED", False, True, 2) if policy == "timeout_as_failure"
                else ("SUSPECTED_UNAVAILABLE", False, False, 1))
    return None


def audit_records(records, config):
    errors = []
    by_trial = defaultdict(list)
    for row in records:
        if not isinstance(row, dict) or row.get("schema") != "failure-detector-async-transition-v1":
            errors.append("invalid transition schema")
            continue
        by_trial[row.get("trial_id")].append(row)
        expected = _expected_state(row.get("policy"), row.get("world"), row.get("event"))
        actual = (row.get("state"), row.get("route_enabled"), row.get("authority_revoked"),
                  row.get("authority_generation"))
        if expected is None or actual != expected:
            errors.append(f"transition state mismatch at {row.get('trial_id')}:{row.get('event')}")
        if row.get("effectful_action") is not False:
            errors.append(f"effectful action present at {row.get('trial_id')}:{row.get('event')}")
        if row.get("event") == "INVALID_UNAUTHENTICATED_RESPONSE" and row.get("authenticated") is not False:
            errors.append(f"invalid response authenticated at {row.get('trial_id')}")
        if row.get("event") == "INDEPENDENT_CRASH_WITNESS" and row.get("witness_domain") != "kernel-domain":
            errors.append(f"crash witness domain mismatch at {row.get('trial_id')}")

    expected_trials = {(d, w, p) for d in config["deadlines"] for w in config["worlds"]
                       for p in config["policies"]}
    if len(by_trial) != config["expected"]["trial_count"]:
        errors.append("trial count mismatch")
    seen_trials = set()
    prefix_groups = defaultdict(list)
    deadline_states = defaultdict(list)
    healthy_terminal_failures = 0
    for trial_id, rows in by_trial.items():
        rows.sort(key=lambda row: row.get("tick", -1))
        if not rows:
            errors.append(f"empty trial {trial_id}")
            continue
        identity = (rows[0].get("deadline"), rows[0].get("world"), rows[0].get("policy"))
        seen_trials.add(identity)
        if identity not in expected_trials:
            errors.append(f"unexpected trial identity {trial_id}")
            continue
        deadline, world, policy = identity
        expected_events = ([("START")] + ["NO_HEARTBEAT"] * deadline
                           + ["TIMEOUT_DECISION"])
        expected_events.append({"healthy_slow": "FRESH_AUTHENTICATED_HEARTBEAT",
                                "crashed": "INDEPENDENT_CRASH_WITNESS",
                                "invalid_response": "INVALID_UNAUTHENTICATED_RESPONSE"}[world])
        if world == "crashed":
            expected_events.append("LATE_OLD_GENERATION_RESPONSE")
        if [row.get("event") for row in rows] != expected_events:
            errors.append(f"event schedule mismatch at {trial_id}")
        observations = [row.get("observation") for row in rows if row.get("event") == "NO_HEARTBEAT"]
        expected_observations = [{"tick": tick, "event": "NO_HEARTBEAT", "heartbeat_sequence": None}
                                 for tick in range(1, deadline + 1)]
        if observations != expected_observations:
            errors.append(f"observation prefix mismatch at {trial_id}")
        prefix = json.dumps(observations, sort_keys=True, separators=(",", ":"))
        prefix_groups[(deadline, policy)].append(prefix)
        decision = [row for row in rows if row.get("event") == "TIMEOUT_DECISION"]
        if len(decision) != 1:
            errors.append(f"deadline decision count mismatch at {trial_id}")
        else:
            drow = decision[0]
            deadline_states[(deadline, policy)].append(
                (world, drow.get("state"), drow.get("route_enabled"), drow.get("authority_revoked")))
            if drow.get("prefix_sha256") != hashlib.sha256(prefix.encode()).hexdigest():
                errors.append(f"deadline prefix digest mismatch at {trial_id}")
            if world == "healthy_slow" and drow.get("state") == "FAILED":
                healthy_terminal_failures += 1
        ticks = [row.get("tick") for row in rows]
        if any(type(tick) is not int for tick in ticks):
            errors.append(f"non-integer tick at {trial_id}")
        if ticks != sorted(ticks):
            errors.append(f"time regression at {trial_id}")
    if seen_trials != expected_trials:
        errors.append("expected trial matrix incomplete")
    for key, prefixes in prefix_groups.items():
        if len(prefixes) != len(config["worlds"]) or len(set(prefixes)) != 1:
            errors.append(f"world prefixes diverge for deadline/policy {key}")
    for key, states in deadline_states.items():
        decisions = {(state, route, revoked) for _, state, route, revoked in states}
        if len(states) != len(config["worlds"]) or len(decisions) != 1:
            errors.append(f"worlds receive different deadline decisions for {key}")
    metrics = {
        "trials": len(by_trial),
        "raw_rows": len(records),
        "prefix_groups": len(prefix_groups),
        "healthy_terminal_failures_at_deadline": healthy_terminal_failures,
        "effectful_actions": sum(row.get("effectful_action") is True for row in records),
    }
    if metrics["healthy_terminal_failures_at_deadline"] != len(config["deadlines"]):
        errors.append("healthy-slow timeout-as-failure count mismatch")
    if metrics["effectful_actions"] != 0:
        errors.append("nonzero effectful action count")
    return {"status": "PASS_ASYNC_DELAY_BOUNDARY_SCOPED" if not errors else "FAIL_AUDIT",
            "errors": errors, "metrics": metrics,
            "scope": "finite logical-time simulator only; no real timing or runtime safety evidence"}


def audit_file(raw_path, output_path, freeze_path):
    raw_bytes = Path(raw_path).read_bytes()
    records = [json.loads(line) for line in raw_bytes.splitlines() if line]
    config = json.loads(Path(freeze_path).read_text(encoding="utf-8"))
    result = audit_records(records, config)
    result["raw_sha256"] = hashlib.sha256(raw_bytes).hexdigest()
    Path(output_path).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if not result["errors"] else 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("raw")
    parser.add_argument("audit")
    parser.add_argument("freeze")
    args = parser.parse_args()
    raise SystemExit(audit_file(args.raw, args.audit, args.freeze))


if __name__ == "__main__":
    main()
