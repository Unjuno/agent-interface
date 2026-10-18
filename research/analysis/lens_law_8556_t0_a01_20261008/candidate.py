"""Candidate scoped lens-law checker for finite observation/update fixtures."""

import argparse
import json
from pathlib import Path


def _project(state, fields):
    return {field: state.get(field) for field in fields}


def _equivalent(left, right, fields):
    return all(left.get(field) == right.get(field) for field in fields)


def _applicable(state, operation):
    if operation["mode"] == "conditional_set":
        return bool(state.get("can_update"))
    return True


def _apply(state, requested, operation):
    updated = dict(state)
    mode = operation["mode"]
    target = operation["target"]

    if mode == "set":
        updated[target] = requested[target]
    elif mode == "wrong_field":
        updated[target] = requested[operation["input_field"]]
    elif mode == "ignored":
        pass
    elif mode == "duplicate_callback":
        updated[target] = requested[target]
        updated["callback_count"] = updated.get("callback_count", 0) + 1
    elif mode == "first_write_wins":
        if not updated.get("accepted", False):
            updated[target] = requested[target]
            updated["accepted"] = True
    elif mode == "conditional_set":
        if updated.get("can_update", False):
            updated[target] = requested[target]
    elif mode == "increment":
        updated[target] = updated.get(target, 0) + 1
    else:
        raise ValueError("unknown operation mode: " + repr(mode))

    return updated


def _ambiguous_projection(worlds, fields, operation):
    cells = {}
    for world in worlds:
        view_key = tuple(sorted(_project(world, fields).items()))
        cells.setdefault(view_key, set()).add(_applicable(world, operation))
    return any(len(applicability) > 1 for applicability in cells.values())


def classify(case):
    if case["observed_epoch"] != case["current_epoch"]:
        return {
            "case_id": case["id"],
            "status": "UNKNOWN",
            "reason": "STALE_EPOCH",
            "laws": None,
            "baselines": None,
        }
    if case["completion"] != "complete":
        return {
            "case_id": case["id"],
            "status": "UNKNOWN",
            "reason": "COMPLETION_PENDING",
            "laws": None,
            "baselines": None,
        }

    operation = case["operation"]
    if not operation["declared_total"]:
        return {
            "case_id": case["id"],
            "status": "NOT_APPLICABLE",
            "reason": "PARTIAL_DOMAIN",
            "laws": None,
            "baselines": None,
        }
    if not operation["declared_idempotent"]:
        return {
            "case_id": case["id"],
            "status": "NOT_APPLICABLE",
            "reason": "NON_IDEMPOTENT",
            "laws": None,
            "baselines": None,
        }
    if not operation["declared_side_effect_free"]:
        return {
            "case_id": case["id"],
            "status": "NOT_APPLICABLE",
            "reason": "EVENTFUL_OPERATION",
            "laws": None,
            "baselines": None,
        }

    worlds = case["worlds"]
    fields = case["view_fields"]
    semantic_fields = case["semantic_fields"]
    requested = case["requested_view"]
    if _ambiguous_projection(worlds, fields, operation):
        return {
            "case_id": case["id"],
            "status": "UNKNOWN",
            "reason": "AMBIGUOUS_APPLICABILITY",
            "laws": None,
            "baselines": None,
        }

    get_put = True
    put_get = True
    put_put = True
    final_label_only = True
    replay_consistency = True

    for source in worlds:
        current_view = _project(source, fields)
        get_then_put = _apply(source, current_view, operation)
        requested_once = _apply(source, requested, operation)
        requested_twice = _apply(
            _apply(source, current_view, operation), requested, operation
        )
        requested_direct = _apply(source, requested, operation)

        get_put = get_put and _equivalent(source, get_then_put, semantic_fields)
        put_get = put_get and _project(requested_once, fields) == requested
        put_put = put_put and _equivalent(
            requested_twice, requested_direct, semantic_fields
        )
        final_label_only = (
            final_label_only
            and _project(requested_once, fields) == requested
        )
        replay_a = _apply(source, requested, operation)
        replay_b = _apply(source, requested, operation)
        replay_consistency = (
            replay_consistency and replay_a == replay_b
        )

    laws = {
        "get_put": get_put,
        "put_get": put_get,
        "put_put": put_put,
    }
    status = "PASS" if all(laws.values()) else "VIOLATION"
    return {
        "case_id": case["id"],
        "status": status,
        "reason": None if status == "PASS" else "SCOPED_LENS_LAW_VIOLATION",
        "laws": laws,
        "baselines": {
            "final_label_only": final_label_only,
            "replay_consistency": replay_consistency,
        },
    }


def run(fixture):
    return {"rows": [classify(case) for case in fixture["cases"]]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="input.json")
    parser.add_argument("--output", default="results/candidate.json")
    args = parser.parse_args()
    fixture = json.loads(Path(args.input).read_text(encoding="utf-8"))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(run(fixture), stream, sort_keys=True, separators=(",", ":"))
        stream.write("\n")
    print(json.dumps({"cases": len(fixture["cases"]), "status": "CANDIDATE_COMPLETE"},
                     sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
