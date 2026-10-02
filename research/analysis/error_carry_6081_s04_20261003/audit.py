"""Independent exact-arithmetic reconstruction for the #6081 S04 raw output.

This module intentionally does not import candidate.py.
"""

from collections import defaultdict
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
import random
import sys
from pathlib import Path


def fraction_from_triplet(value):
    return Fraction(value[0], value[2]), Fraction(value[1], value[2])


def _best_single(intended, options):
    winner = None
    winner_key = None
    for rank, option in enumerate(options):
        dx = intended[0] - option[0]
        dy = intended[1] - option[1]
        key = (dx * dx + dy * dy, rank)
        if winner_key is None or key < winner_key:
            winner, winner_key = option, key
    return winner


def _reconstruct_bresenham(intended, count, options):
    """Greedy exact cumulative-prefix optimum, reconstructed independently."""
    x = y = 0
    answer = []
    for t in range(1, count + 1):
        target_x, target_y = intended[0] * t, intended[1] * t
        choices = []
        for rank, (dx, dy) in enumerate(options):
            ex, ey = Fraction(x + dx) - target_x, Fraction(y + dy) - target_y
            choices.append((ex * ex + ey * ey, rank, (dx, dy)))
        move = min(choices)[2]
        answer.append(move)
        x += move[0]
        y += move[1]
    return answer


def _reconstruct_independent_round(intended, count, options, seed):
    """Replay stateless coordinate/category rounding from its declared seed."""
    generator = random.Random(seed)
    den = intended[0].denominator * intended[1].denominator // __import__("math").gcd(
        intended[0].denominator, intended[1].denominator
    )
    moves = []
    if len(options) == 4:
        weights = (abs(intended[0]) * den, abs(intended[1]) * den)
        for _ in range(count):
            u = generator.randrange(den)
            if u < weights[0]:
                moves.append((1 if intended[0] > 0 else -1, 0))
            else:
                moves.append((0, 1 if intended[1] > 0 else -1))
        return moves
    for _ in range(count):
        ux, uy = generator.randrange(den), generator.randrange(den)
        px = abs(intended[0]) * den
        py = abs(intended[1]) * den
        mx = (1 if intended[0] > 0 else -1) if ux < px else 0
        my = (1 if intended[1] > 0 else -1) if uy < py else 0
        moves.append((mx, my))
    return moves


def expected_result(request):
    """Independent preflight, policy, and envelope reconstruction."""
    if request["calibration_id"] != request["current_calibration_id"]:
        status = "REFUSE_CALIBRATION_MISMATCH"
        moves = []
    elif request["deadline_slots"] < request["horizon"]:
        status = "REFUSE_DEADLINE"
        moves = []
    elif request.get("required_combo") is not None and request["required_combo"] not in request["available_combos"]:
        status = "REFUSE_UNAVAILABLE_COMBO"
        moves = []
    else:
        vector = fraction_from_triplet(request["intent"])
        options = [tuple(point) for point in request["alphabet"]]
        if vector == (0, 0) or request["policy"] == "no_continuation":
            status = "NO_CONTINUATION"
            moves = []
        elif request["policy"] == "horizon_nearest":
            moves = [_best_single(vector, options)] * request["horizon"]
            status = "COMPLETE"
        elif request["policy"] == "independent_round":
            moves = _reconstruct_independent_round(vector, request["horizon"], options, request["seed"])
            status = "COMPLETE"
        elif request["policy"] == "error_carry":
            moves = _reconstruct_bresenham(vector, request["horizon"], options)
            status = "COMPLETE"
        else:
            raise ValueError("unrecognized preregistered arm")
        # The full schedule is screened before any command would be admitted.
        if status == "COMPLETE":
            x = y = 0
            bound = Fraction(request["max_abs_prefix_error"])
            for t, move in enumerate(moves, 1):
                x, y = x + move[0], y + move[1]
                if max(abs(vector[0] * t - x), abs(vector[1] * t - y)) > bound:
                    status, moves = "REFUSE_ENVELOPE", []
                    break
    return {
        "disposition": status,
        "commands": [list(move) for move in moves],
        "executed_slots": len(moves),
        "release_receipt": {"after_slot": len(moves), "all_inputs_up": True},
    }


def validate_row(request, row):
    expected = expected_result(request)
    return [field for field, value in expected.items() if row.get(field) != value]


def _prefix_errors(request, row):
    target = fraction_from_triplet(request["intent"])
    position = [0, 0]
    commands = row["commands"]
    values = []
    for t in range(1, request["horizon"] + 1):
        if t <= len(commands):
            position[0] += commands[t - 1][0]
            position[1] += commands[t - 1][1]
        ex = target[0] * t - position[0]
        ey = target[1] * t - position[1]
        values.append(ex * ex + ey * ey)
    return values


def _is_nonrepresentable(request):
    vector = fraction_from_triplet(request["intent"])
    return vector != (0, 0) and vector not in {tuple(Fraction(v) for v in action) for action in request["alphabet"]}


def _aggregate(cases, rows):
    requests = {r["request_id"]: r for r in cases["requests"]}
    groups = defaultdict(lambda: {"sum_prefix_sq": Fraction(0), "prefixes": 0, "sum_worst_sq": Fraction(0), "sum_terminal_sq": Fraction(0), "n": 0, "completed": 0})
    pooled = defaultdict(lambda: {"sum_prefix_sq": Fraction(0), "prefixes": 0, "sum_worst_sq": Fraction(0), "sum_terminal_sq": Fraction(0), "n": 0, "completed": 0})
    for row in rows:
        request = requests[row["request_id"]]
        if not request["request_id"].startswith("primary/") or not _is_nonrepresentable(request):
            continue
        errors = _prefix_errors(request, row)
        key = (request["alphabet_id"], request["policy"])
        targets = (groups[key], pooled[request["policy"]])
        for values in targets:
            values["sum_prefix_sq"] += sum(errors, Fraction(0))
            values["prefixes"] += len(errors)
            values["sum_worst_sq"] += max(errors, default=Fraction(0))
            values["sum_terminal_sq"] += errors[-1] if errors else Fraction(0)
            values["n"] += 1
            values["completed"] += row["disposition"] == "COMPLETE"
    def printable(table):
        output = {}
        for key, values in table.items():
            label = "/".join(key) if isinstance(key, tuple) else key
            n, prefix_count = values["n"], values["prefixes"]
            output[label] = {
                "requests": n,
                "completion_rate": [values["completed"], n],
                "mean_squared_prefix_error": fraction_json(values["sum_prefix_sq"] / prefix_count) if prefix_count else None,
                "mean_worst_prefix_squared_error": fraction_json(values["sum_worst_sq"] / n) if n else None,
                "mean_terminal_squared_error": fraction_json(values["sum_terminal_sq"] / n) if n else None,
            }
        return output
    return {"by_alphabet": printable(groups), "pooled": printable(pooled)}


def fraction_json(value):
    value = Fraction(value)
    return {"numerator": value.numerator, "denominator": value.denominator, "decimal": float(value)}


def _transfer_control(requests, rows, truth):
    control = truth["held_out_transfer_control"]
    request = requests[control["source_request_id"]]
    row = next(r for r in rows if r["request_id"] == control["source_request_id"])
    vx = vy = x = y = 0
    collision = False
    max_linear_deviation = Fraction(0)
    for t, command in enumerate(row["commands"], 1):
        vx += command[0]
        vy += command[1]
        nx, ny = x + vx, y + vy
        wall = truth["held_out_transfer_control"]["wall_x"]
        if nx >= wall:
            x = wall
            y = ny
            collision = True
            break
        x, y = nx, ny
        linear_x = sum(c[0] for c in row["commands"][:t])
        linear_y = sum(c[1] for c in row["commands"][:t])
        max_linear_deviation = max(max_linear_deviation, abs(x - linear_x), abs(y - linear_y))
    supported = not collision and max_linear_deviation <= Fraction(1)
    return {
        "source_request_id": request["request_id"],
        "collision": collision,
        "max_linear_deviation": fraction_json(max_linear_deviation),
        "classification": "TRANSFER_SUPPORTED_IN_FIXTURE" if supported else "HOLD_TRANSFER_UNSUPPORTED",
        "included_in_primary_metric": False,
    }


def audit_records(cases, truth, rows):
    errors = []
    expected_count = truth["expected_total_requests"]
    primary_count = sum(r["request_id"].startswith("primary/") for r in cases["requests"])
    control_count = len(cases["requests"]) - primary_count
    if primary_count != truth["expected_primary_requests"]:
        errors.append(f"primary_request_count:{primary_count}!={truth['expected_primary_requests']}")
    if control_count != truth["expected_control_requests"]:
        errors.append(f"control_request_count:{control_count}!={truth['expected_control_requests']}")
    if len(rows) != expected_count:
        errors.append(f"row_count:{len(rows)}!={expected_count}")
    request_map = {r["request_id"]: r for r in cases["requests"]}
    row_map = {}
    for row in rows:
        request_id = row.get("request_id")
        if request_id in row_map:
            errors.append(f"duplicate_request:{request_id}")
        row_map[request_id] = row
    missing = set(request_map) - set(row_map)
    extra = set(row_map) - set(request_map)
    if missing:
        errors.append(f"missing_requests:{len(missing)}")
    if extra:
        errors.append(f"extra_requests:{len(extra)}")
    for request_id in sorted(set(request_map) & set(row_map)):
        row = row_map[request_id]
        for field in validate_row(request_map[request_id], row):
            errors.append(f"{request_id}:{field}:mismatch")
    aggregates = _aggregate(cases, rows)
    required_policies = set(truth["policies"])
    observed_policies = {r.get("policy") for r in cases["requests"] if r["request_id"].startswith("primary/")}
    if observed_policies != required_policies:
        errors.append(f"primary_policy_coverage:{sorted(observed_policies)}!={sorted(required_policies)}")
    for alphabet_id in cases["alphabets"]:
        observed = {r.get("policy") for r in cases["requests"] if r.get("alphabet_id") == alphabet_id and r["request_id"].startswith("primary/")}
        if observed != required_policies:
            errors.append(f"alphabet_policy_coverage:{alphabet_id}:{sorted(observed)}!={sorted(required_policies)}")
    control_results = {}
    for request_id, expected_status in truth["controls"].items():
        if request_id == "omitted_release_mutation":
            continue
        row = row_map.get(request_id)
        actual = None if row is None else row.get("disposition")
        control_results[request_id] = {"expected": expected_status, "actual": actual, "pass": actual == expected_status}
        if actual != expected_status:
            errors.append(f"control:{request_id}:{actual}!={expected_status}")

    # The auditor must prove the release gate rejects a planted raw mutation.
    complete = next((r for r in rows if r.get("disposition") == "COMPLETE"), None)
    mutation_rejected = False
    if complete is not None:
        mutated = deepcopy(complete)
        mutated["release_receipt"] = {"after_slot": mutated["executed_slots"], "all_inputs_up": False}
        mutation_rejected = bool(validate_row(request_map[mutated["request_id"]], mutated))
    if not mutation_rejected:
        errors.append("mutation:omitted_or_false_release_not_rejected")
    control_results["omitted_release_mutation"] = {
        "expected": "REJECT", "actual": "REJECT" if mutation_rejected else "ACCEPT", "pass": mutation_rejected
    }

    transfer = _transfer_control(request_map, rows, truth)
    if transfer["classification"] != truth["held_out_transfer_control"]["classification"]:
        errors.append("held_out_transfer_control:classification_mismatch")

    pooled = aggregates["pooled"]
    c_metric = pooled.get("error_carry", {}).get("mean_squared_prefix_error")
    a_metric = pooled.get("horizon_nearest", {}).get("mean_squared_prefix_error")
    b_metric = pooled.get("independent_round", {}).get("mean_squared_prefix_error")
    def less(left, right):
        if left is None or right is None:
            return False
        return left["numerator"] * right["denominator"] < right["numerator"] * left["denominator"]
    method_pass = less(c_metric, a_metric) and less(c_metric, b_metric)
    # Exact-representable direction controls must preserve their intended vector
    # at every offered prefix, for every policy (no-continuation is excluded).
    for request in cases["requests"]:
        if not request["request_id"].startswith("primary/") or _is_nonrepresentable(request):
            continue
        row = row_map.get(request["request_id"])
        if row is None:
            continue
        intended = fraction_from_triplet(request["intent"])
        if intended == (0, 0) or request["policy"] == "no_continuation":
            continue
        if row.get("disposition") != "COMPLETE":
            errors.append(f"exact_representable_refused:{request['request_id']}")
            continue
        if any(_prefix_errors(request, row)):
            errors.append(f"exact_representable_nonzero_error:{request['request_id']}")
    if errors:
        disposition = "FAIL_AUDIT"
    elif method_pass:
        disposition = "PASS_METHOD_SCOPED"
    else:
        disposition = "FAIL_METHOD"
    return {
        "disposition": disposition,
        "errors": errors,
        "candidate_rows": len(rows),
        "reconstructed_rows": len(set(row_map) & set(request_map)),
        "aggregates": aggregates,
        "method_gate": {"error_carry_below_nearest": less(c_metric, a_metric), "error_carry_below_independent_round": less(c_metric, b_metric)},
        "controls": control_results,
        "omitted_release_mutation_rejected": mutation_rejected,
        "held_out_transfer_control": transfer,
    }


def main(argv):
    if len(argv) != 5:
        raise SystemExit("usage: audit.py cases.json truth.json raw.jsonl audit.json")
    case_bytes = Path(argv[1]).read_bytes()
    truth_bytes = Path(argv[2]).read_bytes()
    raw_bytes = Path(argv[3]).read_bytes()
    cases = json.loads(case_bytes)
    truth = json.loads(truth_bytes)
    rows = [json.loads(line) for line in raw_bytes.decode("utf-8").splitlines() if line]
    result = audit_records(cases, truth, rows)
    result["inputs_sha256"] = {
        "cases": hashlib.sha256(case_bytes).hexdigest(),
        "truth": hashlib.sha256(truth_bytes).hexdigest(),
        "raw": hashlib.sha256(raw_bytes).hexdigest(),
    }
    Path(argv[4]).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    return 0 if result["disposition"] != "FAIL_AUDIT" else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
