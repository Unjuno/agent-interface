"""Independent event-log reconstruction; imports no candidate code."""
import json
import math
import sys


def main(path):
    raw = json.load(open(path, encoding="utf-8"))
    rows = raw["rows"]
    groups = {}
    for r in rows:
        key = (r["topology"], r["seed"], r["imitation"], r["capacity"], r["mode"])
        groups.setdefault(key, []).append({k: v for k, v in r.items() if k not in ("topology", "seed", "imitation", "capacity", "mode")})
    summaries = {}
    errors = []
    for key, events in groups.items():
        opp = [e for e in events if e["type"] == "opportunity"]
        arrivals = {e["id"]: e for e in events if e["type"] == "arrival"}
        starts = {e["id"]: e["tick"] for e in events if e["type"] == "service_start"}
        done = {e["id"]: e for e in events if e["type"] == "completion"}
        unfinished = {e["id"]: e["state"] for e in events if e["type"] == "unfinished"}
        if len(opp) != 160 * 24:
            errors.append(f"{key}: opportunity_denominator={len(opp)}")
        if set(arrivals) != set(starts) | set(unfinished) or set(starts) != set(done) | set(unfinished):
            errors.append(f"{key}: task_accounting_mismatch")
        latencies = []
        for jid, comp in done.items():
            job = arrivals.get(jid)
            if not job or comp["tick"] - job["arrival"] != comp["latency"]:
                errors.append(f"{key}: completion_latency_mismatch:{jid}")
            if jid not in starts or starts[jid] < job["arrival"]:
                errors.append(f"{key}: invalid_service_start:{jid}")
            latencies.append(comp["latency"])
        for tick in range(160):
            if sum(e["tick"] == tick for e in opp) != 24:
                errors.append(f"{key}: per_tick_opportunity:{tick}")
                break
        latencies.sort()
        p95 = latencies[math.ceil(0.95 * len(latencies)) - 1] if latencies else None
        starts_count = sum(e["started"] for e in opp)
        adopted = sum(e["adopted"] for e in opp if e["tick"] == 159)
        summaries[key] = {"opportunities": len(opp), "started": starts_count,
                          "completed": len(done), "unfinished": len(unfinished),
                          "adopters_final": adopted, "p95_latency": p95,
                          "interaction_cost_per_started_task": 6 if key[4] != "baseline_frozen" else 10,
                          "event_count": len(events)}
    def get(top, seed, imi, cap, mode):
        return summaries[(top, seed, imi, cap, mode)]
    reversals = []
    for top in ("ring", "star"):
        for seed in (11, 29, 47, 83):
            for imi in (0.08, 0.2):
                peer = get(top, seed, imi, 1, "reduced_peer")["p95_latency"]
                frozen = get(top, seed, imi, 1, "reduced_frozen")["p95_latency"]
                if peer is not None and frozen is not None and peer > frozen:
                    reversals.append((top, seed, imi))
    controls = {"no_imitation": 0, "partitioned": 0, "nonbinding": 0}
    for top in ("ring", "star"):
        for seed in (11, 29, 47, 83):
            imi = 0.08
            base = get(top, seed, imi, 1, "reduced_frozen")["p95_latency"]
            for label, mode, cap in (("no_imitation", "reduced_no_imitation", 1),
                                     ("partitioned", "reduced_partitioned", 1),
                                     ("nonbinding", "reduced_nonbinding", 1)):
                val = get(top, seed, imi, cap, mode)["p95_latency"]
                if val is not None and base is not None and val > base:
                    controls[label] += 1
    status = "METHOD_PASS_SCOPED" if not errors and len(reversals) >= 12 and not any(controls.values()) else ("NO_REVERSAL_IN_GRID" if not reversals and not errors else "METHOD_FAIL_OR_INCONCLUSIVE")
    json.dump({"status": status, "errors": errors, "groups": len(summaries),
               "reversal_cells": [list(x) for x in reversals], "control_reversal_counts": controls,
               "summary": [{"key": list(k), **v} for k, v in sorted(summaries.items())]},
              sys.stdout, sort_keys=True, separators=(",", ":"))


if __name__ == "__main__":
    main(sys.argv[1])
