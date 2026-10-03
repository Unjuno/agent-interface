"""Finite possible-time oracle and adversarial retained-input controls."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

import intervals as producer


def check(condition, name):
    if not condition:
        raise RuntimeError("control-failed:" + name)


def reject(call, name):
    try:
        call()
    except (producer.Invalid, KeyError, OSError, TypeError, json.JSONDecodeError):
        return {"name": name, "rejected": True}
    raise RuntimeError("accepted-corruption:" + name)


def oracle_controls():
    cases = 0
    for lower in range(7):
        for upper in range(lower, 7):
            for deadline in range(7):
                possible = {t <= deadline for t in range(lower, upper + 1)}
                expected = "UNRESOLVED" if len(possible) == 2 else (
                    "CERTIFIED_ON_TIME" if True in possible else "CERTIFIED_LATE")
                check(producer.classify(lower, upper, deadline) == expected, "possible-time")
                cases += 1
    # Two possible worlds have identical recorded endpoints; the point-endpoint rule invents a miss.
    worlds = {t: t <= 2 for t in range(1, 4)}
    check(set(worlds.values()) == {True, False} and producer.classify(1, 3, 2) == "UNRESOLVED",
          "upper-endpoint-negative-control")
    bad = [(True, 2, 1), (0, False, 1), (0, 2, True), (0.0, 2, 1),
           (0, 2.0, 1), (0, 2, 1.0), ("0", 2, 1), (None, 2, 1), (-1, 2, 1), (2, 1, 1)]
    rejections = [reject(lambda values=values: producer.classify(*values), "invalid-interval-" + str(i))
                  for i, values in enumerate(bad)]
    rejections.append(reject(lambda: producer.strict_load('{"x":1,"x":2}'), "duplicate-json-key"))
    rejections.append(reject(lambda: producer.strict_load('{"x":NaN}'), "nonfinite-json"))
    check(not producer.typed_equal({"x": True}, {"x": 1}), "bool-int-alias")
    check(not producer.typed_equal({"x": 1.0}, {"x": 1}), "float-int-alias")
    return {"possible_time_fixtures": cases, "upper_endpoint_negative_control": "REJECTED_AS_DEFINITE_MISS",
            "type_and_json_rejections": rejections}


def retained_controls(selected):
    raw = producer.RAW
    trials = producer.strict_load(selected[raw + "formal-trials.json"])
    events = [producer.strict_load(line) for line in selected[raw + "app-events.jsonl"].splitlines() if line]
    deadlines = {t["trial_id"]: producer.strict_load(selected[raw + f"deadline-{t['trial_id']}.json"])
                 for t in trials}
    effects = {t["trial_id"]: producer.strict_load(selected[raw + f"effect-{t['trial_id']}.json"])
               for t in trials}
    receipt = producer.strict_load(selected[raw + "candidate-receipt.json"])
    positive = producer.validate_records(trials, events, deadlines, effects, receipt)
    check(len(positive) == 180, "retained-positive-control")
    cases = []
    def mutation(name, change):
        bundle = copy.deepcopy([trials, events, deadlines, effects, receipt])
        change(bundle)
        cases.append(reject(lambda: producer.validate_records(*bundle), name))
    tid = trials[0]["trial_id"]
    def event(bundle, kind):
        return next(e for e in bundle[1] if e["kind"] == kind and e.get("trial_id") == tid)
    mutation("duplicate-trial-id", lambda b: b[0].__setitem__(1, copy.deepcopy(b[0][0])))
    mutation("missing-action", lambda b: b[1].remove(event(b, "action_effect")))
    mutation("duplicate-action", lambda b: b[1].append(copy.deepcopy(event(b, "action_effect"))))
    mutation("inverted-interval", lambda b: event(b, "action_effect").update(
        action_ns=event(b, "action_effect")["persisted_ns"] + 1))
    mutation("boolean-time", lambda b: event(b, "action_effect").update(action_ns=True))
    mutation("float-upper-time", lambda b: event(b, "action_effect").update(
        persisted_ns=float(event(b, "action_effect")["persisted_ns"])))
    mutation("wrong-deadline", lambda b: b[2][tid].update(deadline_ns=b[2][tid]["deadline_ns"] + 1))
    mutation("shifted-origin", lambda b: event(b, "trial_start").update(
        start_ns=event(b, "trial_start")["start_ns"] + 1))
    mutation("missing-effect", lambda b: b[3].pop(tid))
    mutation("wrong-effect-payload", lambda b: b[3][tid].update(value="wrong"))
    mutation("boolean-snapshot-time", lambda b: b[2][tid].update(snapshot_ns=True))
    mutation("integer-effect-present", lambda b: b[2][tid].update(effect_present=1))
    mutation("wrong-snapshot-payload", lambda b: b[2][tid].update(effect_payload={"trial_id": tid, "value": 1}))
    mutation("deadline-event-disagreement", lambda b: event(b, "deadline_observed").update(
        snapshot_ns=event(b, "deadline_observed")["snapshot_ns"] + 1))
    mutation("boolean-exit-code", lambda b: b[4].update(exit_code=False))
    mutation("float-receipt-count", lambda b: b[4].update(trial_count=180.0))
    mutation("unbound-action-path", lambda b: event(b, "action_effect").update(effect_path="effect-other.json"))
    mutation("wrong-allocation-delay", lambda b: b[0][0].update(action_delay_ms=89))
    return {"positive_rows": len(positive), "retained_corruptions": cases}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--freeze", type=Path)
    args = parser.parse_args()
    result = oracle_controls()
    if args.inputs is not None:
        freeze = producer.strict_load(args.freeze.read_bytes())
        selected = producer.verify_inputs(args.inputs, args.manifest, freeze)
        result.update(retained_controls(selected))
        wrong = dict(freeze, input_manifest_sha256="0" * 64)
        result["custody_controls"] = [reject(lambda: producer.verify_inputs(args.inputs, args.manifest, wrong),
                                             "wrong-manifest-digest")]
        # In-memory changes exercise the checksum predicate; no original input is modified.
        item = producer.strict_load(args.manifest.read_bytes())["files"][0]
        damaged = selected[item["path"]] + b"\n"
        check(hashlib.sha256(damaged).hexdigest() != item["sha256"], "changed-source-bytes")
        result["changed_source_checksum_control"] = "DETECTED"
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
