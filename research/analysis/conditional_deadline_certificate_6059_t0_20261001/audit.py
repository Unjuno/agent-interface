"""Independent exhaustive trace oracle for Issue #6059 T0.

This module deliberately does not import candidate.py. It reconstructs trace
completion times from the scenario contract and checks certificate soundness.
"""
import argparse
import itertools
import json
from pathlib import Path


def values(bounds):
    lo, hi = bounds
    return range(lo, hi + 1)


def exact_completions(spec):
    kind = spec["kind"]
    if kind == "serial":
        return [sum(row) for row in itertools.product(*(values(b) for b in spec["ranges"]))]
    if kind == "two_queue_burst":
        a1, b1, a2, b2 = [list(values(b)) for b in spec["ranges"]]
        # A and B arrive together to FIFO queue 1; each feeds FIFO queue 2.
        return [x_a1 + max(x_b1, x_a2) + x_b2
                for x_a1, x_b1, x_a2, x_b2 in itertools.product(a1, b1, a2, b2)]
    if kind == "serial_with_interference":
        return [a + b + spec["interference"]
                for a, b in itertools.product(*(values(x) for x in spec["ranges"]))]
    if kind == "timeout_terminal":
        prefix = values(spec["prefix_range"])
        cancellations = values(spec["cancellation_range"])
        return [p + min(runtime, spec["timeout"]) + cancel
                for p, runtime, cancel in itertools.product(prefix, spec["runtime_values"], cancellations)]
    if kind == "unbounded":
        return list(spec["completion_values"])
    raise ValueError(f"unknown exact model: {kind}")


def audit(data, result):
    certs = {row["id"]: row for row in result["certificates"]}
    errors, checked, summaries = [], 0, []
    if result.get("allocation_id") != data.get("allocation_id"):
        errors.append("allocation identity mismatch")
    for case in data["scenarios"]:
        checked += 1
        row = certs.get(case["id"])
        if row is None:
            errors.append(f"missing certificate: {case['id']}")
            continue
        if row["label"] != case["expected"]:
            errors.append(f"{case['id']}: expected {case['expected']}, got {row['label']}")
        completions = exact_completions(case["exact"])
        all_meet = all(t <= case["deadline"] for t in completions)
        all_miss = all(t > case["deadline"] for t in completions)
        if row["label"] == "CERTIFIED_DEADLINE_MET" and not all_meet:
            errors.append(f"unsound MET certificate: {case['id']}; range={min(completions)}..{max(completions)}")
        if row["label"] == "CERTIFIED_DEADLINE_IMPOSSIBLE" and not all_miss:
            errors.append(f"unsound IMPOSSIBLE certificate: {case['id']}; range={min(completions)}..{max(completions)}")
        if row["label"] == "CERTIFIED_DEADLINE_IMPOSSIBLE":
            proof = case.get("sound_lower_bound", {})
            if proof.get("source") != "independent_proof" or proof.get("ticks", 0) <= case["deadline"]:
                errors.append(f"impossibility lacks an independent strict lower bound: {case['id']}")
        summaries.append({"id": case["id"], "label": row["label"], "trace_count": len(completions),
                          "completion_min": min(completions), "completion_max": max(completions),
                          "all_meet": all_meet, "all_miss": all_miss})
    extra = sorted(set(certs) - {c["id"] for c in data["scenarios"]})
    if extra:
        errors.append(f"unexpected certificates: {extra}")
    return {"allocation_id": data["allocation_id"], "disposition": "PASS_METHOD_SCOPED" if not errors else "FAIL_UNSOUND_CERTIFICATE",
            "checked_cases": checked, "errors": errors, "summaries": summaries,
            "scope": "synthetic finite method fixture only; no product/agent-interface latency guarantee"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--certificates", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    certs = json.loads(Path(args.certificates).read_text(encoding="utf-8"))
    report = audit(data, certs)
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"audit {report['disposition']}: {report['checked_cases']} cases; {len(report['errors'])} errors")
    raise SystemExit(0 if not report["errors"] else 1)


if __name__ == "__main__":
    main()
