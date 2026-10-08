#!/usr/bin/env python3
"""Independent raw-only audit; deliberately does not import candidate.py."""
import hashlib
import json
import pathlib
import sys

SCENARIOS = ("no_aging", "monotone_leak", "cache_plateau", "thermal_only", "hidden_state")
POLICIES = ("NEVER", "FIXED_AGE_10", "RESOURCE_THRESHOLD_112")


def expected_metrics(scenario, age, index):
    rss, latency = 100, 20.0
    if scenario == "monotone_leak":
        rss, latency = 100 + 2 * age, 20.0 + age
    if scenario == "cache_plateau":
        rss = 100 + 3 * min(age, 8)
    if scenario == "thermal_only":
        latency = 20.0 + 0.5 * max(0, index - 10)
    return rss, latency


def independently_detect(rows):
    groups = {}
    for row in rows:
        groups.setdefault(row["generation_before"], []).append(row)
    for group in groups.values():
        group.sort(key=lambda r: r["age_before"])
        if len(group) < 2:
            continue
        a, b = group[0], group[-1]
        if (b["age_before"] - a["age_before"] >= 4 and
                b["rss_mb"] - a["rss_mb"] >= 8 and
                b["latency_ms"] - a["latency_ms"] >= 4):
            return True
    return False


def audit(raw, scenario_bytes):
    errors = []
    if raw.get("schema") != "worker-aging-t1c-raw-v1":
        errors.append("schema")
    if raw.get("scenario_sha256") != hashlib.sha256(scenario_bytes).hexdigest():
        errors.append("scenario_hash")
    cells = raw.get("cells")
    if not isinstance(cells, list) or len(cells) != 15:
        return ["cell_count"]
    observed = {(c.get("scenario"), c.get("policy")): c for c in cells}
    if set(observed) != {(s, p) for s in SCENARIOS for p in POLICIES}:
        errors.append("cell_keys")
        return errors
    for scenario in SCENARIOS:
        for policy in POLICIES:
            cell = observed[(scenario, policy)]
            rows = cell.get("rows")
            if not isinstance(rows, list) or len(rows) != 40:
                errors.append(f"rows:{scenario}:{policy}")
                continue
            generation, age = 1, 0
            restart_count = deferred_count = mismatch_count = 0
            for i, row in enumerate(rows):
                prefix = f"{scenario}:{policy}:{i}"
                rss, latency = expected_metrics(scenario, age, i)
                pending = ["effect-10"] if i in (10, 11, 12) else []
                due = ((policy == "FIXED_AGE_10" and age >= 10) or
                       (policy == "RESOURCE_THRESHOLD_112" and rss >= 112))
                decision = ("not_due" if not due else
                            "deferred_pending_obligation" if pending else "committed_restart")
                restart = decision == "committed_restart"
                want_late = None if not restart else {
                    "receipt_generation": generation,
                    "current_generation": generation + 1,
                    "accepted": False,
                    "reason": "stale_generation",
                }
                expected_output = f"answer-{i}"
                observed_output = "stale-prior-request-marker" if scenario == "hidden_state" and i == 7 else expected_output
                checks = {
                    "job_index": i,
                    "generation_before": generation,
                    "age_before": age,
                    "rss_mb": rss,
                    "latency_ms": latency,
                    "host_temp_c": 30.0 + (max(0, i - 10) if scenario == "thermal_only" else 0),
                    "pending_obligation_ids": pending,
                    "restart_due": due,
                    "restart_decision": decision,
                    "generation_after": generation + int(restart),
                    "age_after": 0 if restart else age + 1,
                    "late_receipt": want_late,
                    "expected_output": expected_output,
                    "observed_output": observed_output,
                    "output_mismatch": observed_output != expected_output,
                }
                for key, expected in checks.items():
                    if row.get(key) != expected:
                        errors.append(f"{prefix}:{key}")
                restart_count += int(restart)
                deferred_count += int(decision == "deferred_pending_obligation")
                mismatch_count += int(observed_output != expected_output)
                generation += int(restart)
                age = 0 if restart else age + 1
            detected = independently_detect(rows)
            should_detect = scenario == "monotone_leak"
            if cell.get("aging_detected") is not should_detect or detected is not should_detect:
                errors.append(f"aging:{scenario}:{policy}")
            if cell.get("restart_count") != restart_count:
                errors.append(f"restart_count:{scenario}:{policy}")
            if cell.get("deferred_count") != deferred_count:
                errors.append(f"deferred_count:{scenario}:{policy}")
            if cell.get("output_mismatch_count") != mismatch_count:
                errors.append(f"output_mismatch_count:{scenario}:{policy}")
            if mismatch_count != int(scenario == "hidden_state"):
                errors.append(f"hidden_state_gate:{scenario}:{policy}")
    return errors


def main(raw_path):
    package = pathlib.Path(__file__).parent
    raw = json.loads(pathlib.Path(raw_path).read_text(encoding="utf-8"))
    errors = audit(raw, (package / "scenario.json").read_bytes())
    result = {"status": "PASS_METHOD_SCOPED" if not errors else "METHOD_FAIL", "errors": errors, "cells": 15, "rows": 600}
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: audit.py RAW_JSON")
    main(sys.argv[1])
