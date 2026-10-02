"""Finite synthetic broker/parser/verifier lane model for Issue #6461."""
import json
import sys
from pathlib import Path


ALLOCATION = "6179-T0B-EXECUTED-BROKER-CONTROLS-20261002-01"
GENERATION = 42
OLD_GENERATION = 41
CAPABILITY = "fixture-capability-6179-t0b"
SOURCE = "verifier-A"
TARGET = "task-17"
VECTORS = (
    {"id": "valid-pass", "kind": "valid", "source": SOURCE, "target": TARGET},
    {"id": "stale-generation", "kind": "stale", "source": SOURCE, "target": TARGET},
    {"id": "missing-mandatory", "kind": "missing", "source": SOURCE, "target": TARGET},
    {"id": "revoked-authority", "kind": "revoked", "source": SOURCE, "target": TARGET},
    {"id": "contradictory-receipt", "kind": "contradictory", "source": SOURCE, "target": TARGET},
    {"id": "wrong-binding", "kind": "binding", "source": "verifier-X", "target": "task-99"},
)
CONDITIONS = ("healthy", "healthy_slow", "stuck_pass", "stale_cache",
              "parser_omission", "skip_mandatory")
ROUTES = ("heartbeat_only", "detached_startup_probe", "in_path_challenge")


def expected_result(vector):
    return {
        "valid": "PASS", "stale": "UNKNOWN", "missing": "UNKNOWN",
        "revoked": "REJECT", "contradictory": "REJECT", "binding": "REJECT",
    }[vector["kind"]]


def verifier_result(condition, vector):
    if condition == "stuck_pass" and vector["kind"] != "valid":
        return "PASS", GENERATION, vector["source"], vector["target"]
    if condition == "stale_cache":
        return expected_result(vector), OLD_GENERATION, vector["source"], vector["target"]
    if condition == "parser_omission" and vector["kind"] == "missing":
        return "PASS", GENERATION, vector["source"], vector["target"]
    if condition == "skip_mandatory" and vector["kind"] == "revoked":
        return "PASS", GENERATION, vector["source"], vector["target"]
    return expected_result(vector), GENERATION, vector["source"], vector["target"]


def admit_challenge(envelope, nonce, generation):
    return (envelope.get("lane") == "challenge"
            and envelope.get("capability") == CAPABILITY
            and envelope.get("nonce") == nonce
            and envelope.get("generation") == generation
            and envelope.get("source") == SOURCE
            and envelope.get("target") == TARGET)


def admit_ordinary_receipt(receipt, generation):
    return (receipt.get("lane") == "ordinary"
            and receipt.get("generation") == generation
            and receipt.get("source") == SOURCE
            and receipt.get("target") == TARGET
            and receipt.get("schema") == "ordinary-verifier-receipt-v1")


def dispatch_envelope(envelope, nonce, generation):
    if envelope.get("lane") == "challenge":
        accepted = admit_challenge(envelope, nonce, generation)
        reducer_attempted = False
        reducer_accepted = False
    elif envelope.get("lane") == "ordinary":
        reducer_attempted = True
        reducer_accepted = admit_ordinary_receipt(envelope, generation)
        accepted = reducer_accepted
    else:
        accepted = False
        reducer_attempted = False
        reducer_accepted = False
    return {"accepted": accepted, "reducer_attempted": reducer_attempted,
            "reducer_accepted": reducer_accepted,
            "publisher_event": reducer_accepted,
            "actuator_effect": reducer_accepted}


def broker_attacks(route_id):
    nonce = f"nonce-{route_id}"
    valid = {"lane": "challenge", "capability": CAPABILITY,
             "nonce": nonce, "generation": GENERATION,
             "source": SOURCE, "target": TARGET}
    forged = dict(valid, capability="forged-capability")
    replay = dict(valid, nonce=f"old-{nonce}", generation=OLD_GENERATION)
    cross_lane = {"lane": "ordinary", "origin_lane": "challenge",
                  "generation": GENERATION,
                  "source": SOURCE, "target": TARGET,
                  "schema": "challenge-result-v1", "result": "PASS"}
    records = [
        {"attack": "forged_capability", "submitted": forged,
         **dispatch_envelope(forged, nonce, GENERATION)},
        {"attack": "old_generation_replay", "submitted": replay,
         **dispatch_envelope(replay, nonce, GENERATION)},
        {"attack": "challenge_as_ordinary", "submitted": cross_lane,
         **dispatch_envelope(cross_lane, nonce, GENERATION)},
    ]
    return {"nonce": nonce, "attempts": records,
            "reducer_attempts": sum(r["reducer_attempted"] for r in records),
            "ordinary_reducer_accepts": sum(r["reducer_accepted"] for r in records),
            "publisher_events": sum(r["publisher_event"] for r in records),
            "obligation_satisfied": sum(r["reducer_accepted"] for r in records),
            "actuator_effects": sum(r["actuator_effect"] for r in records)}


def simulate(route, condition):
    trace = []
    released = False
    detected = False
    if route == "in_path_challenge":
        delay = 3 if condition == "healthy_slow" else 0
        for index, vector in enumerate(VECTORS):
            observed, generation, source, target = verifier_result(condition, vector)
            valid = (generation == GENERATION and source == vector["source"]
                     and target == vector["target"])
            match = valid and observed == expected_result(vector)
            trace.append({"event": "challenge", "index": index,
                          "vector": vector, "observed": observed,
                          "generation": generation, "source": source,
                          "target": target, "response_delay": delay,
                          "matches_contract": match})
            if not match and not detected:
                detected = True
                trace.append({"event": "semantic_fault_detected", "at_index": index})
                break
        if not detected:
            released = True
            trace.append({"event": "ordinary_verdict_released",
                          "generation": GENERATION, "source": SOURCE, "target": TARGET})
    else:
        if route == "heartbeat_only":
            trace.append({"event": "heartbeat_received", "generation": GENERATION})
        else:
            trace.append({"event": "detached_startup_probe_passed", "generation": GENERATION})
        released = True
        trace.append({"event": "ordinary_verdict_released",
                      "generation": GENERATION, "source": SOURCE, "target": TARGET})
    return {"route": route, "condition": condition, "trace": trace,
            "detected_before_release": detected and not released,
            "ordinary_verdict_released": released,
            "permanent_failure": False, "attack_results": broker_attacks(f"{route}-{condition}")}


def build_raw():
    runs = [simulate(route, condition) for route in ROUTES for condition in CONDITIONS]
    return {"schema": "6179-t0b-raw-v1", "allocation": ALLOCATION,
            "generation": GENERATION, "old_generation": OLD_GENERATION,
            "source": SOURCE, "target": TARGET,
            "vectors": list(VECTORS), "conditions": list(CONDITIONS),
            "routes": list(ROUTES), "runs": runs}


def main(path):
    Path(path).write_text(json.dumps(build_raw(), sort_keys=True, indent=2) + "\n",
                          encoding="utf-8")
    print(json.dumps({"allocation": ALLOCATION, "runs": len(ROUTES) * len(CONDITIONS)},
                     sort_keys=True))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: candidate.py RAW_JSON")
    main(sys.argv[1])
