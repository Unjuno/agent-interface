"""Deterministically materialize the frozen visible and auditor-only fixtures."""
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
HORIZON = 40


def x_linear(t):
    return round(12.0 + 0.55 * t, 4)


def x_reversal(t):
    return round(12.0 + 0.55 * min(t, 18) - 1.1 * max(0, t - 18), 4)


def make_case(name, visual, truth, *, probe=None, identity=None, focus=None, lease=None):
    if probe is None:
        probe = visual
    if identity is None:
        identity = ["target-A"] * HORIZON
    if focus is None:
        focus = [True] * HORIZON
    if lease is None:
        lease = [True] * HORIZON
    observations = []
    oracle = []
    for t in range(HORIZON):
        observations.append({
            "tick": t,
            "capture_x": visual[t],
            "probe_x": probe[t],
            "identity": identity[t],
            "focus_valid": focus[t],
            "lease_valid": lease[t],
        })
        oracle.append({"tick": t, "target_x": truth[t], "target_identity": "target-A"})
    return {
        "case_id": name,
        "horizon": HORIZON,
        "initial_agent_x": 0.0,
        "intended_identity": "target-A",
        "observations": observations,
    }, {"case_id": name, "intended_identity": "target-A", "states": oracle}


def build():
    cases = []
    truth_cases = []
    steady = [x_linear(t) for t in range(HORIZON)]
    reversal = [x_reversal(t) for t in range(HORIZON)]

    specs = [
        ("steady_drift", steady, steady, None, None, None, None),
        ("abrupt_reversal", reversal, reversal, None, None, None, None),
        ("target_disappearance", [x_linear(t) if t < 24 else None for t in range(HORIZON)],
         [x_linear(t) if t < 24 else None for t in range(HORIZON)], None, None, None, None),
        ("misleading_animation", [round(18 + (0.65*t if t < 16 else 10.4 - 0.8*(t-16)), 4)
                                   for t in range(HORIZON)],
         [28.0] * HORIZON, None, None, None, None),
        ("semantic_identity_switch", steady, [x_linear(t) if t < 20 else None for t in range(HORIZON)],
         None, ["target-A"] * 20 + ["target-B"] * 20, None, None),
        ("focus_loss", steady, steady, None, None, [True] * 20 + [False] * 20, None),
        ("lease_expiry", steady, steady, None, None, None, [True] * 20 + [False] * 20),
        ("perfect_tracker_positive", steady, steady, None, None, None, None),
        ("stale_tracker_negative", reversal, reversal,
         [x_linear(t) for t in range(HORIZON)], None, None, None),
    ]
    for name, visual, truth, probe, identity, focus, lease in specs:
        visible, oracle = make_case(name, visual, truth, probe=probe, identity=identity,
                                    focus=focus, lease=lease)
        cases.append(visible)
        truth_cases.append(oracle)
    return {"schema": "agent-interface.intermit6061.input.v1", "horizon": HORIZON,
            "cases": cases}, {"schema": "agent-interface.intermit6061.truth.v1",
                               "cases": truth_cases}


def main():
    visible, truth = build()
    ROOT.joinpath("input_fixture.json").write_text(json.dumps(visible, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    ROOT.joinpath("truth_oracle.json").write_text(json.dumps(truth, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
