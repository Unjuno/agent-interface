"""Raw-only exact denominator audit for the frozen #4295 formal stream."""
import argparse
import json
from pathlib import Path


SCHEDULES = {
    "STABLE_BASE",
    "SUPPORT_VERSION_CHANGE",
    "PRODUCER_GENERATION_CHANGE",
    "NOVEL_INPUT",
    "REQUIRED_UNKNOWN",
    "INCOMPLETE_SUPPORT",
    "CORRUPT_REGENERATION",
    "RECOVER_COMPLETE_NEW_VERSION",
}
REPETITIONS = {10, 11}
INDICES = set(range(8))


def audit(data):
    errors = []
    if type(data) is not dict or data.get("mode") != "formal":
        return {"decision": "STOP_COMPLETENESS", "errors": ["mode"]}
    rows = data.get("rows")
    if type(rows) is not list or len(rows) != 128:
        return {"decision": "STOP_COMPLETENESS", "errors": ["row_count"]}

    observed = set()
    for row in rows:
        if type(row) is not dict:
            errors.append("row_type")
            continue
        schedule, rep, index = row.get("schedule"), row.get("rep"), row.get("index")
        if type(schedule) is not str or schedule not in SCHEDULES:
            errors.append("schedule")
            continue
        if type(rep) is not int or rep not in REPETITIONS:
            errors.append("repetition")
            continue
        if type(index) is not int or index not in INDICES:
            errors.append("index")
            continue
        key = (schedule, rep, index)
        if key in observed:
            errors.append("duplicate")
        observed.add(key)

    expected = {
        (schedule, rep, index)
        for schedule in SCHEDULES
        for rep in REPETITIONS
        for index in INDICES
    }
    if observed != expected:
        errors.append("coverage")
    return {
        "decision": "PASS_EXACT_FORMAL_DENOMINATOR" if not errors else "STOP_COMPLETENESS",
        "errors": errors,
        "rows": len(rows),
        "unique_cases": len(observed),
        "expected_cases": len(expected),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("raw")
    parser.add_argument("out")
    args = parser.parse_args()
    result = audit(json.loads(Path(args.raw).read_text()))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if not result["errors"] else 1)


if __name__ == "__main__":
    main()
