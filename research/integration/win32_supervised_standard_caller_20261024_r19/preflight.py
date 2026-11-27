"""Input-free compile and hook lifecycle preflight for R19."""
from __future__ import annotations
import datetime as dt
import importlib.util
import json
from pathlib import Path
import py_compile
import sys

packet = Path(__file__).resolve().parent
result = {"schema": "win32-supervised-standard-caller-r19-preflight-v1",
          "utc": dt.datetime.now(dt.timezone.utc).isoformat(),
          "native_input_sent": False}
try:
    for name in ("probe.py", "audit.py"):
        py_compile.compile(str(packet / name), doraise=True)
    result["probe_py_compile"] = "pass"
    result["audit_py_compile"] = "pass"
    if sys.platform != "win32":
        raise RuntimeError("R19 requires native Windows")
    spec = importlib.util.spec_from_file_location("r19_probe_preflight", packet / "probe.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    hook = module.FrozenKeyHook()
    result["hook_setup"] = dict(hook.trace)
    hook.stop()
    result["hook_cleanup"] = dict(hook.trace)
    if hook.trace.get("error") or not hook.trace.get("thread_exited"):
        raise RuntimeError(f"hook setup/cleanup was not clean: {hook.trace}")
    result["status"] = "PASS"
except BaseException as exc:
    result["status"] = "FAIL_OR_UNKNOWN"
    result["error"] = {"type": type(exc).__name__, "detail": str(exc)}
(packet / "preflight.json").write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({"status": result["status"], "native_input_sent": False}, sort_keys=True))
if result["status"] != "PASS":
    raise SystemExit(1)
