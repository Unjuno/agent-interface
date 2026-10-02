from __future__ import annotations

import copy
import hashlib
import json
import os
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
ALLOC = "ACTION-BOUND-RESIDUALS-6619-T0-WSLC-20261002-01"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pixels(frame):
    return [v for row in frame for v in row]


def translate(source, w, h, dx):
    out = []
    for y in range(h):
        for x in range(w):
            old_x = x - dx
            out.append(source[y * w + old_x] if 0 <= old_x < w else 0)
    return out


def differences(left, right):
    return [position for position in range(len(left)) if left[position] != right[position]]


def independently_valid(receipt, case):
    if not isinstance(receipt, dict):
        return False, "missing_receipt"
    if receipt.get("intent_id") != case.get("intent_id"):
        return False, "intent_mismatch"
    if receipt.get("viewport_generation") != case.get("viewport_generation"):
        return False, "viewport_generation_mismatch"
    if receipt.get("focus_generation") != case.get("focus_generation"):
        return False, "focus_generation_mismatch"
    if receipt.get("delivery_status") != "delivered":
        return False, "delivery_not_confirmed"
    rq, ack, release, captured = (receipt.get("request_ns"), receipt.get("ack_ns"),
                                  receipt.get("release_ns"), case.get("capture_ns"))
    if not all(type(x) is int for x in (rq, ack, release, captured)):
        return False, "receipt_time_missing"
    if not (rq <= ack <= captured <= release):
        return False, "receipt_not_current_at_capture"
    support = receipt.get("allowed_dx")
    if (type(support) is not list or len(support) == 0 or
            not all(type(v) is int and -4 <= v <= 4 for v in support) or
            len(set(support)) != len(support)):
        return False, "transform_support_invalid"
    kind = receipt.get("action")
    if kind not in {"pan_right", "no_input"}:
        return False, "action_class_unknown"
    if kind == "no_input" and support != [0]:
        return False, "no_input_support_mismatch"
    return True, "bound"


def expected_methods(case):
    w, h = case["width"], case["height"]
    before, after = pixels(case["previous"]), pixels(case["current"])
    if len(before) != w * h or len(after) != w * h:
        raise ValueError("bad_raster_shape")
    delta = differences(before, after)
    critical = {y * w + x for x, y in case["critical_pixels"]}
    critical_delta = sorted(pos for pos in critical
                            if before[pos] != 255 and after[pos] == 255)
    raw = {"alarm": bool(delta), "residual_indices": delta,
           "predicted_indices": [],
           "critical_delta_indices": critical_delta,
           "fallback": "FULL_FRAME" if delta else "NONE"}

    best_dx, best_residual = None, None
    for offset in sorted(range(-4, 5), key=lambda v: (abs(v), v)):
        residual = differences(translate(before, w, h, offset), after)
        if best_residual is None or len(residual) < len(best_residual):
            best_dx, best_residual = offset, residual
    registration = {"alarm": bool(best_residual or critical_delta),
                    "selected_dx": best_dx, "residual_indices": best_residual,
                    "predicted_indices": sorted(set(delta).difference(best_residual)),
                    "critical_delta_indices": critical_delta, "fallback": "NONE"}

    def bound(receipt):
        is_valid, why = independently_valid(receipt, case)
        if not is_valid:
            return {"alarm": bool(delta), "residual_indices": delta,
                    "predicted_indices": [],
                    "critical_delta_indices": critical_delta,
                    "fallback": "UNKNOWN_FULL_FRAME", "binding": why,
                    "allowed_dx": None}
        predicted_frames = [translate(before, w, h, offset) for offset in receipt["allowed_dx"]]
        residual = []
        for pos in delta:
            predictions_at_pixel = [image[pos] for image in predicted_frames]
            if any(value != predictions_at_pixel[0] for value in predictions_at_pixel[1:]):
                residual.append(pos)
            elif after[pos] != predictions_at_pixel[0]:
                residual.append(pos)
        return {"alarm": bool(residual or critical_delta),
                "residual_indices": residual,
                "predicted_indices": sorted(set(delta).difference(residual)),
                "critical_delta_indices": critical_delta,
                "fallback": "NONE", "binding": "bound",
                "allowed_dx": receipt["allowed_dx"]}

    return {"raw_delta": raw, "global_registration": registration,
            "action_bound": bound(case["receipt"]),
            "sham_bound": bound(case["sham_receipt"])}, delta


def audit(raw, inputs, oracle, freeze):
    errors = []
    def check(ok, label):
        if not ok:
            errors.append(label)

    check(raw.get("schema") == "action-bound-residual-candidate-v1", "schema")
    check(raw.get("allocation_id") == ALLOC, "allocation")
    check(raw.get("candidate_status") == "PASS_CANDIDATE_SHAPE" and
          raw.get("candidate_completed") is True and raw.get("candidate_errors") == [], "candidate_state")
    check(raw.get("image_id") == freeze.get("image_id"), "image_id")
    check(raw.get("inputs_sha256") == sha(HERE / "fixture" / "inputs.json"), "inputs_hash")
    check(raw.get("oracle_sha256") == sha(HERE / "fixture" / "oracle.json"), "oracle_hash")
    check(raw.get("candidate_sha256") == freeze.get("source_sha256", {}).get("candidate.py"), "candidate_hash")
    for name in ("candidate.py", "audit.py", "make_fixture.py", "PREREGISTRATION.md"):
        check(freeze.get("source_sha256", {}).get(name) == sha(HERE / name), f"frozen_source:{name}")
    check(freeze.get("inputs_sha256") == sha(HERE / "fixture" / "inputs.json"), "freeze_inputs_hash")
    check(freeze.get("oracle_sha256") == sha(HERE / "fixture" / "oracle.json"), "freeze_oracle_hash")
    check(raw.get("capture_budget_per_case") == 1, "budget")
    check(inputs.get("schema") == "action-bound-residual-input-v1", "input_schema")
    check(oracle.get("schema") == "action-bound-residual-oracle-v1", "oracle_schema")
    cases = inputs.get("cases")
    truths = oracle.get("cases")
    rows = raw.get("rows")
    check(type(cases) is list and type(truths) is list and type(rows) is list, "lists")
    if not (type(cases) is list and type(truths) is list and type(rows) is list):
        return errors, {}
    check(len(cases) == 16 and len(rows) == 16 and len(truths) == 16, "case_denominator")
    expected_ids = [c.get("case_id") for c in cases]
    check(len(set(expected_ids)) == len(expected_ids), "input_unique_ids")
    check([r.get("case_id") for r in rows] == expected_ids, "row_identity_order")
    truth_map = {r.get("case_id"): r.get("events") for r in truths}
    check(len(truth_map) == len(truths) and set(truth_map) == set(expected_ids), "oracle_roster")

    recomputed = {}
    for case, row in zip(cases, rows):
        cid = case["case_id"]
        try:
            methods, delta = expected_methods(case)
        except Exception as exc:
            check(False, f"reconstruct:{cid}:{type(exc).__name__}")
            continue
        recomputed[cid] = methods
        check(row.get("intent_id") == case.get("intent_id"), f"intent:{cid}")
        check(row.get("capture_ns") == case.get("capture_ns"), f"capture:{cid}")
        check(row.get("input_receipt") == case.get("receipt") and
              row.get("sham_receipt") == case.get("sham_receipt"), f"receipt_join:{cid}")
        frame_hash = hashlib.sha256(bytes(pixels(case["previous"])) +
                                    bytes(pixels(case["current"]))).hexdigest()
        check(row.get("frame_sha256") == frame_hash, f"frame_hash:{cid}")
        check(row.get("raw_delta_indices") == delta, f"raw_delta:{cid}")
        check(row.get("methods") == methods, f"methods:{cid}")

    # Independent event/deadline scoring from the separate oracle.
    event_roster = []
    missed_critical = []
    for case, row in zip(cases, rows):
        for event in truth_map.get(case["case_id"], []):
            event_roster.append((case["case_id"], event))
            due = event.get("onset_ns", 0) <= case["capture_ns"] <= event.get("deadline_ns", -1)
            for method in ("raw_delta", "global_registration", "action_bound", "sham_bound"):
                observation = row["methods"][method]
                check(not due or observation.get("alarm") is True,
                      f"event_detection:{method}:{event.get('event_id')}")
                if event.get("critical") and method == "action_bound" and not observation.get("alarm"):
                    missed_critical.append(event.get("event_id"))
    check(not missed_critical, "critical_event_loss")
    fallback_expectations = {
        "late_delivery_flash": "receipt_not_current_at_capture",
        "failed_delivery_flash": "delivery_not_confirmed",
        "external_scroll_no_receipt": "missing_receipt",
        "stale_viewport_occlusion": "viewport_generation_mismatch",
        "stale_focus": "focus_generation_mismatch",
    }
    for cid, reason in fallback_expectations.items():
        method = recomputed.get(cid, {}).get("action_bound", {})
        check(method.get("fallback") == "UNKNOWN_FULL_FRAME" and
              method.get("binding") == reason, f"fallback_gate:{cid}")
    for row in rows:
        check(row["methods"]["sham_bound"].get("fallback") == "UNKNOWN_FULL_FRAME" and
              row["methods"]["sham_bound"].get("binding") == "intent_mismatch",
              f"sham_rejected:{row['case_id']}")
    external = next(r for r in rows if r["case_id"] == "external_scroll_no_receipt")
    check(external["methods"]["global_registration"].get("alarm") is False,
          "registration_external_scroll_counterexample")

    # Frozen matched valid-pan contrast. All other cases stay in output and are
    # checked above, but are not silently pooled into this causal-looking slice.
    primary = {"clean_pan_2", "clean_pan_3", "pan_tiny_flash",
               "pan_moving_object", "pan_critical_cue"}
    primary_non_events = {"clean_pan_2", "clean_pan_3"}
    primary_events = {"pan_tiny_flash", "pan_moving_object", "pan_critical_cue"}
    false_raw = sum(bool(next(r for r in rows if r["case_id"] == cid)["methods"]["raw_delta"]["alarm"])
                    for cid in primary_non_events)
    false_bound = sum(bool(next(r for r in rows if r["case_id"] == cid)["methods"]["action_bound"]["alarm"])
                      for cid in primary_non_events)
    recall = {method: sum(bool(next(r for r in rows if r["case_id"] == cid)["methods"][method]["alarm"])
                          for cid in primary_events) for method in ("raw_delta", "action_bound")}
    check(false_bound < false_raw, "primary_false_alarm_reduction")
    check(recall["action_bound"] == recall["raw_delta"], "primary_recall_match")

    counts = {"cases": len(rows), "scheduled_events": len(event_roster),
              "critical_events": sum(bool(event.get("critical")) for _, event in event_roster),
              "primary_cases": len(primary), "primary_false_alarms":
              {"raw_delta": false_raw, "action_bound": false_bound},
              "primary_event_recall": recall,
              "fallback_cases": [r["case_id"] for r in rows
                                 if r["methods"]["action_bound"]["fallback"] == "UNKNOWN_FULL_FRAME"],
              "global_registration_external_scroll_alarm":
              next(r for r in rows if r["case_id"] == "external_scroll_no_receipt")
              ["methods"]["global_registration"]["alarm"],
              "action_bound_external_scroll_fallback":
              next(r for r in rows if r["case_id"] == "external_scroll_no_receipt")
              ["methods"]["action_bound"]["fallback"]}
    return errors, counts


def self_test(raw_path):
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    inputs = json.loads((HERE / "fixture" / "inputs.json").read_text(encoding="utf-8"))
    oracle = json.loads((HERE / "fixture" / "oracle.json").read_text(encoding="utf-8"))
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    base, _ = audit(raw, inputs, oracle, freeze)
    if base:
        return {"status": "FAIL", "base_errors": base, "mutations_rejected": 0, "mutations_total": 5}
    mutations = []
    def mutate(fn):
        item = copy.deepcopy(raw)
        fn(item)
        mutations.append(item)
    mutate(lambda x: x["rows"][2]["methods"]["action_bound"].update(alarm=False))
    mutate(lambda x: x["rows"][3]["input_receipt"].update(intent_id="foreign"))
    mutate(lambda x: x["rows"][8]["methods"]["action_bound"].update(fallback="NONE"))
    mutate(lambda x: x["rows"][4]["methods"]["action_bound"].update(critical_delta_indices=[]))
    mutate(lambda x: x["rows"].pop())
    rejected = sum(bool(audit(item, inputs, oracle, freeze)[0]) for item in mutations)
    return {"status": "PASS" if rejected == len(mutations) else "FAIL",
            "base_errors": [], "mutations_rejected": rejected,
            "mutations_total": len(mutations)}


def main(argv):
    if len(argv) > 1 and argv[1] == "--self-test":
        path = Path(argv[2]) if len(argv) > 2 else HERE / "formal_01" / "candidate_output" / "raw.json"
        report = self_test(path)
        print(json.dumps(report, sort_keys=True))
        return 0 if report["status"] == "PASS" else 1
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    inputs = json.loads((HERE / "fixture" / "inputs.json").read_text(encoding="utf-8"))
    oracle = json.loads((HERE / "fixture" / "oracle.json").read_text(encoding="utf-8"))
    raw_path = Path(os.environ.get("RAW_PATH", "/audit-input/raw.json"))
    out_path = Path(os.environ.get("AUDIT_OUT", "/audit-output/audit.json"))
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    errors, metrics = audit(raw, inputs, oracle, freeze)
    result = {"schema": "action-bound-residual-audit-v1", "allocation_id": ALLOC,
              "status": "METHOD_PASS_SCOPED" if not errors else "STOP_AUDIT",
              "errors": errors, "metrics": metrics,
              "scope": "synthetic raster method T0 only; no live detector, GUI, game, input, or task claim"}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
