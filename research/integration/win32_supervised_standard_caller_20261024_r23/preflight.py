"""Input-free compile and owned-hook lifecycle preflight for R23."""
from __future__ import annotations
import datetime as dt
import importlib.util
import json
from pathlib import Path
import py_compile
import sys

packet = Path(__file__).resolve().parent
result = {"schema": "win32-supervised-standard-caller-r23-preflight-v1",
          "utc": dt.datetime.now(dt.timezone.utc).isoformat(),
          "native_input_sent": False}
try:
    for name in ("probe.py", "audit.py"):
        py_compile.compile(str(packet / name), doraise=True)
        result[f"{name[:-3]}_py_compile"] = "pass"
    if sys.platform != "win32":
        raise RuntimeError("R23 requires native Windows")
    spec = importlib.util.spec_from_file_location("r23_probe_preflight", packet / "probe.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    hook = module.FrozenKeyHook(max_callback_hold_ms=250)
    result["hook_setup"] = dict(hook.trace)
    hook.stop()
    result["hook_cleanup"] = dict(hook.trace)
    if hook.trace.get("error") or not hook.trace.get("thread_exited"):
        raise RuntimeError(f"hook lifecycle was not clean: {hook.trace}")
    result["status"] = "PASS"
except BaseException as exc:
    result["status"] = "FAIL_OR_UNKNOWN"
    result["error"] = {"type": type(exc).__name__, "detail": str(exc)}
(packet / "preflight.json").write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({"status": result["status"],
                  "native_input_sent": result["native_input_sent"]}, sort_keys=True))
if result["status"] != "PASS":
    raise SystemExit(1)
