"""Independent raw-only reconstruction for Issue #5776 T0; imports no candidate."""
from __future__ import annotations

import copy
import hashlib
import json
import math
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT / "fixture.json"
EXPECTED_MECHANISMS = {"gradual_slowing", "abrupt_breaker", "stable_null", "load_drift"}


def reference_opportunity(mechanism: str, episode: int, opportunity: int) -> dict:
    phase = episode % 4
    capacity_loss = max(0, opportunity // 2 + phase - 1) if mechanism == "gradual_slowing" else 0
    demand_shift = max(0, opportunity // 2 + phase - 1) if mechanism == "load_drift" else 0
    pre = 8 - capacity_loss - demand_shift
    if mechanism == "abrupt_breaker" and opportunity >= 6:
        pre = 0
    loss = pre <= 0
    unknown = mechanism == "abrupt_breaker" and opportunity >= 6
    recovery = None if unknown else (1 if loss else 1 + (capacity_loss if mechanism == "gradual_slowing" else 0))
    return {"episode_id": episode, "mechanism": mechanism, "opportunity": opportunity,
            "capacity_loss": capacity_loss, "demand_shift": demand_shift,
            "pre_disturbance_margin": pre, "disturbance_units": 1,
            "post_disturbance_margin": pre - 1, "recovery_ticks": recovery,
            "return_status": "UNKNOWN" if unknown else "RETURNED", "service_loss": loss}


def reference_episode(mechanism: str, episode: int, fixture: dict, threshold: float | None) -> dict:
    rows = [reference_opportunity(mechanism, episode, op)
            for op in range(fixture["opportunities_per_episode"])]
    known = [r["recovery_ticks"] for r in rows if r["recovery_ticks"] is not None]
    stat = statistics.median(known) if known else None
    return {"episode_id": episode, "mechanism": mechanism,
            "partition": "calibration" if episode in fixture["calibration_episode_ids"] else "heldout",
            "opportunities": rows, "episode_recovery_median": stat,
            "service_loss": any(r["service_loss"] for r in rows),
            "has_unknown_return": any(r["return_status"] == "UNKNOWN" for r in rows),
            "sentinel_statistic": stat,
            "warning": stat is not None and threshold is not None and stat > threshold}


def nearest_rank(values: list[float], q: float) -> float:
    return sorted(values)[math.ceil(q * len(values)) - 1]


def reconstruct(doc: dict, fixture: dict) -> list[str]:
    errors = []
    calibration = []
    for mech in sorted(EXPECTED_MECHANISMS):
        for eid in fixture["calibration_episode_ids"]:
            base = reference_episode(mech, eid, fixture, None)
            if mech == "gradual_slowing" and base["sentinel_statistic"] is not None:
                calibration.append(base["sentinel_statistic"])
    threshold = nearest_rank(calibration, fixture["test_threshold_quantile"])
    wanted = [reference_episode(mech, eid, fixture, threshold)
              for mech in sorted(EXPECTED_MECHANISMS)
              for eid in range(fixture["episodes_per_mechanism"])]
    actual = doc.get("episodes")
    if not isinstance(actual, list) or len(actual) != len(wanted):
        return ["episode_inventory"]
    if doc.get("episode_count") != len(wanted):
        errors.append("episode_count")
    if doc.get("opportunity_count") != len(wanted) * fixture["opportunities_per_episode"]:
        errors.append("opportunity_count")
    if doc.get("threshold") != threshold:
        errors.append("threshold_reconstruction")
    by_key = {}
    for row in actual:
        if not isinstance(row, dict):
            errors.append("episode_shape")
            continue
        key = (row.get("mechanism"), row.get("episode_id"))
        if key in by_key:
            errors.append("duplicate_episode")
        by_key[key] = row
    for expected in wanted:
        key = (expected["mechanism"], expected["episode_id"])
        if by_key.get(key) != expected:
            errors.append("episode_reconstruction:" + str(key))
    test = [r for r in wanted if r["partition"] == "heldout"]
    valid = {m: [r for r in test if r["mechanism"] == m and not r["has_unknown_return"]]
             for m in EXPECTED_MECHANISMS}
    warned = {m: sum(bool(r["warning"]) for r in valid[m]) for m in EXPECTED_MECHANISMS}
    gradual_sensitivity = warned["gradual_slowing"] / len(valid["gradual_slowing"])
    false_alarm = {m: warned[m] / len(valid[m]) if valid[m] else None
                   for m in EXPECTED_MECHANISMS if m != "gradual_slowing"}
    # Abrupt-breaker episodes whose return is UNKNOWN stay visible and cannot be
    # silently scored as negatives; the separate known pre-break opportunities
    # are retained at row level. Synthetic criterion requires no false gradual
    # alert on the known-return abrupt episodes.
    known_abrupt = [r for r in test if r["mechanism"] == "abrupt_breaker"
                    and not r["has_unknown_return"]]
    abrupt_warning = sum(bool(r["warning"]) for r in known_abrupt)
    if gradual_sensitivity < 0.75:
        errors.append("heldout_gradual_sensitivity_gate")
    if any(v is not None and v > 0.10 for v in false_alarm.values()):
        errors.append("heldout_false_alarm_gate")
    if abrupt_warning:
        errors.append("abrupt_control_warning")
    summary = {"heldout_gradual_sensitivity": gradual_sensitivity,
               "heldout_false_alarm_rates_known_return": false_alarm,
               "heldout_abrupt_unknown_episode_count": sum(r["has_unknown_return"] for r in test if r["mechanism"] == "abrupt_breaker"),
               "heldout_abrupt_known_warning_count": abrupt_warning}
    if doc.get("summary") != summary:
        errors.append("summary_reconstruction")
    expected_disposition = "PASS_METHOD_SCOPED" if not errors and gradual_sensitivity >= 0.75 and all(
        v is None or v <= 0.10 for v in false_alarm.values()) and abrupt_warning == 0 else "FAIL_METHOD"
    if doc.get("method_disposition") != expected_disposition:
        errors.append("method_disposition_reconstruction")
    return sorted(set(errors))


def mutation_results(doc: dict, fixture: dict) -> list[dict]:
    mutations = [
        ("drop_no_loss_episode", lambda d: d["episodes"].pop(0)),
        ("drop_abrupt_failure_episode", lambda d: d["episodes"].pop(next(i for i, r in enumerate(d["episodes"]) if r["mechanism"] == "abrupt_breaker" and r["service_loss"]))),
        ("alter_disturbance_schedule", lambda d: d["episodes"][0]["opportunities"][0].update(disturbance_units=2)),
        ("forge_test_threshold", lambda d: d.update(threshold=d["threshold"] + 10)),
        ("recode_unknown_return_as_success", lambda d: None),
        ("duplicate_episode", lambda d: d["episodes"].__setitem__(-1, copy.deepcopy(d["episodes"][0]))),
    ]
    results = []
    for name, mutate in mutations:
        altered = copy.deepcopy(doc)
        try:
            mutate(altered)
            # Dedicated unknown-endpoint mutation, written explicitly because the
            # malformed-input path must not accidentally mutate a boolean value.
            if name == "recode_unknown_return_as_success":
                target = next(r for r in altered["episodes"] if r["has_unknown_return"])
                target["has_unknown_return"] = False
                next(r for r in target["opportunities"] if r["return_status"] == "UNKNOWN").update(
                    return_status="RETURNED", recovery_ticks=1)
            rejected = bool(reconstruct(altered, fixture))
        except Exception:
            rejected = True
        results.append({"name": name, "rejected": rejected})
    return results


def main() -> None:
    raw_bytes = Path(sys.argv[1]).read_bytes()
    doc = json.loads(raw_bytes)
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    errors = reconstruct(doc, fixture)
    controls = mutation_results(doc, fixture)
    if not all(c["rejected"] for c in controls):
        errors.append("mutation_escaped")
    method_disposition = doc.get("method_disposition") if not errors else "NOT_EVALUATED"
    result = {"schema": "issue5776-recovery-rate-t0-audit-v1",
              "audit_status": "PASS_AUDIT" if not errors else "FAIL_AUDIT",
              "method_disposition": method_disposition,
              "errors": sorted(set(errors)), "mutations": controls,
              "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
              "episode_count": doc.get("episode_count"),
              "opportunity_count": doc.get("opportunity_count"),
              "scope": "deterministic synthetic recovery-sentinel method only"}
    print(json.dumps(result, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
