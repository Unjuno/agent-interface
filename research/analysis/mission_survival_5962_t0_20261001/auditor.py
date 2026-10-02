"""Independent exact verifier; does not import candidate implementation."""
from fractions import Fraction
from itertools import product
import copy
import json
import sys

TRANSITIONS = {
    "iid": {"S": Fraction(1, 5), "F": Fraction(1, 5)},
    "clustered": {"S": Fraction(1, 20), "F": Fraction(4, 5)},
    "alternating": {"S": Fraction(1, 4), "F": Fraction(0, 1)},
}
START_FAILURE = Fraction(1, 5)
N_VALUES = tuple(range(1, 9))
ENDPOINTS = ("any_failure", "failure_burst_2")


def expected_probability(name, word):
    trans = TRANSITIONS[name]
    result = START_FAILURE if word[0] == "F" else 1 - START_FAILURE
    for left, right in zip(word, word[1:]):
        chance_f = trans[left]
        result *= chance_f if right == "F" else 1 - chance_f
    return result


def expected_stop(word, endpoint):
    if endpoint == "any_failure":
        for pos, symbol in enumerate(word):
            if symbol == "F":
                return "FAIL", pos + 1
        return "SURVIVE", len(word)
    for pos in range(1, len(word)):
        if word[pos - 1] == word[pos] == "F":
            return "FAIL", pos + 1
    return "SURVIVE", len(word)


def audit(data):
    errors = []
    if data.get("schema") != "issue5962-mission-survival-t0-v1":
        errors.append("schema")
    rows = data.get("rows")
    if not isinstance(rows, list):
        return ["rows_type"]
    expected_keys = {
        (name, n, "".join(bits))
        for name in TRANSITIONS for n in N_VALUES
        for bits in product("SF", repeat=n)
    }
    seen = set()
    totals = {(name, n): Fraction(0) for name in TRANSITIONS for n in N_VALUES}
    marginal_f = {(name, n, pos): Fraction(0)
                  for name in TRANSITIONS for n in N_VALUES for pos in range(n)}
    survival = {(name, n, mode): Fraction(0)
                for name in TRANSITIONS for n in N_VALUES for mode in ENDPOINTS}
    observed_sessions = {(name, n, mode): 0
                         for name in TRANSITIONS for n in N_VALUES for mode in ENDPOINTS}

    for row in rows:
        try:
            name, n, word = row["kernel"], row["n"], row["path"]
            key = (name, n, word)
            if key in seen:
                errors.append("duplicate_path")
                continue
            seen.add(key)
            if key not in expected_keys:
                errors.append("unexpected_path")
                continue
            p = Fraction(row["probability"])
            want = expected_probability(name, word)
            if p != want:
                errors.append("path_probability")
            if p < 0:
                errors.append("negative_probability")
            totals[(name, n)] += p
            for pos, symbol in enumerate(word):
                if symbol == "F":
                    marginal_f[(name, n, pos)] += p
            max_run = max((len(x) for x in word.split("S")), default=0)
            if row.get("potential_max_failure_run") != max_run:
                errors.append("potential_run_length")
            eps = row.get("endpoints", {})
            for mode in ENDPOINTS:
                verdict, observed = expected_stop(word, mode)
                actual = eps.get(mode, {})
                if actual.get("verdict") != verdict:
                    errors.append("endpoint_verdict")
                if actual.get("observed") != observed or actual.get("censored") != n - observed:
                    errors.append("censoring")
                if actual.get("retained_in_denominator") is not True:
                    errors.append("denominator_loss")
                if verdict == "SURVIVE":
                    survival[(name, n, mode)] += p
                observed_sessions[(name, n, mode)] += 1
        except Exception:
            errors.append("malformed_row")

    if seen != expected_keys:
        errors.append("path_population")
    for (name, n), total in totals.items():
        if total != 1:
            errors.append("mass_not_one")
    for key, mass in marginal_f.items():
        if mass != START_FAILURE:
            errors.append("marginal_not_stationary")
    for count in observed_sessions.values():
        if count <= 0:
            errors.append("empty_denominator")

    # Oracle check: one-step dynamic program, independent of path classification.
    for name, trans in TRANSITIONS.items():
        for n in N_VALUES:
            states = {("S", 0): 1 - START_FAILURE, ("F", 1): START_FAILURE}
            for _ in range(1, n):
                nxt = {}
                for (last, streak), mass in states.items():
                    pf = trans[last]
                    for current, pc in (("S", 1 - pf), ("F", pf)):
                        if streak >= 2:
                            new_streak = 2  # absorbing terminal burst state
                        else:
                            new_streak = streak + 1 if current == "F" else 0
                        nxt[(current, new_streak)] = nxt.get((current, new_streak), Fraction(0)) + mass * pc
                states = nxt
            # Absorbing-failure probability: survival requires initial S and
            # every subsequent transition to remain S.
            no_failure = (1 - START_FAILURE) * (1 - trans["S"]) ** (n - 1)
            no_burst = sum(m for (last, streak), m in states.items() if streak < 2)
            if survival[(name, n, "any_failure")] != no_failure:
                errors.append("any_failure_oracle")
            if survival[(name, n, "failure_burst_2")] != no_burst:
                errors.append("burst_oracle")

    return errors


def corruption_controls(data):
    outcomes = {}
    cases = {}
    for name, mutate in {
        "drop_path": lambda d: d["rows"].pop(0),
        "duplicate_path": lambda d: d["rows"].append(copy.deepcopy(d["rows"][0])),
        "change_probability": lambda d: d["rows"][0].__setitem__("probability", "999/1000"),
        "erase_censoring": lambda d: next(r["endpoints"]["any_failure"].__setitem__("censored", 0) for r in d["rows"] if r["endpoints"]["any_failure"]["censored"] > 0),
        "drop_failed_session_denominator": lambda d: next(r["endpoints"]["any_failure"].__setitem__("retained_in_denominator", False) for r in d["rows"] if "F" in r["path"]),
    }.items():
        damaged = copy.deepcopy(data)
        mutate(damaged)
        cases[name] = bool(audit(damaged))
    return cases


def summarize(data):
    result = {}
    for name in TRANSITIONS:
        result[name] = {}
        for n in N_VALUES:
            selected = [r for r in data["rows"] if r["kernel"] == name and r["n"] == n]
            result[name][str(n)] = {
                mode: str(sum((Fraction(r["probability"]) for r in selected if r["endpoints"][mode]["verdict"] == "SURVIVE"), Fraction(0)))
                for mode in ENDPOINTS
            }
    return result


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as stream:
        data = json.load(stream)
    errors = audit(data)
    controls = corruption_controls(data) if not errors else {}
    print(json.dumps({"audit": "PASS" if not errors and all(controls.values()) else "FAIL",
                      "errors": errors, "controls_rejected": controls,
                      "survival": summarize(data)}, sort_keys=True, separators=(",", ":")))
    sys.exit(0 if not errors and all(controls.values()) else 1)
