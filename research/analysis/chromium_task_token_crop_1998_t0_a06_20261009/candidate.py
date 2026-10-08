#!/usr/bin/env python3
"""One-shot OCR over the 20 frozen smaller A04 crop PNGs only."""
import hashlib, json, pathlib, platform, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
PKG = pathlib.Path(__file__).resolve().parent

def sha(data): return hashlib.sha256(data).hexdigest()

def main():
    freeze = json.loads((PKG / "FREEZE.json").read_text())
    tessdata = freeze["tessdata_dir"]
    tesseract = freeze["tesseract_path"]  # Bind before any identity check.
    if (pathlib.Path(sys.executable).resolve().as_posix() != freeze["python_executable"] or
        sys.version != freeze["python_version"] or platform.platform() != freeze["platform"] or
        platform.machine() != freeze["machine"] or platform.release() != freeze["kernel_release"]):
        raise SystemExit("frozen Python/host identity mismatch")
    for rel, expected in freeze["inputs"].items():
        if sha((ROOT / rel).read_bytes()) != expected: raise SystemExit("frozen input digest mismatch: " + rel)
    for rel, expected in freeze["code_sources"].items():
        if sha((PKG / rel).read_bytes()) != expected: raise SystemExit("frozen code digest mismatch: " + rel)
    version = subprocess.run([tesseract, "--version"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if version.returncode or version.stdout.decode("utf-8", "replace").splitlines()[0] != freeze["tesseract_version"]:
        raise SystemExit("frozen Tesseract version mismatch")
    if sha(pathlib.Path(tesseract).read_bytes()) != freeze["tesseract_sha256"]: raise SystemExit("Tesseract binary digest mismatch")
    if sha(pathlib.Path(freeze["eng_traineddata_path"]).read_bytes()) != freeze["eng_traineddata_sha256"]: raise SystemExit("traineddata digest mismatch")
    a04 = json.loads((ROOT / freeze["a04_candidate_path"]).read_text())
    rows = [r for r in a04["rows"] if r["frame_id"] == freeze["frame_id"] and r["selected_kind"] == "FOCUSED_REGION"]
    if len(rows) != 20: raise SystemExit(f"expected 20 crops, got {len(rows)}")
    output = []
    for row in rows:
        rel = freeze["a04_package"] + "/" + row["focus_png_path"]
        data = (ROOT / rel).read_bytes()
        proc = subprocess.run([tesseract, "stdin", "stdout", "--psm", str(freeze["psm"]), "-l", "eng", "--tessdata-dir", tessdata], input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output.append({"case_id": row["case_id"], "bounds": row["request"]["bounds"], "png_path": rel,
          "payload_bytes": row["focus_payload_bytes"], "full_payload_bytes": row["full_payload_bytes"],
          "input_sha256": sha(data), "ocr_exit": proc.returncode,
          "ocr_text": proc.stdout.decode("utf-8", "replace"), "ocr_stderr": proc.stderr.decode("utf-8", "replace")})
    result = {"schema":"a06-ocr-output-v1", "freeze_sha256":sha((PKG/"FREEZE.json").read_bytes()), "case_count":len(output), "rows":output}
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if all(r["ocr_exit"] == 0 for r in output) else 1

if __name__ == "__main__": raise SystemExit(main())
