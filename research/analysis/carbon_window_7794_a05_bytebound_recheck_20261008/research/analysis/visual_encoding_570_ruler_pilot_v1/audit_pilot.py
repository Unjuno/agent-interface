"""Independent raw-only auditor for the Issue #570 ruler pilot."""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageChops


ROOT = Path(__file__).resolve().parent
FORMAL = ROOT / "results" / "formal01"
WIDTH, HEIGHT = 1280, 800
MODEL_DIGEST = "fb90415cde1ef08aa669ae74b082d49b158729b6db1ab183c941417d507e71a1"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    errors: list[str] = []
    p = FORMAL / "FORMAL_RESULT.json"
    if not p.is_file():
        print(json.dumps({"status": "HOLD_RAW_RESULT_MISSING", "errors": ["FORMAL_RESULT.json missing"]}))
        return 2
    data = p.read_bytes()
    result = json.loads(data)
    rows = result.get("rows", [])
    if result.get("schema") != "visual-ruler-570-localvlm-raw-v1":
        errors.append("result schema mismatch")
    if result.get("model_digest") != MODEL_DIGEST:
        errors.append("model digest mismatch")
    if result.get("formal_optimizer_steps") != 0:
        errors.append("unexpected optimizer steps")
    if result.get("run_exit") != 0:
        errors.append("runner exit not zero")
    if len(rows) != 12:
        errors.append(f"row count {len(rows)} != 12")

    metrics = {arm: {"positive_hits": 0, "positive_count": 0, "absent_false_select": 0, "absent_count": 0, "errors": []} for arm in ("RAW", "BORDER_RULER")}
    paired_distances: dict[str, list[float]] = {"RAW": [], "BORDER_RULER": []}
    complete_pairs = 0
    for index, row in enumerate(rows):
        if row.get("index") != index:
            errors.append(f"row {index}: index mismatch")
        prompt = row.get("prompt")
        if not isinstance(prompt, str) or not prompt:
            errors.append(f"row {index}: missing prompt")
        if set(row.get("calls", {})) != {"RAW", "BORDER_RULER"}:
            errors.append(f"row {index}: missing/extra arm calls")
            continue
        raw_path = FORMAL / "cases" / f"{index:02d}_raw.png"
        ruler_path = FORMAL / "cases" / f"{index:02d}_ruler.png"
        if not raw_path.is_file() or not ruler_path.is_file():
            errors.append(f"row {index}: image missing")
            continue
        raw_bytes, ruler_bytes = raw_path.read_bytes(), ruler_path.read_bytes()
        if digest(raw_bytes) != row.get("source_image_sha256") or digest(raw_bytes) != row.get("arm_image_sha256", {}).get("RAW"):
            errors.append(f"row {index}: raw image hash mismatch")
        if digest(ruler_bytes) != row.get("arm_image_sha256", {}).get("BORDER_RULER"):
            errors.append(f"row {index}: ruler image hash mismatch")
        raw, ruler = Image.open(raw_path).convert("RGB"), Image.open(ruler_path).convert("RGB")
        if raw.size != (WIDTH, HEIGHT) or ruler.size != (WIDTH, HEIGHT):
            errors.append(f"row {index}: image dimensions mismatch")
        diff = ImageChops.difference(raw, ruler)
        diff_pixels = diff.load()
        for y in range(64, HEIGHT):
            for x in range(72, WIDTH):
                if diff_pixels[x, y] != (0, 0, 0):
                    errors.append(f"row {index}: ruler changed source UI pixel at {(x, y)}")
                    break
            else:
                continue
            break
        truth = row.get("truth")
        is_absent = truth is None
        pair_valid = True
        for arm in ("RAW", "BORDER_RULER"):
            call = row["calls"].get(arm, {})
            if call.get("status") != "ok":
                errors.append(f"row {index}/{arm}: call not successful")
                pair_valid = False
                continue
            if call.get("request_image_sha256") != row.get("arm_image_sha256", {}).get(arm):
                errors.append(f"row {index}/{arm}: request-image binding mismatch")
            parsed = call.get("parsed")
            if not isinstance(parsed, dict) or not isinstance(parsed.get("abstain"), bool):
                errors.append(f"row {index}/{arm}: response schema invalid")
                pair_valid = False
                continue
            x, y, abstain = parsed.get("x_norm"), parsed.get("y_norm"), parsed.get("abstain")
            valid_xy = isinstance(x, (int, float)) and isinstance(y, (int, float)) and 0 <= x <= 1 and 0 <= y <= 1
            if not abstain and not valid_xy:
                errors.append(f"row {index}/{arm}: non-abstain lacks in-range coordinates")
                pair_valid = False
                continue
            if abstain and (x is not None or y is not None):
                errors.append(f"row {index}/{arm}: abstain has coordinates")
                pair_valid = False
                continue
            if is_absent:
                metrics[arm]["absent_count"] += 1
                if not abstain:
                    metrics[arm]["absent_false_select"] += 1
            else:
                metrics[arm]["positive_count"] += 1
                if not abstain:
                    px, py = x * WIDTH, y * HEIGHT
                    box = truth["box"]
                    hit = box[0] <= px <= box[2] and box[1] <= py <= box[3]
                    metrics[arm]["positive_hits"] += int(hit)
                    cx, cy = truth["center"]
                    distance = math.hypot(px - cx, py - cy) / math.hypot(WIDTH, HEIGHT)
                    metrics[arm]["errors"].append(distance)
                    paired_distances[arm].append(distance)
                else:
                    metrics[arm]["errors"].append(1.0)
                    paired_distances[arm].append(1.0)
        complete_pairs += int(pair_valid)

    if complete_pairs != 12:
        errors.append(f"complete paired rows {complete_pairs} != 12")
    if sum(m["positive_count"] for m in metrics.values()) != 20:
        errors.append("positive case denominator mismatch")
    if sum(m["absent_count"] for m in metrics.values()) != 4:
        errors.append("absent case denominator mismatch")
    summary = {}
    for arm, m in metrics.items():
        vals = m["errors"]
        summary[arm] = {
            "positive_hits": m["positive_hits"],
            "positive_count": m["positive_count"],
            "absent_false_select": m["absent_false_select"],
            "absent_count": m["absent_count"],
            "mean_normalized_center_error": sum(vals) / len(vals) if vals else None,
        }
    raw_mean = summary["RAW"]["mean_normalized_center_error"]
    ruler_mean = summary["BORDER_RULER"]["mean_normalized_center_error"]
    improvement = None if raw_mean is None or ruler_mean is None else raw_mean - ruler_mean
    if errors:
        disposition = "HOLD_AUDIT_ERROR"
    elif complete_pairs < 8:
        disposition = "HOLD_INSUFFICIENT_PAIRED_RESPONSES"
    elif summary["BORDER_RULER"]["positive_hits"] < summary["RAW"]["positive_hits"] or summary["BORDER_RULER"]["absent_false_select"] > summary["RAW"]["absent_false_select"]:
        disposition = "REJECT_RULER_CORRECTNESS_REGRESSION"
    elif improvement is not None and improvement >= 0.02:
        disposition = "RETAIN_RULER_SCOPED"
    else:
        disposition = "REJECT_NO_MATERIAL_LOCALIZATION_GAIN"
    audit = {
        "schema": "visual-ruler-570-independent-audit-v1",
        "formal_result_sha256": digest(data),
        "complete_pairs": complete_pairs,
        "metrics": summary,
        "paired_mean_error_improvement_raw_minus_ruler": improvement,
        "disposition": disposition,
        "errors": errors,
    }
    audit_bytes = (json.dumps(audit, sort_keys=True, indent=2) + "\n").encode("utf-8")
    (FORMAL / "AUDIT.json").write_bytes(audit_bytes)
    print(json.dumps(audit, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
