#!/usr/bin/env python3
"""Frozen synthetic decision-value acquisition experiment for Issue #7934."""
import hashlib
import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
PROFILES = json.loads((ROOT / "profiles.json").read_text(encoding="utf-8"))
POLICIES = ("cost", "entropy", "decision_value", "oracle")


def draw(profile, seed, stream):
    key = f"7934-T0-A01|{profile}|{seed}|{stream}".encode()
    value = int(hashlib.sha256(key).hexdigest()[:13], 16)
    return value / float(16**13)


def joint(profile):
    return [(int(x), int(y), float(p)) for x, y, p in profile["state_prior"]]


def likelihood(check, state, signal):
    x, y, _ = state
    if check["kind"] == "noisy_x":
        return check["accuracy"] if signal == x else 1.0 - check["accuracy"]
    if check["kind"] == "perfect_y":
        return 1.0 if signal == y else 0.0
    raise ValueError(check["kind"])


def entropy(probabilities):
    return -sum(p * math.log2(p) for p in probabilities if p > 0)


def score_check(profile, check, allowed=("A", "B")):
    states = joint(profile)
    p_signal = {}
    posterior = {}
    for signal in (0, 1):
        weights = [(s, p * likelihood(check, s, signal)) for s in states for p in (s[2],)]
        total = sum(w for _, w in weights)
        p_signal[signal] = total
        posterior[signal] = [(s, w / total) for s, w in weights] if total else []
    h_state = entropy([p for _, _, p in states])
    conditional_h = 0.0
    before = route_value(states, allowed)
    after = 0.0
    for signal in (0, 1):
        if p_signal[signal] == 0:
            continue
        conditional_h += p_signal[signal] * entropy([p for _, p in posterior[signal]])
        after += p_signal[signal] * route_value(
            [(s[0], s[1], p) for s, p in posterior[signal]], allowed
        )
    return {"information_bits": h_state - conditional_h, "evsi": after - before}


def route_value(states, allowed):
    values = {
        "A": sum(p for x, _, p in states if x == 0),
        "B": sum(p for x, _, p in states if x == 1),
    }
    return max((values[r] for r in allowed), default=0.0)


def choose_route(states, allowed):
    values = {
        "A": sum(p for x, _, p in states if x == 0),
        "B": sum(p for x, _, p in states if x == 1),
    }
    return min(allowed, key=lambda r: (-values[r], r)) if allowed else None


def select(profile, policy, *, allowed=("A", "B"), fresh=True,
           dependency_known=True, unknown_mass=0.0, budget=None):
    if not fresh or not dependency_known or unknown_mass > 0:
        return {"status": "UNKNOWN", "check": None, "route": None,
                "checks_performed": 0}
    if len(allowed) == 1:
        return {"status": "SELECTED", "check": None, "route": allowed[0],
                "checks_performed": 0}
    if not allowed:
        return {"status": "UNKNOWN", "check": None, "route": None,
                "checks_performed": 0}
    budget = PROFILES["budget"] if budget is None else budget
    scored = [(c, score_check(profile, c, allowed)) for c in profile["checks"]]
    available = [(c, s) for c, s in scored if c["cost"] <= budget]
    picked = None
    if policy == "cost" and available:
        picked = min((c for c, _ in available), key=lambda c: (c["cost"], c["id"]))
    elif policy == "entropy" and available:
        c, s = min(available, key=lambda pair: (-pair[1]["information_bits"],
                                                  pair[0]["cost"], pair[0]["id"]))
        if s["information_bits"] >= PROFILES["entropy_threshold_bits"]:
            picked = c
    elif policy in ("decision_value", "oracle"):
        positive = [(c, s) for c, s in available
                    if s["evsi"] - c["cost"] > 1e-12]
        if positive:
            c, _ = min(positive, key=lambda pair: (-(pair[1]["evsi"] - pair[0]["cost"]),
                                                    pair[0]["cost"], pair[0]["id"]))
            picked = c
    else:
        raise ValueError(policy)
    return {"status": "SELECTED", "check": picked["id"] if picked else None,
            "route": None, "checks_performed": int(picked is not None)}


def observed_signal(check, record):
    if check is None:
        return None
    return record["signals"][check]


def posterior_route(profile, check_id, signal, allowed=("A", "B")):
    if check_id is None:
        return choose_route(joint(profile), allowed)
    check = next(c for c in profile["checks"] if c["id"] == check_id)
    weights = [(s, s[2] * likelihood(check, s, signal)) for s in joint(profile)]
    total = sum(w for _, w in weights)
    states = [(s[0], s[1], w / total) for s, w in weights if total]
    return choose_route(states, allowed)


def make_record(profile_name, seed, profile):
    x = int(draw(profile_name, seed, "x") >= 0.5)
    if profile_name == "agreement":
        y = int(draw(profile_name, seed, "y") >= 0.99)
    elif profile_name == "disagreement":
        y = int(draw(profile_name, seed, "y") >= 0.5)
    else:
        same = draw(profile_name, seed, "y") < 0.7
        y = x if same else 1 - x
    x_signal = x if draw(profile_name, seed, "xcheck") < 0.8 else 1 - x
    return {"profile": profile_name, "seed": seed, "x": x, "y": y,
            "signals": {"xcheck": x_signal, "ycheck": y}}


def run(outdir):
    outdir.mkdir(parents=True, exist_ok=True)
    raw_path = outdir / "raw_observations.jsonl"
    raw = []
    summaries = {}
    decisions = {}
    for name, profile in PROFILES["profiles"].items():
        rows = [make_record(name, PROFILES["seed_start"] + i, profile)
                for i in range(PROFILES["seed_count"])]
        raw.extend(rows)
        summaries[name] = {}
        decisions[name] = {}
        for policy in POLICIES:
            selected = select(profile, policy)
            actual = []
            for row in rows:
                signal = observed_signal(selected["check"], row)
                route = posterior_route(profile, selected["check"], signal)
                utility = int((route == "A" and row["x"] == 0) or
                              (route == "B" and row["x"] == 1))
                actual.append({"seed": row["seed"], "signal": signal, "route": route,
                               "utility": utility, "regret": 1 - utility,
                               "cost": next((c["cost"] for c in profile["checks"]
                                             if c["id"] == selected["check"]), 0.0),
                               "gate_violation": route not in ("A", "B")})
            summaries[name][policy] = {
                "selected_check": selected["check"],
                "mean_realized_regret": sum(r["regret"] for r in actual) / len(actual),
                "mean_check_cost": sum(r["cost"] for r in actual) / len(actual),
                "hard_gate_violations": sum(r["gate_violation"] for r in actual),
                "actual_decisions": actual,
            }
            decisions[name][policy] = selected["check"]
    raw_path.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in raw),
                        encoding="utf-8")
    controls = {
        "stale_source": select(PROFILES["profiles"]["disagreement"], "decision_value", fresh=False),
        "unknown_dependency": select(PROFILES["profiles"]["correlated"], "decision_value",
                                      dependency_known=False),
        "unmodeled_mass_0_10": select(PROFILES["profiles"]["disagreement"],
                                       "decision_value", unknown_mass=0.10),
    }
    denied = {p: select(PROFILES["profiles"]["disagreement"], p, allowed=("A",))
              for p in POLICIES}
    result = {"allocation": "7934-T0-A01", "profile_count": len(PROFILES["profiles"]),
              "seed_count_per_profile": PROFILES["seed_count"],
              "observations": len(raw), "policies": POLICIES,
              "decisions": decisions, "summaries": summaries,
              "controls": controls, "one_route_denied": denied,
              "raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest()}
    result_path = outdir / "candidate_result.json"
    result_path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps({"status": "SIMULATOR_COMPLETE", "observations": len(raw),
                      "raw_sha256": result["raw_sha256"],
                      "decisions": decisions}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(run(pathlib.Path(sys.argv[1])))
