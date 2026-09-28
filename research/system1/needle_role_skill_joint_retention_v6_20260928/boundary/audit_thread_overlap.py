"""Independent standard-library audit of one host thread-boundary raw record."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def unique_pairs(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("duplicate_json_key")
        out[key] = value
    return out


def audit(document):
    errors = []
    if document.get("schema") != "needle-host-thread-overlap-boundary-v1":
        errors.append("schema")
    if document.get("allocation") != "needle-host-thread-overlap-boundary-20260928-v1":
        errors.append("allocation")
    env = document.get("environment", {})
    if (env.get("thread_count") != 2 or env.get("docker_invocations") != 0
            or env.get("formal_seed_access") is not False or env.get("optimizer_steps") != 0
            or env.get("model_calls") != 0 or env.get("clock") != "time.perf_counter_ns"):
        errors.append("environment_scope")
    record = document.get("online_window")
    if not isinstance(record, dict):
        return errors + ["online_window"]
    queries, feedback = record.get("queries"), record.get("feedback")
    if not isinstance(queries, list) or len(queries) != 1:
        return errors + ["query_cardinality"]
    if not isinstance(feedback, list) or len(feedback) != 1:
        return errors + ["feedback_cardinality"]
    query, item = queries[0], feedback[0]
    if not isinstance(query, dict) or not isinstance(item, dict):
        return errors + ["event_types"]
    qs, qe = query.get("inference_start_ns"), query.get("inference_end_ns")
    qid, qworker = query.get("query_id"), query.get("worker_id")
    calls = query.get("inference_calls")
    if (type(qs) is not int or type(qe) is not int or not 0 <= qs < qe
            or not isinstance(qid, str) or not isinstance(qworker, str)
            or not isinstance(calls, list) or len(calls) != 1):
        return errors + ["query_interval_or_identity"]
    call = calls[0]
    if not isinstance(call, dict):
        return errors + ["call_type"]
    cs, ce = call.get("call_start_ns"), call.get("call_end_ns")
    if (type(cs) is not int or type(ce) is not int or not qs <= cs < ce <= qe
            or call.get("kind") != "barrier-blocked-placeholder-no-model"):
        errors.append("placeholder_call_interval")
    arrived, consumed = item.get("arrived_ns"), item.get("consumed_ns")
    start, end = item.get("update_start_ns"), item.get("update_end_ns")
    if (item.get("query_id") != qid or type(arrived) is not int or type(consumed) is not int
            or type(start) is not int or type(end) is not int
            or not qs < arrived <= consumed < qe or not start <= consumed < end):
        errors.append("feedback_interval")
    if item.get("activity_kind") != "barrier-held-empty-critical-section-no-optimizer":
        errors.append("trainer_activity_scope")
    if not isinstance(item.get("trainer_worker_id"), str) or item.get("trainer_worker_id") == qworker:
        errors.append("worker_identity")
    if type(cs) is int and type(ce) is int and type(start) is int and type(end) is int:
        if not (start < ce and cs < end):
            errors.append("no_real_interval_overlap")
    return errors


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: audit_thread_overlap.py RAW_JSON AUDIT_JSON")
    raw_path, output = map(Path, sys.argv[1:])
    if output.exists():
        raise SystemExit("STOP_AUDIT_OUTPUT_EXISTS")
    raw_bytes = raw_path.read_bytes()
    doc = json.loads(raw_bytes, object_pairs_hook=unique_pairs)
    errors = audit(doc)
    result = {"schema": "needle-host-thread-overlap-audit-v1",
              "decision": "PASS_HOST_THREAD_OVERLAP_INSTRUMENTATION_SCOPED" if not errors else "FAIL_BOUNDARY_AUDIT",
              "errors": errors, "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
              "source_scope": "stdlib-independent; no candidate protocol/model/optimizer imports"}
    payload = canonical(result) + b"\n"
    with output.open("xb") as stream:
        stream.write(payload)
    print(json.dumps({"decision": result["decision"], "errors": len(errors),
                      "raw_sha256": result["raw_sha256"],
                      "audit_sha256": hashlib.sha256(payload).hexdigest()}, sort_keys=True))
    raise SystemExit(0 if not errors else 2)


if __name__ == "__main__":
    main()
