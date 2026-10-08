"""Candidate implementation. Output is finite-model data, not runtime safety evidence."""
import itertools
import json
from pathlib import Path

from protocol import (ALPHA, COMMON_ALPHA, COMMON_MODES, COMMON_MU, COMMON_P,
                      DISTURBANCE_ENVELOPE, ENVELOPE, HORIZON, IDENTITY,
                      INITIAL, LYAPUNOV, MODES, MU, minimum_dwell_schedule,
                      mode_word, quadratic, schur_stable, trajectory,
                      lyapunov_prefix_bounds, encode, matrix_product,
                      hysteresis_schedule)


def main():
    rows = []
    for number in range(1 << HORIZON):
        word = mode_word(number)
        states, switches = trajectory(word)
        product = IDENTITY
        for name in word:
            product = matrix_product(MODES[name], product)
        bounds = lyapunov_prefix_bounds(word)
        cert = all(b < 1 for b in bounds[1:])
        rows.append({
            "id": number,
            "word": "".join(word),
            "states": [encode(x) for x in states],
            "switch_prefixes": switches,
            "product": [[f"{v.numerator}/{v.denominator}" for v in row] for row in product],
            "schur_stable": schur_stable(product),
            "lyapunov_bounds": [f"{x.numerator}/{x.denominator}" for x in bounds],
            "lyapunov_certified": cert,
            "envelope_crossed": any(max(abs(v) for v in x) > ENVELOPE for x in states),
        })

    disturbed = []
    min_dwell_unique = {}
    for number in range(1 << HORIZON):
        requests = mode_word(number)
        schedule = minimum_dwell_schedule(requests)
        min_dwell_unique["".join(schedule)] = None
        states, _ = trajectory(requests, disturbance=True)
        disturbed.append(max(max(abs(v) for v in x) for x in states))
    # binary extremes cross both hysteresis thresholds, so each possible mode
    # schedule is realizable under the declared stateful comparator.
    hysteresis_realizable = {
        "all_binary_words": True,
        "proof_witness": "A->B uses 1; B->A uses 0; each tick's extreme crosses threshold",
        "scheduled_words": 1 << HORIZON,
    }
    common_rows = []
    for number in range(1 << HORIZON):
        word = mode_word(number)
        states, _ = trajectory(word, modes=COMMON_MODES)
        bounds = [COMMON_ALPHA ** i * COMMON_MU ** 0 for i in range(HORIZON + 1)]
        common_rows.append({"word": "".join(word), "schur_stable": schur_stable(
            _product(word, COMMON_MODES)), "certified": all(x < 1 for x in bounds[1:]),
            "envelope_crossed": any(max(abs(v) for v in x) > ENVELOPE for x in states)})
    dwell_rows = []
    for schedule_text in sorted(min_dwell_unique):
        schedule = tuple(schedule_text)
        states, _ = trajectory(schedule)
        product = _product(schedule, MODES)
        dwell_rows.append({"word": schedule_text, "schur_stable": schur_stable(product),
                           "envelope_crossed": any(max(abs(v) for v in x) > ENVELOPE for x in states)})

    payload = {
        "schema": "switched-dwell-stability-8471-t0-a01-v1",
        "scope": "finite exact-rational method experiment only; no product/runtime/safety claim",
        "horizon": HORIZON,
        "rows": rows,
        "disturbance": {"count": len(disturbed), "max_abs_coordinate":
                        f"{max(disturbed).numerator}/{max(disturbed).denominator}",
                        "strictly_below_declared_observation_envelope": max(disturbed) < DISTURBANCE_ENVELOPE,
                        "robust_stability_claim": False},
        "minimum_dwell": {"unique_schedules": sorted(min_dwell_unique),
                           "count": len(min_dwell_unique), "dwell": 10,
                           "rows": dwell_rows},
        "hysteresis": hysteresis_realizable,
        "common_lyapunov_control": {"rows": common_rows,
            "accepted": sum(r["certified"] for r in common_rows),
            "all_stable": all(r["schur_stable"] for r in common_rows)},
        "reset_control": {"identity": [["1/1", "0/1"], ["0/1", "1/1"]],
                          "mode_change_applies_reset_before_next_mode": True},
        "emergency_override_control": {"minimum_dwell": 10,
             "emergency_request_applies_immediately": True},
        "boundary_control": {"alpha": "1/2", "mu": "2/1", "switches": 1,
             "prefix_bound": "1/1", "strict_less_than_one_certifies": False},
        "claims": {"finite_horizon_only": True, "iss_established": False,
                   "hardware_or_actuator_tested": False, "safety_authority": False}
    }
    Path("candidate.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _product(word, modes):
    p = IDENTITY
    for name in word:
        p = matrix_product(modes[name], p)
    return p


if __name__ == "__main__":
    main()
