#!/usr/bin/env python3
"""One-shot Tesseract pass over the frozen full frame and 20 A04 crops."""
import hashlib
import json
import pathlib
import platform
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
PKG = pathlib.Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    freeze = json.loads((PKG / "FREEZE.json").read_text())
    if (pathlib.Path(sys.executable).resolve().as_posix() != freeze["python_executable"] or
            sys.version != freeze["python_version"] or platform.platform() != freeze["platform"] or
            platform.machine() != freeze["machine"] or platform.release() != freeze["kernel_release"]):
        raise SystemExit("frozen Python/host identity mismatch")
    for rel, expected in freeze["inputs"].items():
        if sha((ROOT / rel).read_bytes()) != expected:
            raise SystemExit("frozen input digest mismatch: " + rel)
    for rel, expected in freeze["code_sources"].items():
        if sha((PKG / rel).read_bytes()) != expected:
            raise SystemExit("frozen code digest mismatch: " + rel)
    version = subprocess.run([freeze["tesseract_path"], "--version"],
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    if version.returncode != 0 or version.stdout.decode("utf-8", "replace").splitlines()[0] != freeze["tesseract_version"]:
        raise SystemExit("frozen Tesseract version mismatch")
    if sha(pathlib.Path(tesseract).read_bytes()) != freeze["tesseract_sha256"]:
        raise SystemExit("frozen Tesseract executable digest mismatch")
    if sha(pathlib.Path(freeze["eng_traineddata_path"]).read_bytes()) != freeze["eng_traineddata_sha256"]:
        raise SystemExit("frozen English traineddata digest mismatch")
    tesseract = freeze["tesseract_path"]
    tessdata = freeze["tessdata_dir"]
    design = json.loads((ROOT / freeze["a04_design_path"]).read_text())
    a04 = json.loads((ROOT / freeze["a04_candidate_path"]).read_text())
    frame_id = freeze["frame_id"]
    frame = next(f for f in design["frames"] if f["frame_id"] == frame_id)
    source_path = ROOT / frame["source_png_path"]
    source_bytes = source_path.read_bytes()
    rows = [r for r in a04["rows"] if r["frame_id"] == frame_id and r["selected_kind"] == "FOCUSED_REGION"]
    if len(rows) != 20:
        raise SystemExit(f"expected 20 smaller crops, got {len(rows)}")
    full_payload = next(r for r in a04["rows"] if r["frame_id"] == frame_id and r["selected_kind"] == "FULL_FRAME")
    cases = [{"case_id": "full_frame_control", "kind": "FULL_FRAME",
              "png_path": frame["source_png_path"], "payload_bytes": full_payload["full_payload_bytes"],
              "input_bytes": source_bytes}]
    for row in rows:
        # A04 artifact path is relative to its own package, not repository root.
        path = ROOT / "research/analysis/pillow_focused_observation_payload_1998_t0_a04_20261009" / row["focus_png_path"]
        cases.append({"case_id": row["case_id"], "kind": "FOCUSED_REGION",
                      "bounds": row["request"]["bounds"], "payload_bytes": row["focus_payload_bytes"],
                      "png_path": str(path.relative_to(ROOT)), "input_bytes": path.read_bytes()})
    result = []
    for case in cases:
        proc = subprocess.run([tesseract, "stdin", "stdout", "--psm", str(freeze["psm"]),
                               "-l", "eng", "--tessdata-dir", tessdata],
                              input=case["input_bytes"], stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, check=False)
        result.append({k: v for k, v in case.items() if k != "input_bytes"} | {
            "input_sha256": sha(case["input_bytes"]), "ocr_exit": proc.returncode,
            "ocr_text": proc.stdout.decode("utf-8", "replace"),
            "ocr_stderr": proc.stderr.decode("utf-8", "replace")})
    out = {"schema": "a05-ocr-output-v1", "freeze_sha256": sha((PKG / "FREEZE.json").read_bytes()),
           "case_count": len(result), "rows": result}
    sys.stdout.write(json.dumps(out, sort_keys=True, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
