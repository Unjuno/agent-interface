"""Input-free R42 custody and frozen-source preflight."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
import time
from pathlib import Path

PACKET = Path(__file__).resolve().parent
ROOT = PACKET.parents[2]
C = json.loads((PACKET / "conditions.json").read_text(encoding="utf-8"))
OUT = {"schema": "win32-r49-preflight-v1",
       "attempt_id": C["attempt_id"],
       "utc": dt.datetime.now(dt.timezone.utc).isoformat(),
       "conditions_sha256": hashlib.sha256(
           (PACKET / "conditions.json").read_bytes()).hexdigest(),
       "native_input_sent": False,
       "checks": {}}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"],
            cwd=ROOT, text=True).strip()
        tracked = subprocess.run(["git", "status", "--porcelain=v1",
            "--untracked-files=no"], cwd=ROOT, capture_output=True,
            text=True, check=True).stdout.strip()
        OUT["source_commit"] = commit
        OUT["tracked_status"] = tracked
        OUT["python"] = sys.version
        OUT["platform"] = platform.platform()
        OUT["host"] = platform.node()
        clock_names = ("monotonic", "perf_counter")
        OUT["clock_info"] = {name: {
            "implementation": time.get_clock_info(name).implementation,
            "resolution_seconds": time.get_clock_info(name).resolution,
            "monotonic": time.get_clock_info(name).monotonic,
            "adjustable": time.get_clock_info(name).adjustable,
        } for name in clock_names}
        required_clock = C["clock_contract"]
        perf = OUT["clock_info"]["perf_counter"]
        OUT["checks"]["hold_deadline_and_audit_use_perf_counter_ns"] = (
            required_clock["deadline_clock"] == "time.perf_counter_ns"
            and required_clock["audit_clock"] == "time.perf_counter_ns"
            and perf["implementation"] == required_clock["implementation"]
            and perf["monotonic"] is True
            and perf["resolution_seconds"] <= required_clock["max_resolution_seconds"])
        OUT["checks"]["native_windows"] = sys.platform == "win32"
        OUT["checks"]["source_commit_matches"] = commit == C["source_commit"]
        OUT["checks"]["tracked_tree_clean"] = not tracked

        frozen = {rel: digest(PACKET / rel) for rel in C["frozen_files"]}
        OUT["frozen_files"] = frozen
        OUT["checks"]["frozen_packet_hashes_match"] = frozen == C["frozen_files"]
        source = {rel: digest(ROOT / rel) for rel in C["runtime_source_sha256"]}
        OUT["runtime_source_sha256"] = source
        OUT["checks"]["runtime_source_hashes_match"] = source == C["runtime_source_sha256"]

        predecessor = {}
        for name, rel in C["predecessor_hashes"].items():
            predecessor[name] = digest(ROOT / rel["path"])
        OUT["predecessor_hashes"] = predecessor
        OUT["checks"]["predecessors_match"] = predecessor == {
            name: rel["sha256"] for name, rel in C["predecessor_hashes"].items()}

        output_paths = ["run", "raw.json", "audit_r36.json", "task_raw.json",
                        "audit_r49.json", "phase2_status.json", "phases.json",
                        "PRERUN_CUSTODY.json", "SHA256SUMS"]
        existing = [rel for rel in output_paths if (PACKET / rel).exists()]
        OUT["existing_outputs"] = existing
        OUT["checks"]["all_attempt_outputs_absent"] = not existing
        markers = [PACKET / "run" / "phase1-foreground.json",
                   PACKET / "run" / "phase2_task" / "phase2-foreground.json"]
        marker_presence = {str(path.relative_to(PACKET)): path.exists() for path in markers}
        OUT["foreground_markers_before_attempt"] = marker_presence
        OUT["checks"]["foreground_markers_absent_before_attempt"] = not any(marker_presence.values())
        OUT["checks"]["conditions_id_matches_schema"] = (
            C.get("schema") == "win32-supervised-recovery-fresh-generation-task-r49-v1"
            and C["attempt_id"].startswith("win32-supervised-recovery-fresh-generation-task-20261024-r49-"))

        import importlib.util
        OUT["checks"]["mcp_sdk_available"] = importlib.util.find_spec("mcp") is not None

        if sys.platform == "win32":
            import winreg
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                        r"Control Panel\Desktop", 0, winreg.KEY_READ) as key:
                    hook_timeout = winreg.QueryValueEx(key, "LowLevelHooksTimeout")[0]
            except FileNotFoundError:
                hook_timeout = None
            OUT["low_level_hooks_timeout_registry"] = hook_timeout
            OUT["checks"]["hook_timeout_registry_matches"] = (
                hook_timeout is None if C["timeout_registry_expected"] == "absent"
                else hook_timeout == C["timeout_registry_expected"])

            with tempfile.TemporaryDirectory(prefix="r49-instrumentation-preflight-") as temp:
                trace_path = Path(temp) / "trace.jsonl"
                env = os.environ.copy()
                existing = env.get("PYTHONPATH", "")
                env["PYTHONPATH"] = str(PACKET / "instrumentation") + (
                    os.pathsep + existing if existing else "")
                env["AGENT_INTERFACE_CANCEL_TRACE"] = str(trace_path)
                env["AGENT_INTERFACE_REPO_ROOT"] = str(ROOT)
                smoke = subprocess.run([sys.executable, "-c",
                    "from runtime.backends.win32_v1.backend import Win32Backend; print('R49_TRACE_IMPORT_OK')"],
                    cwd=ROOT, env=env, capture_output=True, text=True, timeout=15)
                trace = ([json.loads(line) for line in trace_path.read_text(
                    encoding="utf-8").splitlines() if line.strip()]
                    if trace_path.exists() else [])
                seen = {row.get("event") for row in trace}
                OUT["instrumentation_smoke"] = {"returncode": smoke.returncode,
                    "stdout": smoke.stdout, "stderr": smoke.stderr, "trace": trace}
                OUT["checks"]["instrumentation_loaded_without_input"] = (
                    smoke.returncode == 0 and "R49_TRACE_IMPORT_OK" in smoke.stdout
                    and "sitecustomize_loaded" in seen
                    and "recovery_trace_wrappers_installed" in seen)

        OUT["status"] = "PASS" if all(OUT["checks"].values()) else "FAIL_OR_UNKNOWN"
    except BaseException as error:
        OUT["status"] = "FAIL_OR_UNKNOWN"
        OUT["error"] = {"type": type(error).__name__, "detail": str(error)}
    (PACKET / "preflight.json").write_text(json.dumps(
        OUT, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": OUT["status"], "checks": OUT["checks"],
        "native_input_sent": False}, sort_keys=True))
    return 0 if OUT["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
