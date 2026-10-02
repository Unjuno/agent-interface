"""Candidate schedule generator for frozen Issue #6081 finite fixture."""
import argparse
import json
from fractions import Fraction
from pathlib import Path


def nearest(vector, alphabet):
    # Deterministic tie break follows the frozen alphabet order.
    return max(alphabet, key=lambda a: (vector[0] * a[0] + vector[1] * a[1], -alphabet.index(a)))


def compile_case(intent, horizon, alphabet, policy):
    desired = (Fraction(intent[0], intent[2]), Fraction(intent[1], intent[2]))
    if policy == "no_continuation" or intent[:2] == [0, 0]:
        return []
    if policy == "horizon_nearest":
        return [nearest(desired, alphabet)] * horizon
    schedule = []
    carry = [Fraction(0), Fraction(0)]
    position = [0, 0]
    for _ in range(horizon):
        if policy == "independent_round":
            command = nearest(desired, alphabet)
        elif policy == "error_carry":
            # Select the legal next slot minimizing exact squared cumulative
            # position error; ties preserve frozen alphabet order.
            target = (desired[0] * (len(schedule) + 1), desired[1] * (len(schedule) + 1))
            command = min(alphabet, key=lambda a: (
                (Fraction(position[0] + a[0]) - target[0]) ** 2
                + (Fraction(position[1] + a[1]) - target[1]) ** 2,
                alphabet.index(a),
            ))
            carry[0] += desired[0] - command[0]
            carry[1] += desired[1] - command[1]
        else:
            raise ValueError(policy)
        schedule.append(command)
        position[0] += command[0]
        position[1] += command[1]
    return schedule


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    spec = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    alphabet_names = list(spec["alphabets"])
    rows = []
    for alphabet_name in alphabet_names:
        alphabet = spec["alphabets"][alphabet_name]
        for intent in spec["intents"]:
            for horizon in spec["horizons"]:
                for policy in spec["policy_names"]:
                    schedule = compile_case(intent["intent"], horizon, alphabet, policy)
                    x = y = 0
                    prefixes = []
                    for command in schedule:
                        x += command[0]
                        y += command[1]
                        prefixes.append([x, y])
                    rows.append({"alphabet": alphabet_name, "intent_id": intent["id"], "horizon": horizon,
                                 "policy": policy, "schedule": schedule, "prefixes": prefixes,
                                 "released": True, "refused": False})
    with Path(args.output).open("x", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    print(f"candidate rows={len(rows)}")


if __name__ == "__main__":
    main()
