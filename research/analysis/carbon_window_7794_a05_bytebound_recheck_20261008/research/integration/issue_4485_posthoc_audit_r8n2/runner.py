#!/usr/bin/env python3
"""Obstac mount/metadata gate for the read-only #4485 posthoc audit."""
import hashlib
import json
import os
from pathlib import Path

SPEC = Path("/audit/FREEZE.json")
EVIDENCE = Path("/study")
OUT = Path("/evidence")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def refuse_write(directory):
    probe = directory / ".obstac-readonly-probe"
    try:
        probe.write_text("must-not-write")
    except OSError:
        return True
    else:
        probe.unlink(missing_ok=True)
        return False


freeze = json.loads(SPEC.read_text())
expected_env = {
    "OBSTAC_SOURCE_COMMIT": freeze["source"]["commit"],
    "OBSTAC_SOURCE_TREE": freeze["source"]["tree"],
    "OBSTAC_IMAGE_ID": freeze["container"]["image_id"],
    "OBSTAC_FREEZE_SHA256": sha(SPEC),
    "OBSTAC_DOCKER_CONTEXT": freeze["container"]["context"],
    "OBSTAC_PLATFORM": freeze["container"]["platform"],
}
for key, value in expected_env.items():
    if os.environ.get(key) != value:
        raise SystemExit(f"STOP_OBSTAC_METADATA {key}")
if os.environ.get("OBSTAC_RUN_KIND") not in {"construction", "posthoc-audit"}:
    raise SystemExit("STOP_OBSTAC_METADATA OBSTAC_RUN_KIND")
if os.environ["OBSTAC_RUN_KIND"] == "construction":
    if not refuse_write(Path("/repo")) or not refuse_write(EVIDENCE) or not refuse_write(SPEC.parent):
        raise SystemExit("STOP_OBSTAC_READONLY_MOUNT")
    if not (EVIDENCE / "formal_run_01/formal/AUDIT.json").is_file():
        raise SystemExit("STOP_OBSTAC_INPUT_MISSING")
    if not OUT.is_dir() or not os.access(OUT, os.W_OK):
        raise SystemExit("STOP_OBSTAC_OUTPUT_NOT_WRITABLE")
    marker = {
        "decision": "PASS_CONSTRUCTION_ONLY",
        "obstac_env": expected_env,
        "run_kind": "construction",
        "source_readonly": True,
        "study_readonly": True,
        "audit_spec_readonly": True,
        "evidence_writable": True,
        "broker_invocations": 0,
        "fake_invocations": 0,
        "model_calls": 0,
    }
    (OUT / "CONSTRUCTION.json").write_text(json.dumps(marker, sort_keys=True, indent=2) + "\n")
    print("OBSTAC_POSTHOC_CONSTRUCTION PASS source=ro study=ro audit_spec=ro evidence=rw broker=0 fake=0 model=0")
else:
    if not refuse_write(Path("/repo")) or not refuse_write(EVIDENCE) or not refuse_write(SPEC.parent):
        raise SystemExit("STOP_OBSTAC_READONLY_MOUNT")
    import subprocess

    result = subprocess.run(["python", "-B", "/audit/audit.py"], check=False)
    raise SystemExit(result.returncode)
