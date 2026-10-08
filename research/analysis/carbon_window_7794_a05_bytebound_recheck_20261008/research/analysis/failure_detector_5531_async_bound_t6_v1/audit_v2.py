"""Corrective independent raw-only audit; deliberately imports no candidate or v1 auditor."""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def expected_state(policy, world, event):
    if event in ("START", "NO_HEARTBEAT"):
        return "AVAILABLE", True, False, 1
    if event == "TIMEOUT_DECISION":
        return (("FAILED", False, True, 2) if policy == "timeout_as_failure"
                else ("SUSPECTED_UNAVAILABLE", False, False, 1))
    if world == "healthy_slow" and event == "FRESH_AUTHENTICATED_HEARTBEAT":
        return (("FAILED", False, True, 2) if policy == "timeout_as_failure"
                else ("AVAILABLE", True, False, 1))
    if world == "crashed" and event in ("INDEPENDENT_CRASH_WITNESS", "LATE_OLD_GENERATION_RESPONSE"):
        return "FAILED", False, True, 2
    if world == "invalid_response" and event == "INVALID_UNAUTHENTICATED_RESPONSE":
        return (("FAILED", False, True, 2) if policy == "timeout_as_failure"
                else ("SUSPECTED_UNAVAILABLE", False, False, 1))
    return None


def check_authentication(row, errors):
    event = row.get("event")
    proof = row.get("observation") or {}
    expected = {
        "FRESH_AUTHENTICATED_HEARTBEAT": (True, 1, "subject-channel", "heartbeat_sequence", 1),
        "INDEPENDENT_CRASH_WITNESS": (True, None, "kernel-domain", "witness_sequence", 1),
        "LATE_OLD_GENERATION_RESPONSE": (True, 1, "subject-channel", "heartbeat_sequence", 1),
        "INVALID_UNAUTHENTICATED_RESPONSE": (False, 1, "untrusted-channel", "heartbeat_sequence", 1),
    }.get(event)
    if expected is None:
        return
    authenticated, generation, domain, field, value = expected
    if row.get("authenticated") is not authenticated:
        errors.append(f"authentication mismatch at {row.get('trial_id')}:{event}")
    if row.get("response_generation") != generation:
        errors.append(f"response generation mismatch at {row.get('trial_id')}:{event}")
    if row.get("witness_domain") != domain:
        errors.append(f"witness domain mismatch at {row.get('trial_id')}:{event}")
    if proof.get(field) != value:
        errors.append(f"witness sequence mismatch at {row.get('trial_id')}:{event}")


def audit_records(records, freeze):
    errors = []
    by_trial = defaultdict(list)
    deadlines = [1, 3, 5]
    worlds = ["healthy_slow", "crashed", "invalid_response"]
    policies = ["timeout_as_failure", "typed_suspicion"]
    expected_trials = {(d, w, p) for d in deadlines for w in worlds for p in policies}
    prefix_groups = defaultdict(list)
    decisions = defaultdict(list)
    metrics = {
        "trials": 0,
        "raw_rows": len(records),
        "prefix_groups": 0,
        "healthy_timeout_as_failure": 0,
        "healthy_typed_failed_at_deadline": 0,
        "crash_typed_failed_after_witness": 0,
        "invalid_response_cleared_typed_suspicion": 0,
        "stale_reactivation": 0,
        "effectful_actions": 0,
        "authenticated_proof_rows_checked": 0,
    }
    for row in records:
        if not isinstance(row, dict) or row.get("schema") != "failure-detector-async-transition-v1":
            errors.append("invalid transition schema")
            continue
        by_trial[row.get("trial_id")].append(row)

    if len(by_trial) != len(expected_trials):
        errors.append("trial count mismatch")
    seen = set()
    for trial_id, rows in by_trial.items():
        rows.sort(key=lambda row: row.get("tick", -1))
        if not rows:
            errors.append(f"empty trial {trial_id}")
            continue
        first = rows[0]
        identity = (first.get("deadline"), first.get("world"), first.get("policy"))
        deadline, world, policy = identity
        seen.add(identity)
        if identity not in expected_trials or trial_id != f"d{deadline}-{world}-{policy}":
            errors.append(f"unexpected trial identity {trial_id}")
            continue
        expected_events = ["START"] + ["NO_HEARTBEAT"] * deadline + ["TIMEOUT_DECISION"]
        expected_events.append({"healthy_slow": "FRESH_AUTHENTICATED_HEARTBEAT",
                                "crashed": "INDEPENDENT_CRASH_WITNESS",
                                "invalid_response": "INVALID_UNAUTHENTICATED_RESPONSE"}[world])
        if world == "crashed":
            expected_events.append("LATE_OLD_GENERATION_RESPONSE")
        if [row.get("event") for row in rows] != expected_events:
            errors.append(f"event schedule mismatch at {trial_id}")
        last_tick = -1
        observations = []
        for row in rows:
            if (row.get("trial_id"), row.get("deadline"), row.get("world"), row.get("policy")) != (
                    trial_id, deadline, world, policy):
                errors.append(f"trial identity changes within {trial_id}")
            tick = row.get("tick")
            if type(tick) is not int or tick < last_tick:
                errors.append(f"invalid/nonmonotonic tick at {trial_id}")
            else:
                last_tick = tick
            state = expected_state(policy, world, row.get("event"))
            actual = (row.get("state"), row.get("route_enabled"), row.get("authority_revoked"),
                      row.get("authority_generation"))
            if state is None or actual != state:
                errors.append(f"state transition mismatch at {trial_id}:{row.get('event')}")
            if row.get("effectful_action") is not False:
                errors.append(f"effectful action present at {trial_id}:{row.get('event')}")
            if row.get("event") == "NO_HEARTBEAT":
                observations.append(row.get("observation"))
            if row.get("event") == "TIMEOUT_DECISION":
                decisions[(deadline, policy)].append((world, actual))
                if world == "healthy_slow" and policy == "timeout_as_failure" and actual[0] == "FAILED":
                    metrics["healthy_timeout_as_failure"] += 1
                if world == "healthy_slow" and policy == "typed_suspicion" and actual[0] == "FAILED":
                    metrics["healthy_typed_failed_at_deadline"] += 1
            if row.get("event") == "INDEPENDENT_CRASH_WITNESS" and policy == "typed_suspicion":
                if actual[0] == "FAILED" and actual[2] is True:
                    metrics["crash_typed_failed_after_witness"] += 1
            if row.get("event") == "INVALID_UNAUTHENTICATED_RESPONSE" and policy == "typed_suspicion":
                if actual[0] != "SUSPECTED_UNAVAILABLE":
                    metrics["invalid_response_cleared_typed_suspicion"] += 1
            if row.get("event") == "LATE_OLD_GENERATION_RESPONSE" and actual[0] != "FAILED":
                metrics["stale_reactivation"] += 1
            if row.get("event") in ("FRESH_AUTHENTICATED_HEARTBEAT", "INDEPENDENT_CRASH_WITNESS",
                                     "LATE_OLD_GENERATION_RESPONSE", "INVALID_UNAUTHENTICATED_RESPONSE"):
                before = len(errors)
                check_authentication(row, errors)
                if len(errors) == before:
                    metrics["authenticated_proof_rows_checked"] += 1
        expected_observations = [{"tick": t, "event": "NO_HEARTBEAT", "heartbeat_sequence": None}
                                 for t in range(1, deadline + 1)]
        if observations != expected_observations:
            errors.append(f"observation prefix mismatch at {trial_id}")
        prefix_text = canonical(observations)
        prefix_groups[(deadline, policy)].append(prefix_text)
        prefix_digest = hashlib.sha256(prefix_text.encode()).hexdigest()
        for row in rows:
            if row.get("prefix_sha256") != prefix_digest:
                errors.append(f"prefix digest mismatch at {trial_id}:{row.get('event')}")
    metrics["trials"] = len(by_trial)
    metrics["prefix_groups"] = len(prefix_groups)
    if seen != expected_trials:
        errors.append("trial matrix incomplete")
    for key, group in prefix_groups.items():
        if len(group) != len(worlds) or len(set(group)) != 1:
            errors.append(f"world prefix divergence at {key}")
    for key, group in decisions.items():
        if len(group) != len(worlds) or len({repr(state) for _, state in group}) != 1:
            errors.append(f"deadline decisions diverge at {key}")
    expected_metrics = {
        "trials": 18,
        "raw_rows": 114,
        "prefix_groups": 6,
        "healthy_timeout_as_failure": 3,
        "healthy_typed_failed_at_deadline": 0,
        "crash_typed_failed_after_witness": 3,
        "invalid_response_cleared_typed_suspicion": 0,
        "stale_reactivation": 0,
        "effectful_actions": 0,
        "authenticated_proof_rows_checked": 24,
    }
    if metrics != expected_metrics:
        errors.append("summary metric mismatch")
    return {"status": "PASS_ASYNC_DELAY_BOUNDARY_SCOPED_AUDIT_V2" if not errors else "FAIL_AUDIT_V2",
            "errors": errors, "metrics": metrics,
            "scope": "finite logical-time simulator only; no real timing or runtime safety evidence"}


def audit_file(raw_path, freeze_path, output_path):
    raw_bytes = Path(raw_path).read_bytes()
    raw_hash = hashlib.sha256(raw_bytes).hexdigest()
    freeze = json.loads(Path(freeze_path).read_text(encoding="utf-8"))
    if raw_hash != freeze["raw_sha256"]:
        result = {"status": "STOP_RAW_IDENTITY_MISMATCH", "errors": ["raw sha256 does not match audit-v2 freeze"],
                  "raw_sha256": raw_hash, "metrics": {}}
    else:
        records = [json.loads(line) for line in raw_bytes.splitlines() if line]
        result = audit_records(records, freeze)
        result["raw_sha256"] = raw_hash
    Path(output_path).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if not result["errors"] else 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True)
    parser.add_argument("--freeze", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    raise SystemExit(audit_file(args.raw, args.freeze, args.output))


if __name__ == "__main__":
    main()
