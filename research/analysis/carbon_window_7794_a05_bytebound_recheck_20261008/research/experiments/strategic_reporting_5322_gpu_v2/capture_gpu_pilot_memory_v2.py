#!/usr/bin/env python3
"""No-disk adapter executing frozen GPU pilot/auditor source passed as base64 argv."""
import base64, contextlib, hashlib, io, json, sys, zlib
from pathlib import Path

ROOT = Path.cwd() / "research" / "experiments" / "strategic_reporting_5322_gpu_v2"
EXPECTED = {
    "pilot": "29f4d654dec7fe657de64e1031a6e16e7116cb2993630cc4741cbe8d500f82c9",
    "audit": "3c14de0c7a9572220b12de9507b0e2eaff346a08e1d6fa9ff874998c1b9b2949",
}
if len(sys.argv) != 3:
    raise SystemExit("STOP: runner requires frozen pilot and auditor base64 inputs")
pilot_source = base64.b64decode(sys.argv[1])
audit_source = base64.b64decode(sys.argv[2])
for name, source in (("pilot", pilot_source), ("audit", audit_source)):
    actual = hashlib.sha256(source).hexdigest()
    if actual != EXPECTED[name]:
        raise SystemExit(f"STOP: {name} source digest mismatch: {actual}")

FILES = {}
def memory_mkdir(self, *args, **kwargs): return None
def memory_write_text(self, data, *args, **kwargs):
    FILES[self.name] = str(data)
    return len(str(data))
def memory_read_text(self, *args, **kwargs): return FILES[self.name]
def memory_read_bytes(self): return FILES[self.name].encode("utf-8")
Path.mkdir = memory_mkdir
Path.write_text = memory_write_text
Path.read_text = memory_read_text
Path.read_bytes = memory_read_bytes

stdout = io.StringIO()
pilot_exit = None
sys.argv = [str(ROOT / "gpu_model_pilot_v2.py"), "--output", "memory-gpu-pilot-02"]
try:
    with contextlib.redirect_stdout(stdout):
        exec(compile(pilot_source.decode("utf-8"), str(ROOT / "gpu_model_pilot_v2.py"), "exec"),
             {"__name__": "__main__", "__file__": str(ROOT / "gpu_model_pilot_v2.py")})
except SystemExit as exc:
    pilot_exit = exc.code
except BaseException as exc:
    pilot_exit = "EXCEPTION"
    FILES["capture_exception.txt"] = repr(exc)
FILES["pilot_stdout.txt"] = stdout.getvalue()
FILES["capture_status.json"] = json.dumps({"pilot_exit": pilot_exit,
    "pilot_complete": "RESULT_STATUS.json" in FILES}, sort_keys=True) + "\n"

if "RESULT_STATUS.json" in FILES:
    audit_stdout = io.StringIO()
    audit_exit = None
    sys.argv = [str(ROOT / "audit_gpu_model_pilot_v2.py"), "memory-gpu-pilot-02"]
    try:
        with contextlib.redirect_stdout(audit_stdout):
            exec(compile(audit_source.decode("utf-8"), str(ROOT / "audit_gpu_model_pilot_v2.py"), "exec"),
                 {"__name__": "__main__", "__file__": str(ROOT / "audit_gpu_model_pilot_v2.py")})
    except SystemExit as exc:
        audit_exit = exc.code
    except BaseException as exc:
        audit_exit = "EXCEPTION"
        FILES["audit_exception.txt"] = repr(exc)
    FILES["audit_stdout.txt"] = audit_stdout.getvalue()
    FILES["audit_exit.json"] = json.dumps({"audit_exit": audit_exit}, sort_keys=True) + "\n"

sys.stdout.write("CAPTURE_B64:" + base64.b64encode(
    zlib.compress(json.dumps(FILES, sort_keys=True, separators=(",", ":")).encode("utf-8"), 9)
).decode("ascii") + "\n")
