"""Independent exact-rational reconstruction of Issue #6081 candidate rows."""
import argparse
import json
from fractions import Fraction
from pathlib import Path


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def pick(target, alphabet):
    # Reconstruct deterministic tie breaking from the public alphabet, not candidate code.
    scores = [dot(target, command) for command in alphabet]
    best = max(scores)
    return alphabet[scores.index(best)]


def oracle_schedule(intent, n, alphabet, policy):
    unit = (Fraction(intent[0], intent[2]), Fraction(intent[1], intent[2]))
    if policy == "no_continuation" or intent[:2] == [0, 0]:
        return []
    if policy == "horizon_nearest":
        command = pick(unit, alphabet)
        return [command[:] for _ in range(n)]
    residual = [Fraction(0), Fraction(0)]
    position = [0, 0]
    output = []
    for _ in range(n):
        if policy == "independent_round":
            command = pick(unit, alphabet)
        else:
            # Independent implementation: exhaustive exact objective evaluation.
            target = (unit[0] * (len(output) + 1), unit[1] * (len(output) + 1))
            scores = [
                (Fraction(position[0] + c[0]) - target[0]) ** 2
                + (Fraction(position[1] + c[1]) - target[1]) ** 2
                for c in alphabet
            ]
            command = alphabet[scores.index(min(scores))]
        output.append(command[:])
        position[0] += command[0]
        position[1] += command[1]
        if policy == "error_carry":
            residual[0] += unit[0] - command[0]
            residual[1] += unit[1] - command[1]
    return output


def trajectory(schedule):
    x = y = 0
    prefixes = []
    for dx, dy in schedule:
        x, y = x + dx, y + dy
        prefixes.append([x, y])
    return prefixes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", required=True)
    ap.add_argument("--raw", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    spec = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    by_name = {name: spec["alphabets"][name] for name in spec["alphabets"]}
    rows = [json.loads(line) for line in Path(args.raw).read_text(encoding="utf-8").splitlines() if line]
    expected_count = len(by_name) * len(spec["intents"]) * len(spec["horizons"]) * len(spec["policy_names"])
    errors = []
    seen = set()
    metrics = {}
    maxima = spec["safety_envelope"]["max_abs_prefix_coordinate"]
    intent_map = {x["id"]: x["intent"] for x in spec["intents"]}
    for row in rows:
        key = (row.get("alphabet"), row.get("intent_id"), row.get("horizon"), row.get("policy"))
        if key in seen:
            errors.append({"key": key, "error": "duplicate"})
            continue
        seen.add(key)
        if key[0] not in by_name or key[1] not in intent_map or key[2] not in spec["horizons"] or key[3] not in spec["policy_names"]:
            errors.append({"key": key, "error": "unexpected row"})
            continue
        intent = intent_map[key[1]]
        expected = oracle_schedule(intent, key[2], by_name[key[0]], key[3])
        prefixes = trajectory(expected)
        envelope_breach = any(abs(c) > maxima for point in prefixes for c in point)
        if row.get("schedule") != expected:
            errors.append({"key": key, "error": "schedule mismatch"})
        if row.get("prefixes") != prefixes:
            errors.append({"key": key, "error": "prefix mismatch"})
        if row.get("released") is not True or row.get("refused") is not False:
            errors.append({"key": key, "error": "release/refusal contract"})
        dx, dy = Fraction(intent[0], intent[2]), Fraction(intent[1], intent[2])
        errors_sq = [(Fraction(p[0]) - dx * (i + 1)) ** 2 + (Fraction(p[1]) - dy * (i + 1)) ** 2 for i, p in enumerate(prefixes)]
        max_prefix = max(errors_sq, default=Fraction(0))
        terminal = errors_sq[-1] if errors_sq else Fraction(0)
        switches = sum(expected[i] != expected[i - 1] for i in range(1, len(expected)))
        item = metrics.setdefault(key[0], {}).setdefault(key[3], {"rows": 0, "worst_prefix_sq_sum": Fraction(0), "terminal_sq_sum": Fraction(0), "switches": 0, "envelope_breaches": 0, "released_rows": 0})
        item["rows"] += 1
        item["worst_prefix_sq_sum"] += max_prefix
        item["terminal_sq_sum"] += terminal
        item["switches"] += switches
        item["envelope_breaches"] += int(envelope_breach)
        item["released_rows"] += int(row.get("released") is True)
    expected_keys = {(a, i["id"], n, p) for a in by_name for i in spec["intents"] for n in spec["horizons"] for p in spec["policy_names"]}
    if seen != expected_keys:
        errors.append({"error": "row set mismatch", "missing": len(expected_keys - seen), "extra": len(seen - expected_keys)})
    serial = {a: {p: {k: (str(v) if isinstance(v, Fraction) else v) for k, v in values.items()} for p, values in policies.items()} for a, policies in metrics.items()}
    result = {"schema": "agent-interface.error-carry-6081.audit.v1", "rows_expected": expected_count, "rows_seen": len(rows), "errors": errors, "metrics": serial}
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(f"auditor rows={len(rows)} errors={len(errors)}")


if __name__ == "__main__":
    main()
