#!/usr/bin/env python3
"""Post-hoc re-audit retained #4732 raw; does not modify/re-run frozen auditor."""
import argparse
import importlib.util
import json
import math
from pathlib import Path
import sys


def load_frozen_audit(path):
    spec = importlib.util.spec_from_file_location("frozen_audit_4732", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def summarize(audit, obj):
    stages = {}
    for mode in audit.MODES:
        rows = obj["arms"][mode]
        stage = {"ack_p95_ms": audit.p95([r["ack_elapsed_ns"] for r in rows]),
                 "update_p95_ms": audit.p95([r["ack"]["update_ns"] for r in rows]),
                 "commit_p95_ms": audit.p95([r["ack"]["commit_ns"] for r in rows]),
                 "full_batch_p95_ms": audit.p95([
                     (r["ack"].get("full_prediction_ns") if mode == "INLINE_512"
                      else r["post_ack_audit"]["full_prediction_ns"]) for r in rows])}
        if mode == "ONLINE_QUERY_ONLY":
            stage["single_query_p95_ms"] = audit.p95(
                [r["ack"]["one_prediction_ns"] for r in rows])
        stages[mode] = stage
    ratio = stages["ONLINE_QUERY_ONLY"]["ack_p95_ms"] / stages["INLINE_512"]["ack_p95_ms"]
    return {"seed": obj["seed"], "arm_order": obj["arm_order"],
            "inline_512": stages["INLINE_512"],
            "online_query_only": stages["ONLINE_QUERY_ONLY"],
            "ratio": ratio,
            "query_only_total_elapsed_ms": obj["arm_total_elapsed_ns"]["ONLINE_QUERY_ONLY"] / 1e6,
            "inline_total_elapsed_ms": obj["arm_total_elapsed_ns"]["INLINE_512"] / 1e6}


def audit(raw, volume, frozen_audit, seeds):
    checked = []
    errors = []
    for seed in seeds:
        try:
            report = json.loads((Path(raw) / str(seed) / "run.json").read_text(encoding="utf-8"))
            frozen_audit.validate_report(report, seed, volume)
            checked.append(summarize(frozen_audit, report))
        except Exception as exc:
            errors.append({"seed": seed, "error": f"{type(exc).__name__}:{exc}"})
    controls = frozen_audit.corruption_controls(seeds[0])
    gates = {"integrity_valid": not errors and len(checked) == len(seeds),
             "corruption_controls_rejected": all(controls.values()),
             "per_seed_latency_gate": all(
                 row["online_query_only"]["ack_p95_ms"] <= 60 and row["ratio"] <= .5
                 for row in checked) if checked else False}
    decision = ("POSTHOC_HOLD_LATENCY_BUDGET" if gates["integrity_valid"] and
                gates["corruption_controls_rejected"] and not gates["per_seed_latency_gate"]
                else "POSTHOC_PASS_SCOPED" if all(gates.values())
                else "POSTHOC_FAIL_INTEGRITY")
    return {"schema": "needle-single-query-ack-posthoc-audit-v1",
            "allocation": frozen_audit.ALLOCATION, "status": decision,
            "pre_registered_formal_verdict": None,
            "notice": "Post-hoc independent replay; does not replace the frozen auditor STOP or constitute a pre-registered formal verdict.",
            "seeds": checked, "gates": gates, "corruption_controls": controls,
            "errors": errors}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--raw", required=True)
    p.add_argument("--volume", required=True)
    p.add_argument("--frozen-audit", required=True)
    p.add_argument("--baseline", required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args()
    sys.path.insert(0, str(Path(a.baseline).parent))
    frozen = load_frozen_audit(a.frozen_audit)
    result = audit(a.raw, a.volume, frozen, frozen.FORMAL_SEEDS)
    out = Path(a.out) / "POSTHOC_AUDIT.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "gates": result["gates"],
                      "errors": len(result["errors"])}, sort_keys=True), flush=True)
    if result["errors"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
