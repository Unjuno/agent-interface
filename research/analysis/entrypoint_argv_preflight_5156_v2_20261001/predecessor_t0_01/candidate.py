"""Harmless argv/preflight boundary smoke; not the #5156 owner runner."""
import argparse
import hashlib
import importlib
import json
import os
import sys
from pathlib import Path


def boundary(argv, expected_argv, dependency, runner):
    if argv != expected_argv:
        return {"decision": "STOP_ARGV_MISMATCH", "runner_calls": 0}
    try:
        importlib.import_module(dependency)
    except ImportError:
        return {"decision": "STOP_PREFLIGHT_DEPENDENCY_MISSING", "runner_calls": 0}
    result = runner()
    return {"decision": "PASS_ENTRYPOINT_ARGV_CONSTRUCTION", "runner_calls": 1,
            "runner_result": result, "preflight_module": dependency}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke-only", action="store_true")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    source = Path(__file__).read_bytes()
    case_bytes = Path("/work/cases.json").read_bytes()
    cases = json.loads(case_bytes)
    expected = cases["expected_argv"]
    result = boundary(sys.argv, expected, cases["preflight_module"], lambda: "smoke-runner")
    raw = {
        "schema": "entrypoint-argv-smoke-raw-v1",
        "allocation": cases["allocation"],
        "base_main_sha": os.environ["EXPERIMENT_BASE_SHA"],
        "container": {"image": os.environ["EXPERIMENT_IMAGE"],
                      "platform": os.environ["EXPERIMENT_PLATFORM"], "network": "none"},
        "image_entrypoint": cases["entrypoint"],
        "sys_executable": sys.executable,
        "sys_argv": sys.argv,
        "argv_exact": sys.argv == expected,
        "preflight": {"module": cases["preflight_module"],
                      "imported_before_runner": result["decision"] == "PASS_ENTRYPOINT_ARGV_CONSTRUCTION"},
        "boundary": result,
        "candidate_sha256": hashlib.sha256(source).hexdigest(),
        "input_sha256": hashlib.sha256(case_bytes).hexdigest(),
        "formal_runner_invocations": 0,
        "gui_input_calls": 0,
        "network_calls": 0,
        "model_calls": 0,
    }
    output = Path(args.output)
    output.write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"decision": result["decision"], "argv_exact": raw["argv_exact"],
                      "runner_calls": result["runner_calls"]}, sort_keys=True))
    if result["decision"] != "PASS_ENTRYPOINT_ARGV_CONSTRUCTION" or not raw["argv_exact"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
