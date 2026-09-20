#!/usr/bin/env python3
"""Reproduce coordinated raw/freeze/study-manifest substitution for Issue #3691."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INPUTS = ROOT / "inputs"
EXPECTED = {
    "audit.py": "0956b13a9e98c504c870096507b9428acae0510a27903d0eccb0f730af35c579",
    "test_integrity.py": "15dbc3167b3d39dc622944bdf770c2c3d12036d23d9079c8cb80fbb628a98105",
    "raw.json": "ccb9a75eefb7df73cb13dbc9191d33334fb672c2fd58fcc5fa32be998e182807",
    "predecessor_FREEZE.json": "f40494b1be99fb1e68d7b09c498297df35a72c043740b5f09d3faec7e059acfe",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def manifest(work: Path, raw_bytes: bytes, freeze_bytes: bytes) -> dict:
    return {
        "predecessor_raw_sha256": sha256(raw_bytes),
        "predecessor_freeze_sha256": sha256(freeze_bytes),
        "source_sha256": {
            name: sha256((work / name).read_bytes())
            for name in ("audit.py", "test_integrity.py")
        },
    }


def invoke(work: Path, label: str) -> dict:
    output_path = work / f"{label}-audit.json"
    completed = subprocess.run(
        [
            sys.executable, str(work / "audit.py"), str(work / "raw.json"),
            "--freeze", str(work / "freeze.json"),
            "--study-freeze", str(work / "study.json"),
            "--output", str(output_path),
        ],
        capture_output=True, text=True, check=False,
    )
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError:
        result = {"unparsed_stdout": completed.stdout}
    return {"exit_code": completed.returncode, "result": result, "stderr": completed.stderr}


def main() -> int:
    expected_paths = {
        "audit.py": INPUTS / "audit.py",
        "test_integrity.py": INPUTS / "test_integrity.py",
        "raw.json": INPUTS / "raw.json",
        "predecessor_FREEZE.json": INPUTS / "predecessor_FREEZE.json",
    }
    hashes = {name: sha256(path.read_bytes()) for name, path in expected_paths.items()}
    if hashes != EXPECTED:
        raise SystemExit(f"frozen input hash mismatch: {hashes}")

    with tempfile.TemporaryDirectory(prefix="issue3691-manifest-root-") as temp:
        base = Path(temp)
        for name, source in expected_paths.items():
            target = "freeze.json" if name == "predecessor_FREEZE.json" else name
            shutil.copyfile(source, base / target)
        raw_bytes = (base / "raw.json").read_bytes()
        freeze_bytes = (base / "freeze.json").read_bytes()
        (base / "study.json").write_text(json.dumps(manifest(base, raw_bytes, freeze_bytes)))
        canonical = invoke(base, "canonical")

        raw = json.loads(raw_bytes)
        raw["events"][0]["identity"]["pixel_sha256"] = "1" * 64
        raw["events"][1]["identity"]["pixel_sha256"] = "1" * 64
        replacement_freeze = freeze_bytes + b" "
        raw["freeze_sha256"] = sha256(replacement_freeze)
        replacement_raw = json.dumps(raw, sort_keys=True).encode("utf-8")
        (base / "raw.json").write_bytes(replacement_raw)
        (base / "freeze.json").write_bytes(replacement_freeze)
        replacement_manifest = manifest(base, replacement_raw, replacement_freeze)
        (base / "study.json").write_text(json.dumps(replacement_manifest, sort_keys=True))
        replacement = invoke(base, "replacement")
        output = {
            "decision": "PASS_REPRODUCTION_MANIFEST_TRUST_ROOT_GAP",
            "canonical": canonical,
            "coordinated_replacement": replacement,
            "frozen_input_sha256": hashes,
            "replacement_sha256": {
                "raw": sha256(replacement_raw),
                "freeze": sha256(replacement_freeze),
                "study_manifest": sha256((base / "study.json").read_bytes()),
            },
        }
        print(json.dumps(output, indent=2, sort_keys=True))
        if canonical["exit_code"] != 0 or replacement["exit_code"] != 0:
            return 1
        if canonical["result"].get("status") != "PASS_OFFLINE_STRUCTURAL_AUDIT":
            return 1
        if replacement["result"].get("status") != "PASS_OFFLINE_STRUCTURAL_AUDIT":
            return 1
        if canonical["result"].get("errors") != [] or replacement["result"].get("errors") != []:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())