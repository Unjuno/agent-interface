"""Harmless successor smoke for explicit Python entrypoint and argv preflight."""
import argparse
import hashlib
import importlib
import json
import os
import sys
from pathlib import Path


def effective_argv(image_config, override, command):
    executable = override if override is not None else image_config["Entrypoint"]
    if executable is not None:
        return list(executable) + list(command)
    return list(command) if command else list(image_config["Cmd"] or [])


def boundary(argv, expected_argv, dependency, runner):
    if argv != expected_argv:
        return {"decision": "STOP_ARGV_MISMATCH", "runner_calls": 0}
    try:
        importlib.import_module(dependency)
    except ImportError:
        return {"decision": "STOP_PREFLIGHT_DEPENDENCY_MISSING", "runner_calls": 0}
    return {"decision": "PASS_ENTRYPOINT_ARGV_CONSTRUCTION", "runner_calls": 1,
            "runner_result": runner(), "preflight_module": dependency}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke-only", action="store_true")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    source = Path(__file__).read_bytes()
    input_bytes = Path("/work/cases.json").read_bytes()
    spec = json.loads(input_bytes)
    resolved = effective_argv(spec["image_config"], spec["entrypoint_override"], spec["command"])
    outcome = boundary(sys.argv, spec["expected_sys_argv"], spec["preflight_module"],
                       lambda: "smoke-runner")
    raw = {
        "schema": "entrypoint-argv-smoke-v2-raw-v1",
        "allocation": spec["allocation"],
        "base_main_sha": os.environ["EXPERIMENT_BASE_SHA"],
        "container": {"image": os.environ["EXPERIMENT_IMAGE"],
                      "platform": os.environ["EXPERIMENT_PLATFORM"], "network": "none"},
        "image_config": spec["image_config"],
        "entrypoint_override": spec["entrypoint_override"],
        "resolved_process_argv": resolved,
        "sys_executable": sys.executable,
        "sys_argv": sys.argv,
        "argv_exact": sys.argv == spec["expected_sys_argv"],
        "preflight": {"module": spec["preflight_module"],
                      "imported_before_smoke_runner": outcome["decision"] == "PASS_ENTRYPOINT_ARGV_CONSTRUCTION"},
        "boundary": outcome,
        "candidate_sha256": hashlib.sha256(source).hexdigest(),
        "input_sha256": hashlib.sha256(input_bytes).hexdigest(),
        "formal_runner_invocations": 0,
        "gui_input_calls": 0,
        "network_calls": 0,
        "model_calls": 0,
    }
    Path(args.output).write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"decision": outcome["decision"], "resolved_process_argv": resolved,
                      "argv_exact": raw["argv_exact"], "runner_calls": outcome["runner_calls"]}, sort_keys=True))
    if outcome["decision"] != "PASS_ENTRYPOINT_ARGV_CONSTRUCTION" or not raw["argv_exact"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
