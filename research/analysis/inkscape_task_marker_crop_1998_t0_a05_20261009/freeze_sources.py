#!/usr/bin/env python3
"""Create the A05 immutable source/input freeze; run before formal execution."""
import hashlib
import json
import os
import pathlib
import subprocess
import xml.etree.ElementTree as ET
from decimal import Decimal, ROUND_HALF_UP

ROOT = pathlib.Path(__file__).resolve().parents[3]
PKG = pathlib.Path(__file__).resolve().parent
A04 = ROOT / "research/analysis/pillow_focused_observation_payload_1998_t0_a04_20261009"
FRAME_ID = "inkscape-49f759cae634"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    design_path = "research/analysis/pillow_focused_observation_payload_1998_t0_a04_20261009/design.json"
    candidate_path = "research/analysis/pillow_focused_observation_payload_1998_t0_a04_20261009/results/candidate.stdout"
    design = json.loads((ROOT / design_path).read_text())
    a04 = json.loads((ROOT / candidate_path).read_text())
    frame = next(f for f in design["frames"] if f["frame_id"] == FRAME_ID)
    rows = [r for r in a04["rows"] if r["frame_id"] == FRAME_ID]
    crops = [r for r in rows if r["selected_kind"] == "FOCUSED_REGION"]
    full = next(r for r in rows if r["selected_kind"] == "FULL_FRAME")
    if len(crops) != 20:
        raise SystemExit(f"expected 20 fixed crops, found {len(crops)}")
    run = ROOT / "research/observation_gating/results/baseline-screen-02/inkscape-1101-O0"
    result_path = "research/observation_gating/results/baseline-screen-02/inkscape-1101-O0/result.json"
    svg_path = "research/observation_gating/results/baseline-screen-02/inkscape-1101-O0/shape.svg"
    result = json.loads((ROOT / result_path).read_text())
    rect = ET.parse(ROOT / svg_path).getroot().find("{http://www.w3.org/2000/svg}rect")
    exact = {k: result["oracle"]["actual"][k] for k in ("x", "y", "width", "height")}
    if rect is None or any(rect.get(k) != exact[k] for k in exact):
        raise SystemExit("saved SVG does not match the retained task oracle")
    displayed = {k: format(Decimal(v).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP), "f")
                 for k, v in exact.items()}
    tess = pathlib.Path(os.path.realpath("/run/current-system/sw/bin/tesseract"))
    tessdata = tess.parent.parent / "share/tessdata"
    eng = tessdata / "eng.traineddata"
    version_out = subprocess.run([str(tess), "--version"], stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, check=True).stdout.decode().splitlines()[0]
    crop_map = {r["case_id"]: r["focus_payload_bytes"] for r in crops}
    paths = {
        design_path, candidate_path,
        "research/analysis/pillow_focused_observation_payload_1998_t0_a04_20261009/FREEZE.json",
        "research/analysis/pillow_focused_observation_payload_1998_t0_a04_20261009/OUTPUT_SHA256SUMS.txt",
        "research/analysis/pillow_focused_observation_payload_1998_t0_a04_20261009/results/audit.stdout",
        "research/analysis/pillow_focused_observation_payload_1998_t0_a04_20261009/REPORT.md",
        frame["source_png_path"], frame["ledger_path"], result_path, svg_path,
        "research/observation_gating/gui_suite.py",
    }
    paths.update("research/analysis/pillow_focused_observation_payload_1998_t0_a04_20261009/" + r["focus_png_path"]
                 for r in crops)
    inputs = {p: sha((ROOT / p).read_bytes()) for p in sorted(paths)}
    code_paths = ("candidate.py", "auditor.py", "formal_runner.py", "freeze_sources.py")
    code_sources = {p: sha((PKG / p).read_bytes()) for p in code_paths}
    base_main = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "origin/main"],
                               stdout=subprocess.PIPE, check=True).stdout.decode().strip()
    data = {
        "schema": "a05-freeze-v1",
        "allocation": "LABEL-CONTROL-AMBIGUITY-1998-T0-A05-20261009",
        "base_main_commit": base_main,
        "depends_on_a04_head": "5d4dbe50bb63a3df19f06b97701bde43217d24af",
        "frame_id": FRAME_ID,
        "a04_design_path": design_path,
        "a04_candidate_path": candidate_path,
        "a04_audit_path": "research/analysis/pillow_focused_observation_payload_1998_t0_a04_20261009/results/audit.stdout",
        "frame_png_path": frame["source_png_path"],
        "result_json_path": result_path,
        "svg_path": svg_path,
        "source_pixel_sha256": frame["source_pixel_sha256"],
        "full_payload_bytes": full["full_payload_bytes"],
        "crop_payload_bytes": crop_map,
        "oracle_exact": exact,
        "display_values_3dp": displayed,
        "ocr_normalized_digits": {k: "".join(c for c in v if c.isdigit()) for k, v in displayed.items()},
        "tesseract_path": str(tess),
        "tesseract_sha256": sha(tess.read_bytes()),
        "tesseract_version": version_out,
        "tessdata_dir": str(tessdata),
        "eng_traineddata_path": str(eng),
        "eng_traineddata_sha256": sha(eng.read_bytes()),
        "psm": 11,
        "candidate_invocations": 1,
        "auditor_invocations": 1,
        "retries": 0,
        "inputs": inputs,
        "code_sources": code_sources,
        "scope": "one retained Inkscape screen, Tesseract OCR extractability only",
    }
    out = (json.dumps(data, sort_keys=True, indent=2) + "\n").encode()
    (PKG / "FREEZE.json").write_bytes(out)
    (PKG / "FREEZE.sha256").write_text(sha(out) + "  FREEZE.json\n")
    print(json.dumps({"freeze_sha256": sha(out), "input_count": len(inputs),
                      "crop_count": len(crops), "code_count": len(code_sources),
                      "base_main_commit": base_main}, sort_keys=True))


if __name__ == "__main__":
    main()
