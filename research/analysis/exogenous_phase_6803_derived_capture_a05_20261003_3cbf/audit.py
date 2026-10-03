"""Standalone finite-set oracle. Imports no candidate, prepare or legacy code."""
import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def frozen_fixture():
    # Independently spell out the frozen protocol and finite cell domain.
    rows = []
    settings = {"capture_schedule_ms": [10, 50], "observation_horizon_ms": 60,
                "clock_synchronized": True, "delivery_latency_ms": 1,
                "decision_latency_ms": 1, "effect_latency_ms": 0,
                "effect_enabled": True, "safe_stop": False}
    intervals = [(20, 21), (51, 52), (60, 61)]
    for expiry, count in intervals:
        for onset in range(count):
            rows.append(dict(settings, case_id=f"grid-e{expiry}-o{onset:02}",
                             opportunity={"onset_ms": onset, "expiry_ms": expiry}))
    controls = [
        ("control-no-cue", None, {}),
        ("control-unsynced", (9, 20), {"clock_synchronized": False}),
        ("control-late-delivery", (9, 20), {"delivery_latency_ms": 11}),
        ("control-late-decision", (9, 20), {"decision_latency_ms": 10}),
        ("control-no-effect", (9, 20), {"effect_enabled": False}),
        ("control-safe-stop", (9, 20), {"safe_stop": True}),
        ("control-right-censor", (9, 20), {"observation_horizon_ms": 15, "effect_latency_ms": 10}),
        ("control-late-effect", (9, 20), {"effect_latency_ms": 10}),
        ("control-before-capture", (9, 20), {"observation_horizon_ms": 9}),
        ("control-expiry-equality", (9, 10), {}),
        ("control-zero-latency", (10, 10), {"delivery_latency_ms": 0, "decision_latency_ms": 0}),
        ("duration-hit", (9, 11), {"delivery_latency_ms": 0, "decision_latency_ms": 0}),
        ("duration-miss", (11, 13), {"delivery_latency_ms": 0, "decision_latency_ms": 0}),
    ]
    for identity, interval, changes in controls:
        cue = None if interval is None else dict(zip(("onset_ms", "expiry_ms"), interval))
        rows.append(dict(settings, case_id=identity, opportunity=cue, **changes))
    return {"schema": "derived-capture-input-v1", "fixture_id": "FIXTURE-6969-A05-3CBF", "cases": rows}


def expected_row(c):
    cue, end = c["opportunity"], c["observation_horizon_ms"]
    active_times = set() if cue is None or not c["clock_synchronized"] else set(range(cue["onset_ms"], cue["expiry_ms"] + 1))
    observed_times = set(range(end + 1))
    samples = sorted(set(c["capture_schedule_ms"]) & active_times & observed_times)
    d = q = e = s = None
    if samples:
        proposed = min(samples) + c["delivery_latency_ms"]
        d = proposed if proposed in observed_times else None
    if d in active_times:
        proposed = d + c["decision_latency_ms"]
        q = proposed if proposed in observed_times else None
    if q in active_times:
        s = q if c["safe_stop"] else None
        proposed = q + c["effect_latency_ms"]
        if s is None and c["effect_enabled"] and proposed in observed_times:
            e = proposed
    branches = [
        (cue is None, "NOT_APPLICABLE", "no_exogenous_opportunity"),
        (not c["clock_synchronized"], "UNKNOWN", "clock_unsynced"),
        (cue is not None and end < cue["expiry_ms"] and e is None and s is None, "UNKNOWN", "right_censored"),
        (not samples, "not_acquired", "no_capture_in_closed_interval"),
        (d not in active_times, "acquired_not_delivered", "no_timely_delivery_observed"),
        (q not in active_times, "delivered_no_decision", "no_timely_decision_observed"),
        (s is not None, "decision_no_effect", "safe_stop"),
        (e is not None, "eligible_effect_in_model", "simulated_effect_observed"),
        (True, "decision_no_effect", "no_simulated_effect_observed"),
    ]
    _, boundary, reason = next(branch for branch in branches if branch[0])
    return {"case_id": c["case_id"], "opportunity": cue,
            "capture_schedule_ms": c["capture_schedule_ms"], "observation_horizon_ms": end,
            "sampled_capture_ms": samples, "stages_ms": {"delivery": d, "decision": q, "effect": e, "safe_stop": s},
            "boundary": boundary, "reason": reason,
            "simulated_effect_token": None if e is None else "simulated:" + c["case_id"]}


def errors(fixture, raw):
    if canonical(fixture) != canonical(frozen_fixture()):
        return ["fixture_contract_mismatch"]
    expected = {"schema": "derived-capture-raw-v1", "fixture_id": fixture["fixture_id"],
                "authority_events": 0, "live_effect_events": 0,
                "rows": [expected_row(c) for c in fixture["cases"]]}
    failures = []
    if type(raw) is not dict or set(raw) != set(expected):
        return ["raw_schema_mismatch"]
    for key in ("schema", "fixture_id", "authority_events", "live_effect_events"):
        if canonical(raw[key]) != canonical(expected[key]):
            failures.append(key + "_mismatch")
    rows = raw["rows"]
    if type(rows) is not list or len(rows) != 147:
        failures.append("row_count_mismatch")
    if type(rows) is list:
        for index, (observed, wanted) in enumerate(zip(rows, expected["rows"])):
            if canonical(observed) != canonical(wanted):
                failures.append("row_mismatch:" + str(index))
    return failures


def mutants(raw):
    variants = []
    changes = [
        ("drop-row", lambda r: r["rows"].pop()),
        ("duplicate-row", lambda r: r["rows"].__setitem__(1, copy.deepcopy(r["rows"][0]))),
        ("wrong-phase-verdict", lambda r: r["rows"][11].__setitem__("boundary", "eligible_effect_in_model")),
        ("forged-capture", lambda r: r["rows"][11].__setitem__("sampled_capture_ms", [10])),
        ("shifted-source-echo", lambda r: r["rows"][9]["opportunity"].__setitem__("onset_ms", 11)),
        ("altered-schedule", lambda r: r["rows"][9].__setitem__("capture_schedule_ms", [11, 50])),
        ("wrong-decision-time", lambda r: r["rows"][9]["stages_ms"].__setitem__("decision", 13)),
        ("forged-effect-token", lambda r: r["rows"][11].__setitem__("simulated_effect_token", "simulated:forged")),
        ("boolean-time-alias", lambda r: r["rows"][0]["stages_ms"].__setitem__("delivery", True)),
        ("authority-claim", lambda r: r.__setitem__("authority_events", 1)),
    ]
    for name, change in changes:
        value = copy.deepcopy(raw)
        change(value)
        variants.append((name, value))
    return variants


def legacy_errors(result):
    expected_hashes = {
        "candidate.py": "c1e39ebd99e1eee81dbac6902d6d71b03ba1deb872bec8753c22372f270c6d29",
        "fixture.json": "2b3c934bef9dfdb9ea0b758521570bf8ee5d3878e2008d9b9702c9a1a371919e"}
    base = {"capture_schedule_ms": [10, 50], "observation_horizon_ms": 60,
            "opportunity": {"onset_ms": 9, "expiry_ms": 20}, "clock_synchronized": True,
            "captures": [{"at_ms": 10, "opportunity_ids": ["o01"]}, {"at_ms": 50, "opportunity_ids": []}],
            "case_id": "c01", "opportunity_id": "o01", "delivery_ms": 11, "decision_ms": 12,
            "effect_receipt_id": "r01", "safe_stop_ms": None}
    expected_rows = []
    for identity, onset in (("c01", 9), ("c01", 11), ("c02", 11), ("c02", 9)):
        item = copy.deepcopy(base)
        item["opportunity"]["onset_ms"] = onset
        if identity == "c02":
            item.update(case_id="c02", opportunity_id="o02", delivery_ms=None,
                        decision_ms=None, effect_receipt_id=None)
            item["captures"][0]["opportunity_ids"] = []
        expected_rows.append({"probe_id": f"{identity}-onset-{onset}", "input": item,
                              "output": ["eligible_effect", "verified_effect", "r01"] if identity == "c01"
                              else ["not_acquired", "no_capture_before_expiry", None]})
    wanted = {"schema": "legacy-onset-probe-v1", "source_sha256": expected_hashes,
              "rows": expected_rows, "authority_events": 0, "live_effect_events": 0}
    return [] if canonical(result) == canonical(wanted) else ["legacy_onset_probe_mismatch"]


def audit(fixture, raw, legacy):
    failures = errors(fixture, raw) + legacy_errors(legacy)
    controls = []
    copies = []
    for name, mutated in mutants(raw):
        rejection = errors(fixture, mutated)
        controls.append({"name": name, "rejected": bool(rejection), "errors": rejection,
                         "sha256": hashlib.sha256((canonical(mutated) + "\n").encode()).hexdigest()})
        copies.append({"name": name, "raw": mutated})
        if not rejection:
            failures.append("mutation_accepted:" + name)
    rows = {r["case_id"]: r for r in raw["rows"]}
    contrasts = {"onset_only": [rows[k]["boundary"] for k in ("grid-e20-o09", "grid-e20-o11")],
                 "fixed_duration": [rows[k]["boundary"] for k in ("duration-hit", "duration-miss")]}
    if any(v != ["eligible_effect_in_model", "not_acquired"] for v in contrasts.values()):
        failures.append("matched_contrast_mismatch")
    return {"schema": "derived-capture-audit-v1", "status": "FAIL_AUDIT" if failures else "PASS_METHOD_SCOPED",
            "errors": failures, "rows_checked": len(raw["rows"]), "grid_cells": 134, "controls": 13,
            "boundary_counts": dict(sorted(Counter(r["boundary"] for r in raw["rows"]).items())),
            "matched_contrasts": contrasts, "legacy_probe_inputs": len(legacy["rows"]),
            "legacy_onset_only_pairs_insensitive": 2 if not legacy_errors(legacy) else 0,
            "mutation_controls": controls, "authority_events": 0, "live_effect_events": 0}, copies


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ("fixture", "raw", "legacy", "out", "mutations-out"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    report, copies = audit(*(json.loads(Path(p).read_text()) for p in (args.fixture, args.raw, args.legacy)))
    for path, value in ((args.out, report), (args.mutations_out, copies)):
        with Path(path).open("x") as target:
            json.dump(value, target, sort_keys=True, indent=2)
            target.write("\n")
    print(report["status"], "rows=" + str(report["rows_checked"]),
          "mutations_rejected=" + str(sum(c["rejected"] for c in report["mutation_controls"])))
    raise SystemExit(1 if report["errors"] else 0)
