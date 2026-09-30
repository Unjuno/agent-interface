from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


EXPECTED_POLICIES = {"ROUTE_ONLY", "ACK_ONLY", "TWO_PHASE", "THREE_PHASE", "FAIL_CLOSED_NO_OWNER"}
EXPECTED_SCENARIOS = {
    "nominal", "offer_lost", "target_refuses", "target_crash_before_accept",
    "source_crash_before_accept", "source_crash_after_accept", "target_crash_after_accept",
    "commit_lost", "stale_snapshot", "lease_expiry", "duplicate_accept",
    "human_intervention", "reclaim_after_target_crash",
}


def audit(raw_path: Path) -> dict:
    payload = raw_path.read_bytes()
    raw = json.loads(payload)
    errors = []
    traces = raw.get("traces", [])
    expected_count = len(EXPECTED_POLICIES) * len(EXPECTED_SCENARIOS)
    if len(traces) != expected_count:
        errors.append("row_count")
    keys = {(r.get("policy"), r.get("scenario")) for r in traces}
    expected = {(p, s) for p in EXPECTED_POLICIES for s in EXPECTED_SCENARIOS}
    if keys != expected:
        errors.append("matrix_coverage")

    corrected = []
    for row in traces:
        trace = row.get("trace", [])
        owners = []
        offer = accepted = prepared = quiesced = committed = stale = expired = False
        source_alive = target_alive = True
        human_seen = False
        for index, item in enumerate(trace):
            if item.get("tick") != index:
                errors.append(f"tick_order:{row.get('policy')}:{row.get('scenario')}:{index}")
            current = item.get("owners")
            if not isinstance(current, list) or len(current) != len(set(current)) or not set(current) <= {"source", "target", "human"}:
                errors.append(f"owner_set:{row.get('policy')}:{row.get('scenario')}:{index}")
                current = []
            if "source" in current and item.get("source_alive") is not True:
                errors.append(f"dead_source_owner:{row.get('policy')}:{row.get('scenario')}:{index}")
            if "target" in current and item.get("target_alive") is not True:
                errors.append(f"dead_target_owner:{row.get('policy')}:{row.get('scenario')}:{index}")
            event = item.get("event")
            if event == "request" and row.get("policy") in {"ROUTE_ONLY", "FAIL_CLOSED_NO_OWNER"}:
                quiesced = True
            elif event == "offer_delivered":
                offer = True
            elif event == "target_prepare" and offer and not stale and not expired:
                prepared = True
            elif event in {"target_accept", "target_accept_duplicate"} and offer and not stale and not expired and target_alive:
                accepted = True
            elif event == "target_refuse":
                accepted = prepared = False
            elif event == "source_quiesce":
                quiesced = True
            elif event == "commit_delivered":
                committed = True
            elif event == "source_crash":
                source_alive = False
            elif event == "target_crash":
                target_alive = False
            elif event == "snapshot_stale":
                stale = True
            elif event == "lease_expired":
                expired = True
            elif event == "human_takeover":
                human_seen = True
            elif event == "source_resume":
                if source_alive and not expired and not human_seen:
                    quiesced = committed = False
            if (item.get("source_alive"), item.get("target_alive")) != (source_alive, target_alive):
                errors.append(f"actor_liveness_mismatch:{row.get('policy')}:{row.get('scenario')}:{index}")
            if "source" in current and (not source_alive or expired or "human" in current):
                errors.append(f"invalid_source_responsibility:{row.get('policy')}:{row.get('scenario')}:{index}")
            if "human" in current and not human_seen:
                errors.append(f"unoffered_human_responsibility:{row.get('policy')}:{row.get('scenario')}:{index}")
            if "target" in current:
                policy = row.get("policy")
                eligible = (
                    policy == "ROUTE_ONLY" and offer and target_alive
                    or policy == "ACK_ONLY" and accepted and offer and target_alive and not stale and not expired
                    or policy == "TWO_PHASE" and accepted and quiesced and committed and offer and target_alive and not stale and not expired and "human" not in current
                    or policy == "THREE_PHASE" and accepted and prepared and quiesced and committed and offer and target_alive and not stale and not expired and "human" not in current
                )
                if not eligible:
                    errors.append(f"target_responsibility_before_protocol:{row.get('policy')}:{row.get('scenario')}:{index}")
                if policy == "FAIL_CLOSED_NO_OWNER":
                    errors.append(f"target_under_fail_closed:{row.get('scenario')}:{index}")
            owners.append(set(current))
        gap = sum(not owner for owner in owners)
        duplicate = sum(len(owner) > 1 for owner in owners)
        work_ticks = [i for i, item in enumerate(trace) if item.get("event") == "work"]
        lost = sum(not owners[i] for i in work_ticks)
        false_success = trace[-1].get("false_success_claims", 0) if trace else 0
        if (row.get("authority_gap_ticks"), row.get("duplicate_owner_ticks"), row.get("lost_work"), row.get("false_success_claims")) != (gap, duplicate, lost, false_success):
            errors.append(f"metric_mismatch:{row.get('policy')}:{row.get('scenario')}")
        corrected.append({
            "policy": row.get("policy"), "scenario": row.get("scenario"),
            "authority_gap_ticks": gap, "duplicate_owner_ticks": duplicate,
            "lost_work": lost, "false_success_claims": false_success,
        })

    if not errors and any(r["duplicate_owner_ticks"] for r in corrected if r["policy"] in {"TWO_PHASE", "THREE_PHASE"}):
        disposition = "FAIL_DUPLICATE_OWNER"
    elif not errors and any(r["false_success_claims"] for r in corrected):
        disposition = "FAIL_FALSE_SUCCESS_CLAIM"
    elif errors:
        disposition = "STOP_ORACLE_MISMATCH"
    else:
        by_key = {(r["policy"], r["scenario"]): r for r in corrected}
        selected = ("nominal", "offer_lost", "reclaim_after_target_crash")
        explicit = [by_key[(p, s)]["authority_gap_ticks"] for p in ("TWO_PHASE", "THREE_PHASE") for s in selected]
        fail_closed = [by_key[("FAIL_CLOSED_NO_OWNER", s)]["authority_gap_ticks"] for s in selected]
        if all(a <= b for a, b in zip(explicit, fail_closed)) and any(a < b for a, b in zip(explicit, fail_closed)):
            disposition = "PASS_HANDOFF_BOUNDARIES_SCOPED"
        else:
            disposition = "HOLD_NO_DISTINGUISHING_VALUE"
    recorded = raw.get("summary", {})
    if recorded.get("rows") != len(traces) or recorded.get("disposition") != disposition:
        errors.append("summary_mismatch")
        disposition = "STOP_ORACLE_MISMATCH"
    return {
        "status": disposition, "errors": errors,
        "trace_count": len(traces), "raw_bytes": len(payload),
        "raw_sha256": hashlib.sha256(payload).hexdigest(),
        "oracle_metrics": corrected,
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m research.analysis.adjustable_autonomy_handoff_5324_t0_v1.audit RAW_JSON")
    result = audit(Path(sys.argv[1]))
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if not result["errors"] else 1)
