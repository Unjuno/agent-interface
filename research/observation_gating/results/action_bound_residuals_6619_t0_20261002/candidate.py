from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


HERE = Path(__file__).resolve().parent
INPUT = HERE / "fixture" / "inputs.json"
OUT = Path(os.environ.get("OUT_DIR", "/out"))
CAPTURE_BUDGET_PER_CASE = 1


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def flat(frame):
    return [value for row in frame for value in row]


def shifted(values, width, height, dx):
    return [values[y * width + (x - dx)] if 0 <= x - dx < width else 0
            for y in range(height) for x in range(width)]


def changed(before, after):
    return [i for i, (a, b) in enumerate(zip(before, after)) if a != b]


def critical_hits(before, after, positions):
    return sorted(i for i in positions if before[i] != 255 and after[i] == 255)


def binding(receipt, case):
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
    request_ns, ack_ns = receipt.get("request_ns"), receipt.get("ack_ns")
    release_ns, capture_ns = receipt.get("release_ns"), case.get("capture_ns")
    if any(type(x) is not int for x in (request_ns, ack_ns, release_ns, capture_ns)):
        return False, "receipt_time_missing"
    if not request_ns <= ack_ns <= capture_ns <= release_ns:
        return False, "receipt_not_current_at_capture"
    support = receipt.get("allowed_dx")
    if (not isinstance(support, list) or not support or
            any(type(dx) is not int or dx < -4 or dx > 4 for dx in support) or
            len(set(support)) != len(support)):
        return False, "transform_support_invalid"
    if receipt.get("action") not in ("pan_right", "no_input"):
        return False, "action_class_unknown"
    if receipt.get("action") == "no_input" and support != [0]:
        return False, "no_input_support_mismatch"
    return True, "bound"


def method_raw(before, after, critical):
    delta = changed(before, after)
    critical_delta = sorted(i for i in critical
                            if before[i] != 255 and after[i] == 255)
    return {"alarm": bool(delta), "residual_indices": delta,
            "predicted_indices": [],
            "critical_delta_indices": critical_delta,
            "fallback": "FULL_FRAME" if delta else "NONE"}


def method_registration(before, after, width, height, critical):
    best = None
    for dx in range(-4, 5):
        prediction = shifted(before, width, height, dx)
        residual = changed(prediction, after)
        key = (len(residual), abs(dx), dx)
        if best is None or key < best[0]:
            best = (key, dx, residual)
    delta = changed(before, after)
    critical_delta = critical_hits(before, after, critical)
    residual = best[2]
    return {"alarm": bool(residual or critical_delta), "selected_dx": best[1],
            "residual_indices": residual,
            "predicted_indices": sorted(set(delta).difference(residual)),
            "critical_delta_indices": critical_delta,
            "fallback": "NONE"}


def method_bound(before, after, width, height, critical, receipt, case):
    delta = changed(before, after)
    critical_delta = critical_hits(before, after, critical)
    valid, reason = binding(receipt, case)
    if not valid:
        return {"alarm": bool(delta), "residual_indices": delta,
                "predicted_indices": [],
                "critical_delta_indices": critical_delta,
                "fallback": "UNKNOWN_FULL_FRAME", "binding": reason,
                "allowed_dx": None}
    predictions = [shifted(before, width, height, dx) for dx in receipt["allowed_dx"]]
    residual = []
    for i in delta:
        values = {prediction[i] for prediction in predictions}
        # Suppress only changes exactly explained by every permitted transform.
        if len(values) != 1 or after[i] not in values:
            residual.append(i)
    alarm = bool(residual or critical_delta)
    return {"alarm": alarm, "residual_indices": residual,
            "predicted_indices": sorted(set(delta).difference(residual)),
            "critical_delta_indices": critical_delta, "fallback": "NONE",
            "binding": "bound", "allowed_dx": receipt["allowed_dx"]}


def analyze_case(case):
    width, height = case["width"], case["height"]
    before, after = flat(case["previous"]), flat(case["current"])
    if len(before) != width * height or len(after) != width * height:
        raise ValueError(f"frame_shape:{case.get('case_id')}")
    critical = [y * width + x for x, y in case["critical_pixels"]]
    return {"case_id": case["case_id"], "intent_id": case["intent_id"],
            "input_receipt": case["receipt"], "sham_receipt": case["sham_receipt"],
            "capture_ns": case["capture_ns"],
            "frame_sha256": hashlib.sha256(bytes(before) + bytes(after)).hexdigest(),
            "raw_delta_indices": changed(before, after),
            "methods": {
                "raw_delta": method_raw(before, after, critical),
                "global_registration": method_registration(before, after, width, height, critical),
                "action_bound": method_bound(before, after, width, height, critical, case["receipt"], case),
                "sham_bound": method_bound(before, after, width, height, critical, case["sham_receipt"], case),
            }}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    input_data = json.loads(INPUT.read_text(encoding="utf-8"))
    if input_data.get("schema") != "action-bound-residual-input-v1":
        raise SystemExit("STOP_FIXTURE_SCHEMA")
    rows = [analyze_case(case) for case in input_data["cases"]]
    freeze_path = HERE / "FREEZE.json"
    image_id = os.environ.get("IMAGE_ID")
    freeze = json.loads(freeze_path.read_text(encoding="utf-8")) if freeze_path.exists() else {}
    freeze_errors = []
    if not freeze_path.exists():
        freeze_errors.append("freeze_missing")
    if image_id != freeze.get("image_id"):
        freeze_errors.append("image_id_mismatch")
    if digest(INPUT) != freeze.get("inputs_sha256"):
        freeze_errors.append("inputs_hash_mismatch")
    if digest(Path(__file__)) != freeze.get("source_sha256", {}).get("candidate.py"):
        freeze_errors.append("candidate_source_hash_mismatch")
    result = {"schema": "action-bound-residual-candidate-v1",
              "allocation_id": "ACTION-BOUND-RESIDUALS-6619-T0-WSLC-20261002-01",
              "candidate_status": "PASS_CANDIDATE_SHAPE",
              "candidate_completed": True, "candidate_errors": [],
              "image_id": image_id,
              "inputs_sha256": digest(INPUT),
              "oracle_sha256": digest(HERE / "fixture" / "oracle.json"),
              "candidate_sha256": digest(Path(__file__)),
              "capture_budget_per_case": CAPTURE_BUDGET_PER_CASE,
              "row_count": len(rows), "rows": rows}
    if freeze_errors:
        result["candidate_status"] = "STOP_FREEZE_OR_IMAGE_MISSING"
        result["candidate_completed"] = False
        result["candidate_errors"] = freeze_errors
    output = OUT / "raw.json"
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["candidate_status"], "rows": len(rows),
                      "output_sha256": digest(output)}, sort_keys=True))
    raise SystemExit(0 if result["candidate_completed"] else 2)


if __name__ == "__main__":
    main()
