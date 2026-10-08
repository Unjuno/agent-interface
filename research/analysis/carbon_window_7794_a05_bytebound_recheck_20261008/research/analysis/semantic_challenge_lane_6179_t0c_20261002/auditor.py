"""Independent raw-only reconstruction for Issue #6477; imports no candidate code."""
import json
import sys
from pathlib import Path


ALLOCATION = "6179-T0C-EXECUTED-BROKER-CONTROLS-20261002-01"
GEN = 42
OLD = 41
SOURCE = "verifier-A"
TARGET = "task-17"
CAPABILITY = "fixture-capability-6179-t0c"
VECTORS = [
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
ATTACKS = ("forged_capability", "old_generation_replay", "challenge_as_ordinary")
RELEASE_VECTOR = {"healthy": "valid-pass", "healthy_slow": "valid-pass",
                  "stuck_pass": "stale-generation", "stale_cache": "valid-pass",
                  "parser_omission": "missing-mandatory", "skip_mandatory": "revoked-authority"}


def broker_accepts(envelope, nonce, lane):
    if lane == "challenge":
        return (envelope.get("lane") == "challenge"
                and envelope.get("capability") == CAPABILITY
                and envelope.get("nonce") == nonce
                and envelope.get("generation") == GEN
                and envelope.get("source") == SOURCE
                and envelope.get("target") == TARGET)
    return (envelope.get("lane") == "ordinary"
            and envelope.get("generation") == GEN
            and envelope.get("source") == SOURCE
            and envelope.get("target") == TARGET
            and envelope.get("schema") == "ordinary-verifier-receipt-v1")


def check_run(run, errors):
    route, condition = run.get("route"), run.get("condition")
    prefix = f"{route}:{condition}"
    if route not in ROUTES or condition not in CONDITIONS:
        errors.append(prefix + ":identity")
        return
    trace = run.get("trace")
    if not isinstance(trace, list) or any(not isinstance(event, dict) for event in trace):
        errors.append(prefix + ":trace_type")
        return

    releases = [i for i, e in enumerate(trace) if e.get("event") == "ordinary_verdict_released"]
    detections = [(i, e) for i, e in enumerate(trace) if e.get("event") == "semantic_fault_detected"]
    released = len(releases) == 1
    if run.get("ordinary_verdict_released") is not released:
        errors.append(prefix + ":release_summary")
    if run.get("permanent_failure") is not False:
        errors.append(prefix + ":permanent_failure")

    if route in ("heartbeat_only", "detached_startup_probe"):
        expected_event = "heartbeat_received" if route == "heartbeat_only" else "detached_startup_probe_passed"
        if len(trace) != 2 or trace[0].get("event") != expected_event:
            errors.append(prefix + ":baseline_schedule")
        if not released or releases != [1] or detections:
            errors.append(prefix + ":baseline_release")
        if run.get("detected_before_release") is not False:
            errors.append(prefix + ":baseline_detection_claim")
        if trace and trace[0].get("generation") != GEN:
            errors.append(prefix + ":baseline_generation")
        release_generation = OLD if condition == "stale_cache" else GEN
        if released and (trace[1].get("generation") != release_generation
                         or trace[1].get("source") != SOURCE
                         or trace[1].get("target") != TARGET):
            errors.append(prefix + ":baseline_release_binding")
        release = trace[1] if released else {}
        vector = next(v for v in VECTORS if v["id"] == RELEASE_VECTOR[condition])
        expected_result = RESULTS[vector["kind"]]
        expected_gen = OLD if condition == "stale_cache" else GEN
        observed = "PASS" if condition in ("stuck_pass", "parser_omission", "skip_mandatory") else expected_result
        matches = observed == expected_result and expected_gen == GEN
        if (release.get("vector") != vector or release.get("result") != observed
                or release.get("generation") != expected_gen
                or release.get("source") != SOURCE or release.get("target") != TARGET
                or release.get("matches_contract") is not matches):
            errors.append(prefix + ":baseline_verdict_reconstruction")
        expected_escape = condition not in ("healthy", "healthy_slow")
        if expected_escape == matches:
            errors.append(prefix + ":baseline_escape_claim")
    else:
        challenge_rows = [(i, e) for i, e in enumerate(trace) if e.get("event") == "challenge"]
        expected_bad = {"stuck_pass": 1, "stale_cache": 0,
                        "parser_omission": 2, "skip_mandatory": 3}
        stop_at = None if condition in ("healthy", "healthy_slow") else expected_bad[condition]
        expected_ids = [v["id"] for v in VECTORS[:6 if stop_at is None else stop_at + 1]]
        seen = []
        first_mismatch = None
        for index, (trace_index, event) in enumerate(challenge_rows):
            vector = event.get("vector")
            if index >= len(VECTORS) or vector != VECTORS[index]:
                errors.append(prefix + ":vector_sequence")
                continue
            seen.append(vector.get("id"))
            expected_delay = 3 if condition == "healthy_slow" else 0
            expected_result = RESULTS[vector["kind"]]
            expected_generation = OLD if condition == "stale_cache" else GEN
            observed = expected_result
            if condition == "stuck_pass" and vector["kind"] != "valid":
                observed = "PASS"
            if condition == "parser_omission" and vector["kind"] == "missing":
                observed = "PASS"
            if condition == "skip_mandatory" and vector["kind"] == "revoked":
                observed = "PASS"
            binding_ok = (event.get("source") == SOURCE and event.get("target") == TARGET)
            expected_match = (event.get("observed") == expected_result
                              and event.get("generation") == GEN
                              and binding_ok and event.get("response_delay") == expected_delay)
            if (event.get("observed") != observed
                    or event.get("generation") != expected_generation
                    or event.get("source") != SOURCE
                    or event.get("target") != TARGET
                    or event.get("index") != index
                    or event.get("response_delay") != expected_delay
                    or event.get("matches_contract") is not expected_match):
                errors.append(prefix + ":challenge_reconstruction")
            if not expected_match and first_mismatch is None:
                first_mismatch = (index, trace_index)
        if seen != expected_ids:
            errors.append(prefix + ":challenge_prefix")
        if stop_at is None:
            if not released or len(releases) != 1 or detections:
                errors.append(prefix + ":healthy_gate")
            if run.get("detected_before_release") is not False:
                errors.append(prefix + ":healthy_detection")
            if releases and releases[0] != len(trace) - 1:
                errors.append(prefix + ":healthy_release_order")
            release = trace[releases[0]] if releases else {}
            if (release.get("vector") != VECTORS[0] or release.get("result") != "PASS"
                    or release.get("generation") != GEN or release.get("source") != SOURCE
                    or release.get("target") != TARGET or release.get("matches_contract") is not True):
                errors.append(prefix + ":healthy_release_reconstruction")
        else:
            if released or len(releases) != 0 or len(detections) != 1:
                errors.append(prefix + ":fault_release_order")
            elif first_mismatch is None or detections[0][0] != first_mismatch[1] + 1:
                errors.append(prefix + ":detection_order")
            elif detections[0][1].get("at_index") != first_mismatch[0]:
                errors.append(prefix + ":detection_index")
            if run.get("detected_before_release") is not True:
                errors.append(prefix + ":fault_detection_claim")

    attacks = run.get("attack_results")
    if not isinstance(attacks, dict):
        errors.append(prefix + ":attack_results_type")
        return
    nonce = f"nonce-{route}-{condition}"
    if attacks.get("nonce") != nonce:
        errors.append(prefix + ":nonce_binding")
    attempts = attacks.get("attempts")
    if not isinstance(attempts, list) or len(attempts) != 3:
        errors.append(prefix + ":attack_count")
        return
    expected_envelopes = [
        {"lane": "challenge", "capability": "forged-capability", "nonce": nonce,
         "generation": GEN, "source": SOURCE, "target": TARGET},
        {"lane": "challenge", "capability": CAPABILITY, "nonce": f"old-{nonce}",
         "generation": OLD, "source": SOURCE, "target": TARGET},
        {"lane": "ordinary", "origin_lane": "challenge", "generation": GEN,
         "source": SOURCE, "target": TARGET, "schema": "challenge-result-v1", "result": "PASS"},
    ]
    reducer_attempt_count = 0
    count = {"ordinary_reducer_accepts": 0, "publisher_events": 0,
             "obligation_satisfied": 0, "actuator_effects": 0}
    for attack, envelope, attempt in zip(ATTACKS, expected_envelopes, attempts):
        if not isinstance(attempt, dict) or attempt.get("attack") != attack:
            errors.append(prefix + ":attack_order")
            continue
        submitted = attempt.get("submitted")
        if submitted != envelope:
            errors.append(prefix + ":submitted_envelope")
            continue
        lane = envelope["lane"]
        accepted = broker_accepts(envelope, nonce, lane)
        reducer_attempted = lane == "ordinary"
        reducer_accepted = reducer_attempted and broker_accepts(envelope, nonce, "ordinary")
        reducer_attempt_count += int(reducer_attempted)
        expected = {"accepted": accepted, "reducer_attempted": reducer_attempted,
                    "reducer_accepted": reducer_accepted,
                    "publisher_event": reducer_accepted, "actuator_effect": reducer_accepted}
        if any(attempt.get(k) is not value for k, value in expected.items()):
            errors.append(prefix + ":attack_decision")
        count["ordinary_reducer_accepts"] += int(reducer_accepted)
        count["publisher_events"] += int(reducer_accepted)
        count["obligation_satisfied"] += int(reducer_accepted)
        count["actuator_effects"] += int(reducer_accepted)
    if attacks.get("reducer_attempts") != reducer_attempt_count:
        errors.append(prefix + ":reducer_attempt_count")
    for key, value in count.items():
        if attacks.get(key) != value or value != 0:
            errors.append(prefix + ":effect_count_" + key)


def audit(raw):
    if (not isinstance(raw, dict) or raw.get("schema") != "6179-t0c-raw-v1"
            or raw.get("allocation") != ALLOCATION or raw.get("generation") != GEN
            or raw.get("old_generation") != OLD or raw.get("source") != SOURCE
            or raw.get("target") != TARGET):
        return ["header"]
    errors = []
    if raw.get("vectors") != VECTORS:
        errors.append("vector_fixture")
    if raw.get("conditions") != list(CONDITIONS) or raw.get("routes") != list(ROUTES):
        errors.append("grid_fixture")
    runs = raw.get("runs")
    if not isinstance(runs, list) or len(runs) != 18:
        return errors + ["grid_size"]
    expected_keys = [(route, condition) for route in ROUTES for condition in CONDITIONS]
    actual_keys = []
    for run in runs:
        if not isinstance(run, dict):
            errors.append("row_type")
            continue
        actual_keys.append((run.get("route"), run.get("condition")))
        check_run(run, errors)
    if actual_keys != expected_keys:
        errors.append("grid_order_or_identity")
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
