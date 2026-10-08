#!/usr/bin/env python3
"""One-shot exact summaries of the immutable #8319 A01 factorial raw."""
import hashlib
from fractions import Fraction
import json
from pathlib import Path
import sys

EXPECTED_SHA256 = "ecffd8121a289d3533c94373c8f7aba50d9c349ffd5db534e46db16522897e9d"
UPDATERS = ("CASE_PATCH", "STRATUM_PATCH")
FEEDBACKS = ("CONTROLLED", "FULL")
METRICS = ("dev_accuracy", "fresh_accuracy", "optimism")
SEEDS = tuple(range(100))


def exact_int(row, key):
    value = row.get(key)
    if type(value) is not int:
        raise ValueError(f"{key} must be an exact integer")
    return value


def validate_rows(rows):
    if type(rows) is not list or len(rows) != 400:
        raise ValueError("expected exactly 400 rows")
    indexed = {}
    for row in rows:
        if type(row) is not dict:
            raise ValueError("row must be an object")
        updater, feedback = row.get("updater"), row.get("feedback")
        seed = exact_int(row, "seed")
        key = updater, feedback, seed
        if updater not in UPDATERS or feedback not in FEEDBACKS or seed not in SEEDS or key in indexed:
            raise ValueError("invalid or duplicate cell/seed")
        dev_n, fresh_n = exact_int(row, "dev_total"), exact_int(row, "fresh_total")
        dev_k, fresh_k = exact_int(row, "dev_correct"), exact_int(row, "fresh_correct")
        if dev_n != 32 or fresh_n != 32 or not (0 <= dev_k <= dev_n and 0 <= fresh_k <= fresh_n):
            raise ValueError("outcome denominator or numerator invalid")
        if (exact_int(row, "query_count") != 5 or exact_int(row, "safety_veto_count") != 1 or
            row.get("candidate_locked_before_fresh") is not True or row.get("raw_released_after_lock") is not True):
            raise ValueError("protocol invariant mismatch")
        optimism = Fraction(str(row.get("optimism")))
        if optimism != Fraction(dev_k - fresh_k, 32):
            raise ValueError("optimism does not equal development minus fresh")
        indexed[key] = row
    expected = {(u, f, s) for u in UPDATERS for f in FEEDBACKS for s in SEEDS}
    if set(indexed) != expected:
        raise ValueError("factorial frame incomplete")
    return indexed


def metric(row, name):
    if name == "dev_accuracy": return Fraction(row["dev_correct"], row["dev_total"])
    if name == "fresh_accuracy": return Fraction(row["fresh_correct"], row["fresh_total"])
    if name == "optimism": return Fraction(str(row["optimism"]))
    raise ValueError("unknown metric")


def distribution(values):
    if len(values) != 100: raise ValueError("each vector must have 100 values")
    ordered = sorted(values)
    return {"n": 100, "mean_fraction": str(sum(values, Fraction()) / 100),
            "median_fraction": str((ordered[49] + ordered[50]) / 2),
            "min_fraction": str(ordered[0]), "max_fraction": str(ordered[-1]),
            "positive": sum(x > 0 for x in values), "zero": sum(x == 0 for x in values),
            "negative": sum(x < 0 for x in values)}


def summarize(rows, digest):
    index = validate_rows(rows)
    cells = {}
    for updater in UPDATERS:
        cells[updater] = {}
        for feedback in FEEDBACKS:
            group = [index[(updater, feedback, seed)] for seed in SEEDS]
            cells[updater][feedback] = {"n": len(group), "safety_vetoes": sum(r["safety_veto_count"] for r in group),
                "metrics": {m: distribution([metric(r, m) for r in group]) for m in METRICS}}
    feedback = {u: {m: distribution([metric(index[(u,"FULL",s)],m)-metric(index[(u,"CONTROLLED",s)],m) for s in SEEDS]) for m in METRICS} for u in UPDATERS}
    updater = {f: {m: distribution([metric(index[("CASE_PATCH",f,s)],m)-metric(index[("STRATUM_PATCH",f,s)],m) for s in SEEDS]) for m in METRICS} for f in FEEDBACKS}
    interaction = {m: distribution([(metric(index[("CASE_PATCH","FULL",s)],m)-metric(index[("CASE_PATCH","CONTROLLED",s)],m))-(metric(index[("STRATUM_PATCH","FULL",s)],m)-metric(index[("STRATUM_PATCH","CONTROLLED",s)],m)) for s in SEEDS]) for m in METRICS}
    return {"schema":"feedback-update-rule-factorial-analysis-v1", "input_sha256":digest, "rows":400,
            "seeds_per_cell":100, "cell_summaries":cells,
            "feedback_full_minus_controlled_within_updater":feedback,
            "update_case_minus_stratum_within_feedback":updater,
            "interaction_case_minus_stratum_of_feedback_effect":interaction,
            "inference":"finite authored 100-seed fixture only; no p-value or population inference"}


def write_result(input_path, output_path):
    raw = input_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_SHA256: raise ValueError("immutable A01 raw SHA-256 mismatch")
    result = summarize(json.loads(raw.decode("utf-8")), digest)
    if not output_path.parent.is_dir(): raise FileNotFoundError("frozen output parent directory missing")
    if output_path.exists(): raise ValueError("refusing to overwrite existing result")
    output_path.write_text(json.dumps(result, sort_keys=True, indent=2)+"\n", encoding="utf-8", newline="\n")
    return result


def main(argv):
    if len(argv) != 3:
        print("usage: analyze.py IMMUTABLE_RAW.json ANALYSIS.json", file=sys.stderr); return 2
    try: result = write_result(Path(argv[1]), Path(argv[2]))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"STOP_ANALYSIS_INPUT_OR_CONTRACT: {type(exc).__name__}: {exc}", file=sys.stderr); return 1
    print(json.dumps({"status":"PASS_ANALYSIS_SCOPED","rows":result["rows"],"input_sha256":result["input_sha256"]},sort_keys=True)); return 0

if __name__ == "__main__": raise SystemExit(main(sys.argv))
