"""One-shot Pareto-bound experiment for Issue #7424; deterministic CPU only."""
import argparse
import json
import platform
import sys

ALPHA = 0.25
RATE = 0.2
LO, HI = 0.0, 1.0
REF = 1.0
HORIZON = 20
MAX_FIRST_JUMP = 0.15


def cold_a03(y, previous):
    z = 0.0
    states = [y]
    commands = []
    for tick in range(HORIZON):
        error = REF - y
        raw = 2.0 * error + z
        requested = min(HI, max(LO, raw))
        applied = min(previous + RATE, max(previous - RATE, requested))
        applied = min(HI, max(LO, applied))
        z_next = z if ((raw >= HI and error > 0) or (raw <= LO and error < 0)) else min(1.0, max(-1.0, z + 0.1 * error))
        commands.append(applied)
        y = y + ALPHA * (applied - y)
        states.append(y)
        previous, z = applied, z_next
    return {"commands": commands, "states": states, "iae": sum(abs(REF - y) for y in states)}


def continuity_constrained_oracle(y, previous):
    states, commands = [y], []
    for tick in range(HORIZON):
        lower, upper = max(LO, previous - RATE), min(HI, previous + RATE)
        if tick == 0:
            upper = min(upper, previous + MAX_FIRST_JUMP)
            lower = max(lower, previous - MAX_FIRST_JUMP)
        # In the frozen positive-error region, greater admissible input
        # monotonically improves current and every future reachable state.
        applied = upper
        commands.append(applied)
        y = y + ALPHA * (applied - y)
        states.append(y)
        previous = applied
    return {"commands": commands, "states": states, "iae": sum(abs(REF - y) for y in states)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True)
    args = parser.parse_args()
    cases = []
    for name, initial_y, previous, cold_iae in (
        ("no-disturbance", 0.4, 0.6, 6.0238),
        ("step-disturbance-at-switch", 0.5, 0.6, 5.65),
    ):
        cold = cold_a03(initial_y, previous)
        oracle = continuity_constrained_oracle(initial_y, previous)
        cases.append({
            "name": name,
            "initial_y": initial_y,
            "actually_applied_u": previous,
            "pinned_a03_cold_iae": cold_iae,
            "replayed_cold_iae": round(cold["iae"], 12),
            "cold_commands": [round(x, 12) for x in cold["commands"]],
            "oracle_commands": [round(x, 12) for x in oracle["commands"]],
            "oracle_states": [round(x, 12) for x in oracle["states"]],
            "oracle_iae": round(oracle["iae"], 12),
            "cold_first_jump": round(abs(cold["commands"][0] - previous), 12),
            "oracle_first_jump": round(abs(oracle["commands"][0] - previous), 12),
            "continuity_reduction": round(1 - abs(oracle["commands"][0] - previous) / abs(cold["commands"][0] - previous), 12),
            "iae_delta_vs_pinned_cold": round(oracle["iae"] - cold_iae, 12),
        })
    raw = {
        "schema": "issue7424-a04-pareto-bound-raw-v1",
        "runtime": {"python": sys.version, "platform": platform.platform()},
        "source": {
            "base_main_sha": "bbed04b9bf5ad7d94e20fcea212b98d19dfa6395",
            "predecessor_pr": 7500,
            "predecessor_head": "2d1c10fcdd3e0263170ba98a08dc5d1c854da9a9",
            "predecessor_raw_git_blob": "720a314e1859ddca9580c1fc46b751cd515ec65c",
        },
        "cases": cases,
        "scope": "deterministic finite scalar oracle; no live runtime or actuation",
    }
    with open(args.raw, "w", encoding="utf-8", newline="\n") as stream:
        json.dump(raw, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(json.dumps({"status": "RUN_COMPLETE", "cases": len(cases)}, sort_keys=True))


if __name__ == "__main__":
    main()
