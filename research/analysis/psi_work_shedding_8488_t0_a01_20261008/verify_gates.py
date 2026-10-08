#!/usr/bin/env python3
"""Checks the frozen output against protocol-level conservation/specificity gates."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    cfg = json.loads((ROOT / "inputs.json").read_text())
    raw = json.loads((ROOT / "RAW_RESULT.json").read_text())
    checks = {}
    checks["complete_factorial"] = len(raw["rows"]) == len(cfg["traces"]) * len(cfg["policies"])
    checks["mandatory_conservation"] = True
    checks["evidence_conservation"] = True
    for trace in cfg["traces"]:
        for row in (r for r in raw["rows"] if r["trace"] == trace["id"]):
            ids = {j["id"] for j in trace["arrivals"]}
            results = row["jobs"]
            if ids != set(results):
                checks["mandatory_conservation"] = False
            for job in trace["arrivals"]:
                result = results.get(job["id"], {})
                if job["class"] in cfg["mandatory_classes"]:
                    if result.get("evidence_id") != job["evidence_id"] or job["evidence_id"] not in row["retained_evidence_ids"]:
                        checks["evidence_conservation"] = False
                    if result.get("remaining", 0) > 0 and result.get("completed_at") is not None:
                        checks["mandatory_conservation"] = False
                    if result.get("remaining", 0) == 0 and result.get("completed_at") is None:
                        checks["mandatory_conservation"] = False
    for trace_id in ("short_memory_spike", "unrelated_cpu_io_pressure", "psi_unavailable", "repeated_short_spikes"):
        row = next(r for r in raw["rows"] if r["trace"] == trace_id and r["policy"] == "psi_memory")
        checks[f"no_psi_shedding_{trace_id}"] = not row["transitions"]
    primary = {r["policy"]: r for r in raw["rows"] if r["trace"] == "memory_burst_primary"}
    checks["psi_beats_fixed_primary"] = len(primary["psi_memory"]["deadline_misses"]) < len(primary["fixed_concurrency"]["deadline_misses"])
    checks["psi_beats_queue_primary"] = len(primary["psi_memory"]["deadline_misses"]) < len(primary["queue_deadline"]["deadline_misses"])
    checks["psi_zero_primary_misses"] = not primary["psi_memory"]["deadline_misses"]
    backlog = next(r for r in raw["rows"] if r["trace"] == "recovered_memory_backlog" and r["policy"] == "psi_memory")
    checks["backlog_latch_preserves_mandatory"] = all(
        not (step["tick"] == 8 and not step["shed"] and step["mandatory_waiting"] > 0)
        for step in backlog["timeline"]
    )
    out = {"checks": checks, "passed": sum(checks.values()), "total": len(checks)}
    (ROOT / "GATE_RESULT.json").write_text(json.dumps(out, indent=2, sort_keys=True)+"\n")
    print(json.dumps(out, sort_keys=True))
    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
