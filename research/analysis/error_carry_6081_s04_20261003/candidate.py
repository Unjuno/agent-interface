"""Candidate schedule compiler for the synthetic #6081 S04 allocation."""

from fractions import Fraction
import json
import random
import sys
from pathlib import Path


def nearest_action(intent, alphabet):
    """Euclidean nearest legal vector; alphabet order is the exact-tie break."""
    return min(
        enumerate(alphabet),
        key=lambda item: (
            (intent[0] - item[1][0]) ** 2 + (intent[1] - item[1][1]) ** 2,
            item[0],
        ),
    )[1]


def error_carry_schedule(intent, horizon, alphabet):
    position = [0, 0]
    schedule = []
    for prefix in range(1, horizon + 1):
        target = (intent[0] * prefix, intent[1] * prefix)
        command = min(
            enumerate(alphabet),
            key=lambda item: (
                (Fraction(position[0] + item[1][0]) - target[0]) ** 2
                + (Fraction(position[1] + item[1][1]) - target[1]) ** 2,
                item[0],
            ),
        )[1]
        schedule.append(tuple(command))
        position[0] += command[0]
        position[1] += command[1]
    return schedule


def _common_denominator(intent):
    a, b = intent[0].denominator, intent[1].denominator
    return a * b // __import__("math").gcd(a, b)


def independent_round_schedule(intent, horizon, alphabet, seed):
    """Unbiased stateless per-slot rounding under the frozen alphabet geometry."""
    rng = random.Random(seed)
    denominator = _common_denominator(intent)
    if len(alphabet) == 4:
        if abs(intent[0]) + abs(intent[1]) != 1:
            raise ValueError("cardinal intent must lie on the L1 unit boundary")
        weights = [abs(intent[0]) * denominator, abs(intent[1]) * denominator]
        output = []
        for _ in range(horizon):
            draw = rng.randrange(denominator)
            if draw < weights[0]:
                output.append((1 if intent[0] > 0 else -1, 0))
            else:
                output.append((0, 1 if intent[1] > 0 else -1))
        return output
    if len(alphabet) == 8:
        if max(abs(intent[0]), abs(intent[1])) != 1:
            raise ValueError("eight-way intent must lie on the L-infinity unit boundary")
        output = []
        for _ in range(horizon):
            xdraw = rng.randrange(denominator)
            ydraw = rng.randrange(denominator)
            x = (1 if intent[0] > 0 else -1) if xdraw < abs(intent[0]) * denominator else 0
            y = (1 if intent[1] > 0 else -1) if ydraw < abs(intent[1]) * denominator else 0
            output.append((x, y))
        return output
    raise ValueError("unsupported action alphabet")


def decode_intent(value):
    return Fraction(value[0], value[2]), Fraction(value[1], value[2])


def compile_request(request):
    """Preflight and compile one bounded request; no execution authority."""
    empty = {"commands": [], "release_receipt": {"after_slot": 0, "all_inputs_up": True}, "executed_slots": 0}
    if request["calibration_id"] != request["current_calibration_id"]:
        return {**empty, "disposition": "REFUSE_CALIBRATION_MISMATCH"}
    if request["deadline_slots"] < request["horizon"]:
        return {**empty, "disposition": "REFUSE_DEADLINE"}
    required = request.get("required_combo")
    if required is not None and required not in request["available_combos"]:
        return {**empty, "disposition": "REFUSE_UNAVAILABLE_COMBO"}
    intent = decode_intent(request["intent"])
    if intent == (0, 0) or request["policy"] == "no_continuation":
        return {**empty, "disposition": "NO_CONTINUATION"}
    alphabet = [tuple(v) for v in request["alphabet"]]
    policy = request["policy"]
    if policy == "horizon_nearest":
        command = nearest_action(intent, alphabet)
        commands = [tuple(command)] * request["horizon"]
    elif policy == "independent_round":
        commands = independent_round_schedule(intent, request["horizon"], alphabet, request["seed"])
    elif policy == "error_carry":
        commands = error_carry_schedule(intent, request["horizon"], alphabet)
    else:
        raise ValueError(f"unknown policy: {policy}")

    position = [0, 0]
    for prefix, command in enumerate(commands, 1):
        position[0] += command[0]
        position[1] += command[1]
        error = (intent[0] * prefix - position[0], intent[1] * prefix - position[1])
        if max(abs(error[0]), abs(error[1])) > Fraction(request["max_abs_prefix_error"]):
            return {**empty, "disposition": "REFUSE_ENVELOPE"}
    return {
        "commands": [list(c) for c in commands],
        "release_receipt": {"after_slot": len(commands), "all_inputs_up": True},
        "executed_slots": len(commands),
        "disposition": "COMPLETE",
    }


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: candidate.py cases.json raw.jsonl")
    cases = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    rows = []
    for request in cases["requests"]:
        rows.append({"request_id": request["request_id"], **compile_request(request)})
    with Path(argv[2]).open("w", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
