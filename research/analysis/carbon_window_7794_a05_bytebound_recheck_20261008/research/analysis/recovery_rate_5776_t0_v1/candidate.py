"""One-shot complete-population synthetic early-warning method candidate."""
from __future__ import annotations

import hashlib
import json
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT / "fixture.json"
OUT = Path("/out/formal01")
MECHANISMS = ("gradual_slowing", "abrupt_breaker", "stable_null", "load_drift")


def simulate(mechanism: str, episode: int, opportunity: int) -> dict:
    """Simulate integer margin recovery after one fixed reversible unit shock."""
    base_margin = 8
    phase = episode % 4
    if mechanism == "gradual_slowing":
        capacity_loss = max(0, opportunity // 2 + phase - 1)
        demand_shift = 0
    elif mechanism == "abrupt_breaker":
        capacity_loss = 0
        demand_shift = 0
    elif mechanism == "stable_null":
        capacity_loss = 0
        demand_shift = 0
    elif mechanism == "load_drift":
        capacity_loss = 0
        demand_shift = max(0, opportunity // 2 + phase - 1)
    else:
        raise ValueError(mechanism)

    pre = base_margin - capacity_loss - demand_shift
    if mechanism == "abrupt_breaker" and opportunity >= 6:
        pre = 0
    disturbance = 1
    post = pre - disturbance
    service_loss = pre <= 0
    # Fixed unit shock has a matched, reversible one-step external demand drop.
    # Recovery is the first tick the margin is back at least at its pre-shock value.
    recovery_ticks = 1 if service_loss else 1 + (capacity_loss if mechanism == "gradual_slowing" else 0)
    if mechanism == "abrupt_breaker" and opportunity >= 6:
        return_state = "UNKNOWN"
        recovery_ticks_value = None
    else:
        return_state = "RETURNED"
        recovery_ticks_value = recovery_ticks
    return {
        "episode_id": episode,
        "mechanism": mechanism,
        "opportunity": opportunity,
        "capacity_loss": capacity_loss,
        "demand_shift": demand_shift,
        "pre_disturbance_margin": pre,
        "disturbance_units": disturbance,
        "post_disturbance_margin": post,
        "recovery_ticks": recovery_ticks_value,
        "return_status": return_state,
        "service_loss": service_loss,
    }


def build_raw() -> dict:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    episodes = []
    for mechanism in MECHANISMS:
        for episode in range(fixture["episodes_per_mechanism"]):
            rows = [simulate(mechanism, episode, op) for op in range(fixture["opportunities_per_episode"])]
            known = [r["recovery_ticks"] for r in rows if r["recovery_ticks"] is not None]
            threshold_source = episode in fixture["calibration_episode_ids"]
            episodes.append({
                "episode_id": episode,
                "mechanism": mechanism,
                "partition": "calibration" if threshold_source else "heldout",
                "opportunities": rows,
                "episode_recovery_median": statistics.median(known) if known else None,
                "service_loss": any(r["service_loss"] for r in rows),
                "has_unknown_return": any(r["return_status"] == "UNKNOWN" for r in rows),
            })
    cal = [e["episode_recovery_median"] for e in episodes
           if e["mechanism"] == "gradual_slowing" and e["partition"] == "calibration"
           and e["episode_recovery_median"] is not None]
    ordered = sorted(cal)
    threshold = ordered[math.ceil(0.75 * len(ordered)) - 1]
    for episode in episodes:
        episode["sentinel_statistic"] = episode["episode_recovery_median"]
        episode["warning"] = (episode["sentinel_statistic"] is not None
                               and episode["sentinel_statistic"] > threshold)
    heldout = [e for e in episodes if e["partition"] == "heldout"]
    valid = {m: [e for e in heldout if e["mechanism"] == m and not e["has_unknown_return"]]
             for m in MECHANISMS}
    warning_counts = {m: sum(bool(e["warning"]) for e in valid[m]) for m in MECHANISMS}
    known_abrupt = [e for e in heldout if e["mechanism"] == "abrupt_breaker" and not e["has_unknown_return"]]
    gradual_sensitivity = warning_counts["gradual_slowing"] / len(valid["gradual_slowing"])
    false_alarm_rates = {m: warning_counts[m] / len(valid[m]) if valid[m] else None
                         for m in MECHANISMS if m != "gradual_slowing"}
    method_pass = (gradual_sensitivity >= 0.75
                   and all(rate is None or rate <= 0.10 for rate in false_alarm_rates.values())
                   and not any(e["warning"] for e in known_abrupt))
    return {
        "schema": "issue5776-recovery-rate-t0-raw-v1",
        "allocation": fixture["allocation"],
        "fixture_sha256": hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
        "candidate_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "threshold_source": "calibration_gradual_slowing_nearest_rank_75th_percentile",
        "threshold": threshold,
        "episodes": episodes,
        "episode_count": len(episodes),
        "opportunity_count": sum(len(e["opportunities"]) for e in episodes),
        "summary": {"heldout_gradual_sensitivity": gradual_sensitivity,
                    "heldout_false_alarm_rates_known_return": false_alarm_rates,
                    "heldout_abrupt_unknown_episode_count": sum(
                        e["has_unknown_return"] for e in heldout if e["mechanism"] == "abrupt_breaker"),
                    "heldout_abrupt_known_warning_count": sum(bool(e["warning"]) for e in known_abrupt)},
        "method_disposition": "PASS_METHOD_SCOPED" if method_pass else "FAIL_METHOD",
        "candidate_invocations": 1,
    }


def main() -> None:
    if OUT.exists():
        raise SystemExit("STOP_OUTPUT_EXISTS")
    OUT.mkdir(parents=True, exist_ok=False)
    raw = (json.dumps(build_raw(), sort_keys=True, separators=(",", ":")) + "\n").encode()
    (OUT / "raw.json").write_bytes(raw)
    print(json.dumps({"status": "CANDIDATE_EXIT_0", "raw_sha256": hashlib.sha256(raw).hexdigest(),
                      "raw_bytes": len(raw)}, sort_keys=True))


if __name__ == "__main__":
    main()
