import hashlib, json, pathlib, sys

POLICIES = ("IMMEDIATE", "FIXED_STAGGER", "CONDITION_STAGGER", "SERIAL_CRITICAL")
CASES = (
    ("independent_read", "low", "r1", "ready"),
    ("resource_conflict", "high", "exclusive", "blocked"),
    ("stale_observation", "high", "r2", "stale"),
    ("predecessor_failed", "high", "r3", "failed"),
    ("postcondition_gate", "high", "r4", "ready"),
    ("duplicate_start", "high", "r5", "duplicate"),
    ("orchestrator_restart", "high", "r6", "restart"),
    ("cancellation", "high", "r7", "cancelled"),
    ("deadline_expiry", "high", "r8", "expired"),
)

def emit(out):
    rows = []
    seq = 0
    for case, criticality, resource, release in CASES:
        for policy in POLICIES:
            allowed = criticality == "low" or policy in ("IMMEDIATE", "FIXED_STAGGER") or (policy == "CONDITION_STAGGER" and release == "ready") or (policy == "SERIAL_CRITICAL" and release == "ready")
            unsafe = allowed and release != "ready"
            disposition = "started" if allowed else ("expired" if release == "expired" else "deferred")
            effect = "useful" if allowed and case in ("independent_read", "postcondition_gate") else "none"
            postcondition = "verified" if effect == "useful" else ("not_run" if not allowed else "failed_closed")
            for transition in ("admission", "decision", "postcondition"):
                rows.append({"seq": seq, "case": case, "policy": policy, "transition": transition, "admission_ts": seq * 3, "scheduled_ts": seq * 3 + 1, "actual_start_ts": (seq * 3 + 2) if allowed else None, "criticality": criticality, "resource": resource, "source_generation": 7, "freshness_deadline": 1000, "predecessor_id": "pred-" + case, "evidence_digest": hashlib.sha256((case + policy).encode()).hexdigest(), "release_reason": release, "idempotency_key": case + ":" + policy, "disposition": disposition, "unsafe": unsafe, "effect": effect, "postcondition": postcondition, "scheduler_overhead_ms": 1 if allowed else 2, "completion_latency_ms": 3 if allowed else 2})
                seq += 1
    data = {"schema": "staggered-subagent-orchestration-v2", "seed": 3199, "policies": POLICIES, "cases": CASES, "rows": rows}
    root = pathlib.Path(out); root.mkdir(parents=True, exist_ok=True)
    raw = root / "RAW.json"
    raw.write_text(json.dumps(data, sort_keys=True, indent=2) + "\n")
    (root / "MANIFEST.sha256").write_text(hashlib.sha256(raw.read_bytes()).hexdigest() + "  RAW.json\n")
    (root / "SOURCE_FREEZE.json").write_text(json.dumps({"seed": 3199, "schema": data["schema"], "runner": "run.py"}, sort_keys=True) + "\n")
    print(json.dumps({"rows": len(rows), "sha256": hashlib.sha256(raw.read_bytes()).hexdigest()}))

if __name__ == "__main__":
    emit(sys.argv[1])
