import hashlib
import json
import pathlib
import subprocess
import tempfile
import time


ROOT = pathlib.Path(__file__).resolve().parent
INPUT = ROOT / "input"
OUT = ROOT / "candidate-out"
BOXES = [(37, 161, 87, 14), (127, 161, 88, 14), (217, 161, 88, 14)]
MODES = [6, 7, 8, 10, 13]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_digit_output(result):
    value = result.stdout.strip()
    if result.returncode == 0 and value.isascii() and value.isdigit():
        return value
    return None


def main():
    OUT.mkdir()
    inputs = json.loads((INPUT / "INPUTS.json").read_text())
    rows = []
    for frame in inputs:
        image = INPUT / frame["path"]
        if sha256(image) != frame["sha256"]:
            raise SystemExit("input hash mismatch: " + frame["id"])
        cells = []
        for index, (x, y, width, height) in enumerate(BOXES):
            calls = []
            for psm in MODES:
                with tempfile.TemporaryDirectory(prefix="gray-psm-") as temporary:
                    crop = pathlib.Path(temporary) / "crop.png"
                    magick_argv = [
                        "magick", str(image), "-colorspace", "Gray", "-crop",
                        f"{width}x{height}+{x}+{y}", "+repage",
                        "-filter", "point", "-resize", f"{width * 4}x{height * 4}!",
                        "-bordercolor", "white", "-border", "20", str(crop),
                    ]
                    prep_start = time.monotonic_ns()
                    prep = subprocess.run(magick_argv, capture_output=True, text=True, timeout=20)
                    prep_end = time.monotonic_ns()
                    if prep.returncode != 0:
                        raise SystemExit("ImageMagick failed: " + prep.stderr)
                    tesseract_argv = [
                        "tesseract", str(crop), "stdout", "--psm", str(psm), "-l", "eng",
                        "-c", "tessedit_char_whitelist=0123456789",
                    ]
                    start = time.monotonic_ns()
                    result = subprocess.run(tesseract_argv, capture_output=True, text=True, timeout=20)
                    end = time.monotonic_ns()
                    calls.append({
                        "psm": psm,
                        "preprocess_argv": magick_argv,
                        "preprocess_start_ns": prep_start,
                        "preprocess_end_ns": prep_end,
                        "preprocess_exit_code": prep.returncode,
                        "crop_sha256": sha256(crop),
                        "argv": tesseract_argv,
                        "start_ns": start,
                        "end_ns": end,
                        "exit_code": result.returncode,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "value": parse_digit_output(result),
                    })
            values = [call["value"] for call in calls]
            consensus = values[0] if values[0] is not None and all(value == values[0] for value in values) else None
            cells.append({"index": index, "calls": calls, "mode_values": values, "consensus": consensus})
        rows.append({"id": frame["id"], "source_sha256": frame["sha256"], "cells": cells})
    record = {
        "candidate": "gray_nearest4x_white20_unanimous_psm_6_7_8_10_13_v1",
        "platform": subprocess.run(["sw_vers"], capture_output=True, text=True, check=True).stdout.strip(),
        "tesseract_version": subprocess.run(["tesseract", "--version"], capture_output=True, text=True, check=True).stdout.splitlines()[0],
        "imagemagick_version": subprocess.run(["magick", "-version"], capture_output=True, text=True, check=True).stdout.splitlines()[0],
        "rows": rows,
    }
    with (OUT / "RAW.json").open("x") as stream:
        json.dump(record, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"frames": len(rows), "cells": sum(len(row["cells"]) for row in rows), "ocr_calls": sum(len(cell["calls"]) for row in rows for cell in row["cells"])}))


if __name__ == "__main__":
    main()
