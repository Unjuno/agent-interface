"""Deterministic presentation transformer; no model, network, or effects."""
import base64
import json
import sys
from pathlib import Path

import scenes

ARMS = ("FULL", "FULL_PLUS_CONTEXT_CROP", "CROP_ONLY", "FULL_PLUS_SHAM_CROP")
INVALID = {"target_hidden": (24, 4, 116, 36), "safety_hidden": (4, 4, 28, 36)}


def visible(box, region):
    return box[0] <= region[0] and box[1] <= region[1] and box[2] >= region[2] and box[3] >= region[3]


def build():
    rows = []
    for case in scenes.cases():
        source = scenes.render(case)
        context = scenes.crop_ppm(source, scenes.CONTEXT)
        sham = scenes.crop_ppm(source, scenes.SHAM)
        items = {
            "FULL": [("source", source, [0, 0, scenes.WIDTH, scenes.HEIGHT])],
            "FULL_PLUS_CONTEXT_CROP": [
                ("source", source, [0, 0, scenes.WIDTH, scenes.HEIGHT]),
                ("context_crop", context, list(scenes.CONTEXT))],
            "CROP_ONLY": [("context_crop", context, list(scenes.CONTEXT))],
            "FULL_PLUS_SHAM_CROP": [
                ("source", source, [0, 0, scenes.WIDTH, scenes.HEIGHT]),
                ("sham_crop", sham, list(scenes.SHAM))],
        }
        for arm in ARMS:
            records = []
            for name, data, box in items[arm]:
                records.append({"name": name, "source_box": box,
                                "sha256": scenes.sha256(data),
                                "ppm_b64": base64.b64encode(data).decode("ascii")})
            rows.append({"case_id": case["id"], "content": case["content"],
                         "layout": case["layout"], "arm": arm, "items": records})
    invalid_checks = []
    for case in scenes.cases():
        for name, box in INVALID.items():
            target_visible = visible(box, scenes.TARGET)
            safety_visible = visible(box, scenes.SAFETY)
            invalid_checks.append({"case_id": case["id"], "invalid_crop": name,
                                  "crop_box": list(box), "target_visible": target_visible,
                                  "safety_visible": safety_visible,
                                  "decision": "ALLOW" if target_visible and safety_visible else "REJECT"})
    return {"schema": "issue-6575-t0-candidate-v1", "rows": rows,
            "invalid_checks": invalid_checks}


def main(argv):
    if len(argv) != 2:
        raise SystemExit("usage: candidate.py OUTPUT.json")
    Path(argv[1]).write_text(json.dumps(build(), sort_keys=True, separators=(",", ":")) + "\n",
                             encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv)
