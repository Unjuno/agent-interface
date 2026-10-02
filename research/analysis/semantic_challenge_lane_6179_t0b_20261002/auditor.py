"""Independent reconstruction of Issue #6461 raw event records."""
import json
import sys
from pathlib import Path


GEN = 42
OLD = 41
SOURCE = "verifier-A"
TARGET = "task-17"
CAP = "fixture-capability-6179-t0b"
KINDS = ("valid", "stale", "missing", "revoked", "contradictory", "binding")
VECTOR_IDS = ("valid-pass", "stale-generation", "missing-mandatory",
              "revoked-authority", "contradictory-receipt", "wrong-binding")
EXPECTED_VECTORS = [
    {"id": "valid-pass", "kind": "valid", "source": SOURCE, "target": TARGET},
    {"id": "stale-generation", "kind": "stale", "source": SOURCE, "target": TARGET},
    {"id": "missing-mandatory", "kind": "missing", "source": SOURCE, "target": TARGET},
    {"id": "revoked-authority", "kind": "revoked", "source": SOURCE, "target": TARGET},
    {"id": "contradictory-receipt", "kind": "contradictory", "source": SOURCE, "target": TARGET},
    {"id": "wrong-binding", "kind": "binding", "source": "verifier-X", "target": "task-99"},
]
CONDITIONS = ("healthy", "healthy_slow", "stuck_pass", "stale_cache",
              "parser_omission", "skip_mandatory")
ROUTES = ("heartbeat_only", "detached_startup_probe", "in_path_challenge")
RESULTS = {"valid": "PASS", "stale": "UNKNOWN", "missing": "UNKNOWN",
           "revoked": "REJECT", "contradictory": "REJECT", "binding": "REJECT"}


def _expected(condition, kind):
    value = RESULTS[kind]
    generation = GEN
    if condition == "stuck_pass" and kind != "valid":
        value = "PASS"
    elif condition == "stale_cache":
        generation = OLD
    elif condition == "parser_omission" and kind == "missing":
        value = "PASS"
    elif condition == "skip_mandatory" and kind == "revoked":
        value = "PASS"
    return value, generation


def _contract(vector_id):
    return RESULTS[KINDS[VECTOR_IDS.index(vector_id)]]


def _broker_accepts(envelope, nonce, lane):
    if lane == "challenge":
        return (envelope.get("lane") == "challenge"
                and envelope.get("capability") == CAP
                and envelope.get("nonce") == nonce
                and envelope.get("generation") == GEN
                and envelope.get("source") == SOURCE
                and envelope.get("target") == TARGET)
    return (envelope.get("lane") == "ordinary"
            and envelope.get("generation") == GEN
            and envelope.get("source") == SOURCE
            and envelope.get("target") == TARGET
            and envelope.get("schema") == "ordinary-verifier-receipt-v1")


def _check_run(run, errors):
    prefix = f"{run.get('route')}:{run.get('condition')}"
    route, condition = run.get("route"), run.get("condition")
    if route not in ROUTES or condition not in CONDITIONS:
        errors.append(prefix + ":identity")
        return
    events = run.get("trace")
    if not isinstance(events, list):
        errors.append(prefix + ":trace_type")
        return
    release_events = [i for i, event in enumerate(events)
                      if event.get("event") == "ordinary_verdict_released"]
    if run.get("ordinary_verdict_released") is not (len(release_events) == 1):
        errors.append(prefix + ":release_summary")
    detection_events = [(i, e) for i, e in enumerate(events)
                        if e.get("event") == "semantic_fault_detected"]
    if route != "in_path_challenge":
        expected_event = ("heartbeat_received" if route == "heartbeat_only"
                          else "detached_startup_probe_passed")
        if len(events) != 2 or events[0].get("event") != expected_event or len(release_events) != 1:
            errors.append(prefix + ":baseline_schedule")
        if run.get("detected_before_release") is not False:
            errors.append(prefix + ":baseline_detection_claim")
    else:
        challenges = [(i, e) for i, e in enumerate(events) if e.get("event") == "challenge"]
        expected_count = 6 if condition in ("healthy", "healthy_slow") else None
        if expected_count is not None and len(challenges) != expected_count:
            errors.append(prefix + ":healthy_challenge_count")
        if expected_count is None and (not challenges or len(challenges) > 6):
            errors.append(prefix + ":fault_challenge_count")
        seen = []
        mismatch_index = None
        for _, event in challenges:
            vector = event.get("vector", {})
            vector_id = vector.get("id")
            seen.append(vector_id)
            if vector_id not in VECTOR_IDS:
                errors.append(prefix + ":unknown_vector")
                continue
            if vector != EXPECTED_VECTORS[VECTOR_IDS.index(vector_id)]:
                errors.append(prefix + ":vector_binding")
            expected_result = _contract(vector_id)
            expected_gen = GEN
            expected_delay = 3 if condition == "healthy_slow" else 0
            binding_matches = (event.get("source") == vector.get("source")
                               and event.get("target") == vector.get("target"))
            match = (event.get("observed") == expected_result
                     and event.get("generation") == expected_gen
                     and binding_matches
                     and event.get("response_delay") == expected_delay)
            if event.get("matches_contract") is not match:
                errors.append(prefix + ":candidate_match_flag")
            if not match and mismatch_index is None:
                mismatch_index = event.get("index")
        if condition in ("healthy", "healthy_slow"):
            if seen != list(VECTOR_IDS) or len(release_events) != 1 or detection_events:
                errors.append(prefix + ":healthy_gate")
            if run.get("detected_before_release") is not False or run.get("permanent_failure") is not False:
                errors.append(prefix + ":healthy_state")
        else:
            if mismatch_index is None:
                errors.append(prefix + ":fault_not_reproduced")
            if len(release_events) != 0 or len(detection_events) != 1:
                errors.append(prefix + ":fault_release_order")
            elif detection_events[0][1].get("at_index") != mismatch_index:
                errors.append(prefix + ":detection_index")
            if run.get("detected_before_release") is not True or run.get("permanent_failure") is not False:
                errors.append(prefix + ":fault_state")
    attacks = run.get("attack_results", {})
    if len(attacks.get("attempts", [])) != 3:
        errors.append(prefix + ":attack_count")
        return
    expected_attacks = ("forged_capability", "old_generation_replay", "challenge_as_ordinary")
    nonce = attacks.get("nonce")
    expected_reducer_attempts = 0
    if nonce != f"nonce-{route}-{condition}":
        errors.append(prefix + ":nonce_binding")
    for attack, attempt in zip(expected_attacks, attacks["attempts"]):
        envelope = attempt.get("submitted", {})
        expected_accepted = (_broker_accepts(envelope, nonce, "challenge")
                             if envelope.get("lane") == "challenge"
                             else _broker_accepts(envelope, nonce, "ordinary")
                             if envelope.get("lane") == "ordinary" else False)
        reducer_attempted = envelope.get("lane") == "ordinary"
        expected_reducer_attempts += int(reducer_attempted)
        reducer_accepted = reducer_attempted and _broker_accepts(envelope, nonce, "ordinary")
        if (attempt.get("attack") != attack
                or attempt.get("accepted") is not expected_accepted
                or attempt.get("reducer_attempted") is not reducer_attempted
                or attempt.get("reducer_accepted") is not reducer_accepted
                or attempt.get("publisher_event") is not reducer_accepted
                or attempt.get("actuator_effect") is not reducer_accepted):
            errors.append(prefix + ":attack_dispatch_reconstruction")
    if attacks.get("reducer_attempts") != expected_reducer_attempts:
        errors.append(prefix + ":reducer_attempt_count")
    expected_counts = {
        "ordinary_reducer_accepts": sum(bool(x.get("reducer_accepted")) for x in attacks["attempts"]),
        "publisher_events": sum(bool(x.get("publisher_event")) for x in attacks["attempts"]),
        "obligation_satisfied": sum(bool(x.get("reducer_accepted")) for x in attacks["attempts"]),
        "actuator_effects": sum(bool(x.get("actuator_effect")) for x in attacks["attempts"]),
    }
    for field, expected_count in expected_counts.items():
        if attacks.get(field) != expected_count or expected_count != 0:
            errors.append(prefix + ":boundary_effect_" + field)


def audit(raw):
    errors = []
    if (not isinstance(raw, dict) or raw.get("schema") != "6179-t0b-raw-v1"
            or raw.get("allocation") != "6179-T0B-EXECUTED-BROKER-CONTROLS-20261002-01"
            or raw.get("generation") != GEN or raw.get("old_generation") != OLD
            or raw.get("source") != SOURCE or raw.get("target") != TARGET):
        return ["header"]
    if raw.get("vectors") != EXPECTED_VECTORS:
        errors.append("vector_fixture_or_order")
    if raw.get("conditions") != list(CONDITIONS) or raw.get("routes") != list(ROUTES):
        errors.append("grid_fixture_or_order")
    if len(raw.get("runs", [])) != 18:
        return ["grid_size"]
    keys = []
    for run in raw["runs"]:
        if not isinstance(run, dict):
            errors.append("row_type")
            continue
        keys.append((run.get("route"), run.get("condition")))
        _check_run(run, errors)
    expected = [(route, condition) for route in ROUTES for condition in CONDITIONS]
    if keys != expected:
        errors.append("grid_identity_or_order")
    return errors


def main(input_path, output_path):
    import hashlib
    payload = Path(input_path).read_bytes()
    raw = json.loads(payload)
    errors = audit(raw)
    report = {"audit": "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD",
              "errors": errors, "raw_sha256": hashlib.sha256(payload).hexdigest(),
              "rows": len(raw.get("runs", []))}
    Path(output_path).write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                                 encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: auditor.py RAW_JSON REPORT_JSON")
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
