"""One-shot PSM diagnostic over the retained, known G12 crop; no app/input."""
from __future__ import annotations

import hashlib
import json
import pathlib
import platform
import shutil
import subprocess
import time
from datetime import datetime, timezone


ROOT = pathlib.Path(__file__).resolve().parent
INPUT = ROOT / "input-c2.png"
OUTPUT = ROOT / "RAW.json"
EXPECTED_INPUT_SHA256 = "851ad8686d681fe55aaa6ac8c609e67f47812334d8ded79658434e94ff8445f8"
MODES = (6, 7, 8, 10, 13)


def main() -> int:
    if OUTPUT.exists():
        raise SystemExit("refusing to replace existing RAW.json")
    binary = shutil.which("tesseract")
    if binary is None:
        raise SystemExit("tesseract is not installed; no OCR call made")
    image = INPUT.read_bytes()
    digest = hashlib.sha256(image).hexdigest()
    if digest != EXPECTED_INPUT_SHA256:
        raise SystemExit(f"input SHA256 mismatch: {digest}; no OCR call made")

    version = subprocess.run([binary, "--version"], capture_output=True, text=True, check=True)
    rows = []
    for psm in MODES:
        argv = [binary, "input-c2.png", "stdout", "--psm", str(psm), "-l", "eng",
                "-c", "tessedit_char_whitelist=0123456789"]
        started = time.monotonic_ns()
        result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=10)
        ended = time.monotonic_ns()
        rows.append({
            "psm": psm,
            "argv": argv,
            "started_monotonic_ns": started,
            "ended_monotonic_ns": ended,
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        })

    matches = [row["psm"] for row in rows if row["exit_code"] == 0 and row["stdout"].strip() == "551"]
    disposition = "DIAGNOSTIC_FOUND_PSM_CANDIDATE" if matches else "DIAGNOSTIC_NO_PSM_MATCH"
    raw = {
        "schema": "known-crop-psm-diagnostic-v1",
        "disposition": disposition,
        "scope": "post-run known-image diagnostic; not held-out validation or G12 regrade",
        "recorded_utc": datetime.now(timezone.utc).isoformat(),
        "host": {"system": platform.platform(), "architecture": platform.machine()},
        "binary": {"path": binary, "version_stdout": version.stdout, "version_stderr": version.stderr},
        "input": {"path": INPUT.name, "bytes": len(image), "sha256": digest, "expected_for_scoring_only": "551"},
        "fixed_options": {"language": "eng", "character_whitelist": "0123456789"},
        "modes": list(MODES),
        "candidate_modes": matches,
        "attempts": rows,
    }
    OUTPUT.write_text(json.dumps(raw, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"disposition": disposition, "candidate_modes": matches,
                      "calls": len(rows), "input_sha256": digest}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
