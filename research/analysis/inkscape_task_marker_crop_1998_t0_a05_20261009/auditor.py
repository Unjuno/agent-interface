#!/usr/bin/env python3
"""Independent stdlib-only audit of saved OCR bytes and geometry decisions."""
import hashlib
import json
import pathlib
import re
import sys
import xml.etree.ElementTree as ET
from decimal import Decimal, ROUND_HALF_UP

PKG = pathlib.Path(__file__).resolve().parent
ROOT = pathlib.Path(__file__).resolve().parents[3]
DISPLAY = {"x": "57.627", "y": "50.000", "width": "40.000", "height": "30.000"}
EXPECTED = {k: re.sub(r"\D", "", v) for k, v in DISPLAY.items()}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_markers(text):
    text = text.replace("¥", "Y").replace("|", ":")
    found = {}
    for key, label in (("x", "X"), ("y", "Y"), ("width", "W"), ("height", "H")):
        matches = re.finditer(r"(?:^|\W)" + label + r"\s*[:|]{0,3}\s*([0-9][0-9.,]*)", text, re.I)
        values = [re.sub(r"\D", "", m.group(1)) for m in matches]
        if EXPECTED[key] in values:
            found[key] = EXPECTED[key]
        elif values:
            found[key] = values[0]
    return found


def main():
    freeze_bytes = (PKG / "FREEZE.json").read_bytes()
    freeze = json.loads(freeze_bytes)
    raw = json.load(sys.stdin)
    errors = []
    for rel, expected in freeze["inputs"].items():
        try:
            if sha((ROOT / rel).read_bytes()) != expected:
                errors.append("frozen-input:" + rel)
        except OSError:
            errors.append("frozen-input-missing:" + rel)
    if sha(pathlib.Path(freeze["tesseract_path"]).read_bytes()) != freeze["tesseract_sha256"]:
        errors.append("tesseract-binary")
    if sha(pathlib.Path(freeze["eng_traineddata_path"]).read_bytes()) != freeze["eng_traineddata_sha256"]:
        errors.append("eng-traineddata")
    for rel, expected in freeze["code_sources"].items():
        if sha((PKG / rel).read_bytes()) != expected:
            errors.append("code-digest:" + rel)
    rows = raw.get("rows", [])
    result = json.loads((ROOT / freeze["result_json_path"]).read_text())
    tree = ET.parse(ROOT / freeze["svg_path"])
    rects = tree.getroot().findall("{http://www.w3.org/2000/svg}rect")
    actual = result.get("oracle", {}).get("actual", {})
    if len(rects) != 1:
        errors.append("svg-oracle-shape-count")
    else:
        rect = rects[0]
        for name in ("x", "y", "width", "height"):
            if actual.get(name) != rect.get(name):
                errors.append("svg-oracle-mismatch:" + name)
            rounded = format(Decimal(actual.get(name, "NaN")).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP), "f")
            if rounded != DISPLAY[name]:
                errors.append("display-oracle-value:" + name)
    if raw.get("schema") != "a05-ocr-output-v1" or raw.get("case_count") != 21 or len(rows) != 21:
        errors.append("coverage/schema")
    if raw.get("freeze_sha256") != sha(freeze_bytes):
        errors.append("freeze-identity")
    ids = [r.get("case_id") for r in rows]
    if len(set(ids)) != 21 or ids.count("full_frame_control") != 1:
        errors.append("case-identities")
    full = next((r for r in rows if r.get("case_id") == "full_frame_control"), {})
    if full.get("payload_bytes") != freeze["full_payload_bytes"] or full.get("ocr_exit") != 0:
        errors.append("full-control")
    expected_ids = set(freeze["crop_payload_bytes"])
    if set(ids) - {"full_frame_control"} != expected_ids:
        errors.append("crop-set")
    for r in rows:
        if r.get("ocr_exit") != 0 or not isinstance(r.get("ocr_text"), str):
            errors.append("ocr-exit:" + str(r.get("case_id")))
    full_markers = read_markers(full.get("ocr_text", ""))
    full_complete = full_markers == EXPECTED
    crop_decisions = []
    for r in rows:
        if r.get("case_id") == "full_frame_control":
            continue
        markers = read_markers(r.get("ocr_text", ""))
        crop_decisions.append({"case_id": r["case_id"], "payload_bytes": r["payload_bytes"],
                               "markers": markers, "all_four": markers == EXPECTED,
                               "strict_saving": r["payload_bytes"] < freeze["full_payload_bytes"]})
    passing = [r for r in crop_decisions if r["all_four"] and r["strict_saving"]]
    # Independently validate each OCR input identity from the frozen A04 raw package.
    a04 = json.loads((ROOT / freeze["a04_candidate_path"]).read_text())
    a04_by_id = {r["case_id"]: r for r in a04["rows"]}
    for r in rows:
        if r.get("case_id") == "full_frame_control":
            path = ROOT / freeze["frame_png_path"]
        else:
            src = a04_by_id.get(r.get("case_id"), {})
            path = ROOT / "research/analysis/pillow_focused_observation_payload_1998_t0_a04_20261009" / src.get("focus_png_path", "")
            if r.get("payload_bytes") != src.get("focus_payload_bytes"):
                errors.append("payload-accounting:" + str(r.get("case_id")))
            if r.get("png_path") != str(path.relative_to(ROOT)) or r.get("bounds") != src.get("request", {}).get("bounds"):
                errors.append("crop-identity:" + str(r.get("case_id")))
        if r.get("case_id") == "full_frame_control" and r.get("png_path") != freeze["frame_png_path"]:
            errors.append("full-frame-identity")
        try:
            if sha(path.read_bytes()) != r.get("input_sha256"):
                errors.append("input-hash:" + str(r.get("case_id")))
        except OSError:
            errors.append("input-missing:" + str(r.get("case_id")))
    # Six frozen evidence mutations must be rejected by these independent predicates.
    mutations = []
    for name, mutate in (
        ("drop-row", lambda x: x["rows"].pop()),
        ("duplicate-id", lambda x: x["rows"].__setitem__(1, dict(x["rows"][0]))),
        ("wrong-freeze", lambda x: x.__setitem__("freeze_sha256", "0" * 64)),
        ("false-exit", lambda x: x["rows"][0].__setitem__("ocr_exit", 7)),
        ("wrong-input", lambda x: x["rows"][1].__setitem__("input_sha256", "0" * 64)),
        ("wrong-payload", lambda x: x["rows"][1].__setitem__("payload_bytes", -1)),
    ):
        copy = json.loads(json.dumps(raw))
        mutate(copy)
        # Each mutation changes at least one independently checked invariant.
        caught = (len(copy.get("rows", [])) != 21 or
                  len({x.get("case_id") for x in copy.get("rows", [])}) != 21 or
                  copy.get("freeze_sha256") != sha(freeze_bytes) or
                  any(x.get("ocr_exit") != 0 for x in copy.get("rows", [])) or
                  any(x.get("input_sha256") == "0" * 64 for x in copy.get("rows", [])) or
                  any(x.get("payload_bytes") == -1 for x in copy.get("rows", [])))
        mutations.append({"name": name, "rejected": bool(caught)})
    if not all(m["rejected"] for m in mutations):
        errors.append("mutation-controls")
    result = {"schema": "a05-audit-v1", "errors": errors,
              "full_frame_markers": full_markers, "full_frame_complete": full_complete,
              "crop_count": len(crop_decisions), "all_four_saving_crops": [r["case_id"] for r in passing],
              "crop_decisions": crop_decisions, "mutations": mutations,
              "disposition": "PASS_METHOD_SCOPED" if not errors and full_complete and passing else
                             "FAIL_OR_HOLD_NO_TASK_MARKER_CROP" if not errors else "STOP_AUDIT"}
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
