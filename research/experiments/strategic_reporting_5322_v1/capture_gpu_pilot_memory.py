#!/usr/bin/env python3
"""Memory-only IO adapter for the frozen Issue #5322 local GPU pilot."""
import base64
import contextlib
import hashlib
import io
import json
import runpy
import sys
import zlib
from pathlib import Path

ROOT = Path.cwd() / "research" / "experiments" / "strategic_reporting_5322_v1"
PILOT = ROOT / "gpu_model_pilot.py"
AUDITOR = ROOT / "audit_gpu_model_pilot.py"
EXPECTED = {
    "gpu_model_pilot.py": "7df869523736423965bb44cb67b5a9c39524f320188d97f932f575a7be1f3625",
    "audit_gpu_model_pilot.py": "d5c6e7a25f2e1b5bb47b10f9e6353c32531e7aa7999a74cfdc764cee3b452c22",
}
for path in (PILOT, AUDITOR):
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != EXPECTED[path.name]:
        raise SystemExit(f"STOP: frozen source hash mismatch for {path.name}: {actual}")

FILES = {}
original_mkdir = Path.mkdir
original_write_text = Path.write_text
original_read_text = Path.read_text
original_read_bytes = Path.read_bytes

def memory_mkdir(self, *args, **kwargs):
    return None

def memory_write_text(self, data, *args, **kwargs):
    FILES[self.name] = str(data)
    return len(str(data))

def memory_read_text(self, *args, **kwargs):
    return FILES[self.name]

def memory_read_bytes(self):
    return FILES[self.name].encode("utf-8")

Path.mkdir = memory_mkdir
Path.write_text = memory_write_text
Path.read_text = memory_read_text
Path.read_bytes = memory_read_bytes

pilot_stdout = io.StringIO()
pilot_exit = None
sys.argv = [str(PILOT), "--output", "memory-gpu-pilot-01"]
try:
    with contextlib.redirect_stdout(pilot_stdout):
        runpy.run_path(str(PILOT), run_name="__main__")
except SystemExit as exc:
    pilot_exit = exc.code
except BaseException as exc:
    pilot_exit = "EXCEPTION"
    FILES["capture_exception.txt"] = repr(exc)

FILES["pilot_stdout.txt"] = pilot_stdout.getvalue()
FILES["capture_status.json"] = json.dumps(
    {"pilot_exit": pilot_exit, "pilot_complete": "RESULT_STATUS.json" in FILES},
    sort_keys=True,
) + "\n"

if "RESULT_STATUS.json" in FILES:
    audit_stdout = io.StringIO()
    audit_exit = None
    sys.argv = [str(AUDITOR), "memory-gpu-pilot-01"]
    try:
        with contextlib.redirect_stdout(audit_stdout):
            runpy.run_path(str(AUDITOR), run_name="__main__")
    except SystemExit as exc:
        audit_exit = exc.code
    except BaseException as exc:
        audit_exit = "EXCEPTION"
        FILES["audit_exception.txt"] = repr(exc)
    FILES["audit_stdout.txt"] = audit_stdout.getvalue()
    FILES["audit_exit.json"] = json.dumps({"audit_exit": audit_exit}, sort_keys=True) + "\n"

Path.mkdir = original_mkdir
Path.write_text = original_write_text
Path.read_text = original_read_text
Path.read_bytes = original_read_bytes
sys.stdout.write("CAPTURE_B64:" + base64.b64encode(
    zlib.compress(json.dumps(FILES, sort_keys=True, separators=(",", ":")).encode("utf-8"), 9)
).decode("ascii") + "\n")
