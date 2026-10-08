#!/usr/bin/env python3
"""Write a one-shot freeze after all source and input checks are complete."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def hashes(paths):
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(paths)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--main-sha", required=True)
    ap.add_argument("--branch", required=True)
    ap.add_argument("--vm", required=True)
    ap.add_argument("--engine-id", required=True)
    ap.add_argument("--image-digest", required=True)
    ap.add_argument("--window-start-utc", required=True)
    ap.add_argument("--deadline-utc", required=True)
    a = ap.parse_args()
    public = json.loads((ROOT / "candidate_input.json").read_text())
    truth = json.loads((ROOT / "truth.json").read_text())
    bundle = ROOT / "formal" / "candidate_input"
    if not bundle.is_dir() or len(public["rows"]) != 36 or len(truth["rows"]) != 36:
        raise SystemExit("candidate bundle/fixture gate failed")
    candidate_files = [p for p in (ROOT / "formal" / "candidate_input").rglob("*")
                       if p.is_file()]
    package_sources = [p for p in ROOT.glob("*.py")]
    if len(candidate_files) != 74:
        raise SystemExit(f"candidate bundle must contain 72 frames and two files: {len(candidate_files)}")
    candidate_input = json.loads((bundle / "candidate_input.json").read_text())
    if any(any(label in row[key].lower() for label in
               ("approach", "native", "contrast", "threshold", "control", "unknown"))
           for row in candidate_input["rows"] for key in ("frame0", "frame1")):
        raise SystemExit("semantic/variant label leaked into candidate frame path")
    all_inputs = [ROOT / "truth.json", ROOT / "candidate_input.json"]
    all_inputs.extend(ROOT / row[k] for row in truth["rows"] for k in ("frame0", "frame1"))
    output = {
        "schema": "looming-contrast-freeze-v1",
        "allocation": "LOOMING-VISUAL-ASSUMPTION-GATE-5905-S04-ORBSTACK-CONTRAST-20261003-01",
        "issue": 6808,
        "predecessor": 5905,
        "allocation_authority": "user explicitly directed this task to execute the Issue experiment in a local Docker/OrbStack container; S04 is bounded to the private VM and the UTC window below",
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "window_start_utc": a.window_start_utc,
        "deadline_utc": a.deadline_utc,
        "main_sha": a.main_sha,
        "branch": a.branch,
        "vm": a.vm,
        "private_docker_engine_id": a.engine_id,
        "image": "python@sha256:" + a.image_digest.removeprefix("sha256:"),
        "architecture": "linux/arm64",
        "resource_limits": {"vm_cpus": 2, "vm_memory_bytes": 2147483648,
                            "candidate_auditor_cpus": 1,
                            "candidate_auditor_memory_bytes": 536870912,
                            "network": "none", "gpu": False},
        "fixture": {"rows": 36, "positive": 9, "visible_controls": 21,
                    "pixel_identical_unknown_rows": 6,
                    "photometric_variants": ["native", "low_contrast", "near_threshold"],
                    "candidate_truth_blind": True},
        "candidate_container_command": (
            "docker run --rm --pull=never --network=none --cpus=1 --memory=512m "
            "--mount type=bind,source=/home/taka/6808-s04/candidate_input,target=/study,readonly "
            "--mount type=bind,source=/home/taka/6808-s04/candidate_output,target=/out "
            "python@sha256:" + a.image_digest.removeprefix("sha256:") +
            " python /study/candidate.py /study/candidate_input.json /out/candidate.json"),
        "auditor_container_command": (
            "docker run --rm --pull=never --network=none --cpus=1 --memory=512m "
            "--mount type=bind,source=/home/taka/6808-s04/audit_input,target=/audit,readonly "
            "--mount type=bind,source=/home/taka/6808-s04/auditor_output,target=/out "
            "python@sha256:" + a.image_digest.removeprefix("sha256:") +
            " python /audit/audit.py /audit /out/audit.json"),
        "source_sha256": hashes(package_sources),
        "protocol_sha256": hashes([ROOT / "PREREG.md", ROOT / "CONSTRUCTION.md"]),
        "formal_input_sha256": hashes(all_inputs),
        "candidate_bundle_sha256": {
            str(p.relative_to(bundle)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(candidate_files)},
        "decision_gate": "9/9 approach variants TTC absolute error <=0.06s and cue at <=0.30s; 21 visible control variants no cue; each of 12 families has identical decision/geometry/TTC under both binary-mask-preserving transforms; paired latent-cause rows are identical UNKNOWN within each variant; 36/36 independent reconstruction; 5/5 corruption rejection; false SAFE=0",
        "retry_budget": 0,
        "scope": "finite synthetic image-geometry construction only; no game/GUI/model/input/live-safety/product claim",
    }
    (ROOT / "FREEZE.json").write_text(json.dumps(output, indent=2) + "\n")


if __name__ == "__main__":
    main()
