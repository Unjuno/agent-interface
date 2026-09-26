"""Local Windows/Docker adapter with fail-closed monitor clock translation."""
from __future__ import annotations

import hashlib
import importlib.util
import os
import shlex
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
V10_PATH = HERE.parent / "map01_model_loop_finite_v10" / "adapter.py"
spec = importlib.util.spec_from_file_location("map01_finite_v10_adapter", V10_PATH)
v10 = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(v10)
base = v10.base

IMAGE = "agent-interface-map01-4544-local:amd64"
CODEX_EXE = r"C:\Users\junny\AppData\Local\OpenAI\Codex\bin\d23520d1e41bfb24\codex.exe"
base.CODEX = CODEX_EXE
TRANSLATION_REPLACEMENT = (
'''final_action_admission=final_admission_from_planner_result(
            planner_result,_planner_terminal_runtime_ns,
            invalidation,_controller_decided_runtime_ns)''',
'''if invalidation is not None:
            from receipt_translation import translate_monitor_receipt
            _translation_session_id=str(os.getpid())+"-"+str(time.time_ns())
            _translation_calibration={"clock_domain":"same_session_host_runtime_monotonic",
                "session_id":_translation_session_id,"probe_count":3,
                "host_clock_domain":"host_monotonic","runtime_clock_domain":"runtime_monotonic",
                "samples":[{k:sample[k] for k in ("host_send_ns","runtime_ns","host_receive_ns")}
                    for sample in _decision_clock_samples],
                "sampled_host_ns":_decision_clock_samples[-1]["host_receive_ns"],
                "offset_lower_ns":_decision_offset_lower,
                "offset_upper_ns":_decision_offset_upper}
            _translation_raw_path=runtime/"policy-invalidation-translations.jsonl"
            _translation_row={"iteration":index,"session_id":_translation_session_id,
                "raw_monitor_receipt":invalidation,"calibration":_translation_calibration,
                "translated_receipt":None}
            with _translation_raw_path.open("a") as _f:
                _f.write(json.dumps(_translation_row,sort_keys=True)+"\\n")
            invalidation=translate_monitor_receipt(invalidation,_translation_calibration,
                _translation_session_id,source_clock_domain="host_monotonic",
                now_host_ns=time.perf_counter_ns())
            _translation_row["translated_receipt"]=invalidation
            with _translation_raw_path.open("a") as _f:
                _f.write(json.dumps(_translation_row,sort_keys=True)+"\\n")
        final_action_admission=final_admission_from_planner_result(
            planner_result,_planner_terminal_runtime_ns,
            invalidation,_controller_decided_runtime_ns)''')
base.REPLACEMENTS = tuple(base.REPLACEMENTS) + (TRANSLATION_REPLACEMENT,)


def load_local_controller():
    module = base.load_controller()
    module.CODEX = CODEX_EXE
    module.IMAGE = IMAGE
    wad_host = Path(os.environ.get("AGENT_INTERFACE_4544_WAD", ""))
    if not wad_host.is_file():
        raise RuntimeError("AGENT_INTERFACE_4544_WAD must point to pinned Freedoom WAD")
    module.WAD = wad_host.resolve()

    def session_command(args, runtime):
        output_root = Path(args.out).resolve()
        source_root = base.REPO.resolve()
        shell = (
            "mkdir -p /tmp/home /tmp/xdg-config /tmp/xdg-cache /tmp/xdg-runtime "
            "&& chmod 700 /tmp/xdg-runtime && "
            "python3 /src/research/doom/session_map01_v12.py "
            f"--out /out/runtime --seed {int(args.seed)} "
            "--timeout-seconds 600 --skill 1 | python3 -c "
            + shlex.quote(base.SESSION_OUTPUT_FILTER)
        )
        return [
            "docker", "run", "--rm", "-i", "--network", "none", "--read-only",
            "--workdir", "/tmp", "--tmpfs", "/tmp:rw,nosuid,nodev,size=128m",
            "--tmpfs", "/run:rw,nosuid,nodev,size=32m",
            "-e", "PYTHONPATH=/src:/src/research/real_apps_v1:/src/research/doom/map01_enriched_policy_invalidation_4544_v1",
            "-e", "HOME=/tmp/home", "-e", "XDG_CONFIG_HOME=/tmp/xdg-config",
            "-e", "XDG_CACHE_HOME=/tmp/xdg-cache", "-e", "XDG_RUNTIME_DIR=/tmp/xdg-runtime",
            "-e", f"AGENT_RESULT_ROOT_HOST={output_root}",
            "-v", f"{source_root}:/src:ro", "-v", f"{output_root}:/out",
            "--entrypoint", "/usr/bin/bash", IMAGE, "-o", "pipefail", "-c", shell,
        ]

    module.win = lambda path: str(Path(path).resolve())
    module.session_command = session_command
    def app_server_command():
        command = [CODEX_EXE, "app-server", "--stdio"]
        for feature in module.DISABLED_FEATURES:
            command += ["--disable", feature]
        command += ["-c", "mcp_servers={}"]
        return command

    module.app_server_command = app_server_command
    return module


def main():
    module = load_local_controller()
    source = module._freshstart_effective_source
    if source.count('translate_monitor_receipt(invalidation,_translation_calibration') != 1:
        raise RuntimeError("effective source must contain one receipt translation call")
    if "async def main" in source:
        raise RuntimeError("unexpected async controller source")
    if "--prepare-only" in sys.argv:
        target = Path(sys.argv[sys.argv.index("--prepare-only") + 1]).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source, encoding="utf-8")
        print(f"effective_controller_sha256={module._freshstart_sha256}")
        print(f"effective_controller_path={target}")
        return
    module.main()


if __name__ == "__main__":
    main()
