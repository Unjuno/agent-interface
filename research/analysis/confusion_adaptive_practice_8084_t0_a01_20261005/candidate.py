#!/usr/bin/env python3
"""Synthetic schedule generator for Issue #8084 T0."""
import functools, json, random, sys


def eligible(values, minimum_span, minimum_peak):
    return max(values)-min(values) >= minimum_span and max(values) >= minimum_peak


def highest_pair(pair_order, values):
    best = max(range(len(values)), key=lambda i: (values[i], -i))
    return pair_order[best]


def random_order(variants, attempts, run_cap, seed):
    items = [v for v in variants for _ in range(attempts)]
    rng = random.Random(seed)
    for _ in range(10000):
        rng.shuffle(items)
        run = 1
        if all(not (items[i] == items[i-1] == items[i-2]) for i in range(2, len(items))):
            return list(items)
    raise RuntimeError("bounded schedule generator exhausted")


def adaptive_order(variants, attempts, run_cap, target_pair):
    target_pair = tuple(target_pair)
    @functools.lru_cache(None)
    def solve(counts, last, run):
        if sum(counts) == 0: return (0, ())
        best = None
        for i, variant in enumerate(variants):
            if counts[i] == 0 or (variant == last and run >= run_cap): continue
            rest = list(counts); rest[i] -= 1
            next_run = run+1 if variant == last else 1
            reward = int((last, variant) == target_pair or (variant, last) == target_pair)
            score, tail = solve(tuple(rest), variant, next_run)
            option = (reward+score, (variant,)+tail)
            if best is None or option[0] > best[0] or (option[0] == best[0] and option[1] < best[1]): best = option
        if best is None: return (-10**6, ())
        return best
    result = solve(tuple(attempts for _ in variants), "", 0)[1]
    if len(result) != len(variants)*attempts: raise RuntimeError("no balanced adaptive order")
    return list(result)


def build(cases, scoring):
    output=[]; gate=cases["eligibility"]
    for index, case in enumerate(cases["cases"]):
        variants, values = case["variants"], case["confusion"]
        ok = eligible(values, gate["minimum_span"], gate["minimum_peak"])
        pair = highest_pair(cases["pair_order"], values)
        baseline = random_order(variants, cases["attempts_per_variant"], cases["max_identical_run"], index+101)
        adaptive = adaptive_order(variants, cases["attempts_per_variant"], cases["max_identical_run"], pair) if ok else baseline
        output.append({"case_id":case["id"], "eligible":ok, "confusion_span":max(values)-min(values),
                       "peak_confusion":max(values), "target_pair":pair,
                       "random":baseline, "adaptive":adaptive,
                       "adaptive_mode":"ADAPTIVE" if ok else "NEUTRAL_FALLBACK"})
    return {"schema":"issue8084-practice-t0-v1", "rows":output,
            "scoring_controls":[{"id":x["id"],"score":score_trace(x, scoring)} for x in scoring["traces"]]}


def score_trace(trace, oracle):
    family=set(oracle["family"])
    if trace["intent"] not in family: return "UNKNOWN_OUTSIDE_FAMILY"
    if trace["observed_target"] != trace["intent"]: return "REJECT_WRONG_TARGET"
    if trace["observed_effect"] != oracle["expected_effect"][trace["intent"]]: return "REJECT_FALSE_SUCCESS"
    if trace["success_claim"] is not True: return "NO_SUCCESS_CLAIM"
    return "VALID_EXACT_EFFECT"


if __name__ == "__main__":
    with open("cases.json", encoding="utf-8") as f: cases=json.load(f)
    with open("scoring_cases.json", encoding="utf-8") as f: scoring=json.load(f)
    result=build(cases, scoring)
    json.dump(result, sys.stdout, sort_keys=True, separators=(",",":")); print()
