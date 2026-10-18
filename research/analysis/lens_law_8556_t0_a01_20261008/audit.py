"""Independent truth-table audit; intentionally does not import candidate.py."""

import argparse
import hashlib
import json
from pathlib import Path


def canonical_digest(fixture):
    encoded = json.dumps(fixture, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _view(state, fields):
    return {key: state.get(key) for key in fields}


def _semantic_equal(left, right, keys):
    return all(left.get(key) == right.get(key) for key in keys)


def _enabled(state, op):
    return bool(state.get("can_update")) if op["mode"] == "conditional_set" else True


def _transition(state, requested, op):
    result = dict(state)
    mode, target = op["mode"], op["target"]
    if mode == "set":
        result[target] = requested[target]
    elif mode == "wrong_field":
        result[target] = requested[op["input_field"]]
    elif mode == "ignored":
        return result
    elif mode == "duplicate_callback":
        result[target] = requested[target]
        result["callback_count"] = result.get("callback_count", 0) + 1
    elif mode == "first_write_wins":
        if not result.get("accepted", False):
            result[target] = requested[target]
            result["accepted"] = True
    elif mode == "conditional_set":
        if result.get("can_update", False):
            result[target] = requested[target]
    elif mode == "increment":
        result[target] = result.get(target, 0) + 1
    else:
        raise ValueError("unsupported operation in frozen fixture")
    return result


def _truth(case):
    op = case["operation"]
    if case["observed_epoch"] != case["current_epoch"]:
        return {"case_id": case["id"], "status": "UNKNOWN", "reason": "STALE_EPOCH", "laws": None, "baselines": None}
    if case["completion"] != "complete":
        return {"case_id": case["id"], "status": "UNKNOWN", "reason": "COMPLETION_PENDING", "laws": None, "baselines": None}
    if not op["declared_total"]:
        return {"case_id": case["id"], "status": "NOT_APPLICABLE", "reason": "PARTIAL_DOMAIN", "laws": None, "baselines": None}
    if not op["declared_idempotent"]:
        return {"case_id": case["id"], "status": "NOT_APPLICABLE", "reason": "NON_IDEMPOTENT", "laws": None, "baselines": None}
    if not op["declared_side_effect_free"]:
        return {"case_id": case["id"], "status": "NOT_APPLICABLE", "reason": "EVENTFUL_OPERATION", "laws": None, "baselines": None}

    cells = {}
    for state in case["worlds"]:
        key = tuple(sorted(_view(state, case["view_fields"]).items()))
        cells.setdefault(key, set()).add(_enabled(state, op))
    if any(len(choices) > 1 for choices in cells.values()):
        return {"case_id": case["id"], "status": "UNKNOWN", "reason": "AMBIGUOUS_APPLICABILITY", "laws": None, "baselines": None}

    gp = pg = pp = label = replay = True
    for state in case["worlds"]:
        current = _view(state, case["view_fields"])
        get_put_state = _transition(state, current, op)
        once = _transition(state, case["requested_view"], op)
        twice = _transition(_transition(state, current, op), case["requested_view"], op)
        direct = _transition(state, case["requested_view"], op)
        gp = gp and _semantic_equal(state, get_put_state, case["semantic_fields"])
        pg = pg and _view(once, case["view_fields"]) == case["requested_view"]
        pp = pp and _semantic_equal(twice, direct, case["semantic_fields"])
        label = label and _view(once, case["view_fields"]) == case["requested_view"]
        replay = replay and _transition(state, case["requested_view"], op) == _transition(state, case["requested_view"], op)
    laws = {"get_put": gp, "put_get": pg, "put_put": pp}
    status = "PASS" if all(laws.values()) else "VIOLATION"
    return {"case_id": case["id"], "status": status, "reason": None if status == "PASS" else "SCOPED_LENS_LAW_VIOLATION",
            "laws": laws, "baselines": {"final_label_only": label, "replay_consistency": replay}}


def audit(fixture, candidate, supplied_digest, sealed):
    digest = canonical_digest(fixture)
    if digest != supplied_digest:
        raise ValueError("fixture digest mismatch")
    if fixture.get("schema") != "lens-law-finite-fixture-v1" or sealed.get("schema") != "lens-law-sealed-truth-v1":
        raise ValueError("unexpected schema")
    expected = [_truth(case) for case in fixture["cases"]]
    if expected != sealed["rows"]:
        raise ValueError("sealed truth does not match independently reconstructed fixture semantics")
    if candidate.get("rows") != expected:
        raise ValueError("candidate rows differ from independent truth")
    if len({row["case_id"] for row in expected}) != len(expected):
        raise ValueError("duplicate case ids")

    # Four positive controls must all be rejected by the same validation boundary.
    controls = []
    missing = json.loads(json.dumps(candidate))
    missing["rows"].pop()
    controls.append(missing)
    false_pp = json.loads(json.dumps(candidate))
    false_pp["rows"][5]["laws"]["put_put"] = True
    controls.append(false_pp)
    stale_digest_fixture = json.loads(json.dumps(fixture))
    stale_digest_fixture["cases"][0]["requested_view"]["value"] = "C"
    controls.append((stale_digest_fixture, candidate, digest, sealed))
    wrong_truth = json.loads(json.dumps(sealed))
    wrong_truth["rows"][0]["laws"]["put_put"] = False
    controls.append((fixture, candidate, supplied_digest, wrong_truth))
    rejected = 0
    for control in controls:
        try:
            if isinstance(control, tuple):
                audit(*control)
            else:
                audit(fixture, control, supplied_digest, sealed)
        except ValueError:
            rejected += 1
    if rejected != 4:
        raise ValueError("mutation controls were not all rejected")
    return {"status": "PASS_LENS_LAW_METHOD_SCOPED", "input_sha256": digest,
            "rows": len(expected), "mutations_rejected": rejected}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="input.json")
    parser.add_argument("--candidate", default="results/candidate.json")
    parser.add_argument("--truth", default="truth.json")
    parser.add_argument("--output", default="results/audit.json")
    args = parser.parse_args()
    fixture = json.loads(Path(args.input).read_text(encoding="utf-8"))
    candidate = json.loads(Path(args.candidate).read_text(encoding="utf-8"))
    sealed = json.loads(Path(args.truth).read_text(encoding="utf-8"))
    report = audit(fixture, candidate, canonical_digest(fixture), sealed)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, sort_keys=True, separators=(",", ":"))
        stream.write("\n")
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
