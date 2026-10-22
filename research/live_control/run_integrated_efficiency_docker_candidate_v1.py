"""Explicit successor entrypoint binding the three-arm runner to Docker IPC."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from integrated_efficiency_model_v1 import CONTRACTS
import docker_model_call_backend_v1 as docker_backend
import run_integrated_efficiency_live_v1 as integrated_runner


USAGE_FIELDS = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens",
                "output_tokens", "reasoning_output_tokens")
REQUIRED_PREREG_SOURCES = {
    "run_integrated_efficiency_live_v1.py",
    "run_integrated_efficiency_docker_candidate_v1.py",
    "docker_model_call_backend_v1.py",
    "container_host_model_ipc_runner_v1.py",
    "../../runtime/host_model_ipc_broker_v1.py",
}


def _preflight_for(output_root: Path):
    output_root = Path(output_root).resolve()

    def preflight(arm: str, contract: str) -> dict:
        if arm not in integrated_runner.ARMS or contract not in CONTRACTS:
            raise ValueError("unknown integrated-efficiency arm or output contract")
        schema, instructions, _validator = CONTRACTS[contract]
        workspace = output_root / "workspaces" / arm
        workspace.mkdir(parents=True, exist_ok=False)
        result = docker_backend.preflight_schema(
            output_root / "preflight" / arm / "docker-backend",
            schema, instructions, workspace)
        usage = result.get("usage")
        if (type(usage) is not dict or set(usage) != set(USAGE_FIELDS)
                or any(type(usage[field]) is not int or usage[field] < 0
                       for field in USAGE_FIELDS)
                or usage["cached_input_tokens"] > usage["input_tokens"]):
            raise RuntimeError(
                "STOP_DOCKER_PREFLIGHT_INCOMPLETE_PROVIDER_USAGE; raw preflight retained")
        if (result.get("status") != "ENDPOINT_COMPATIBLE"
                or result.get("fresh") is not True
                or result.get("model_visible_images") != 0
                or result.get("retry_performed") is not False):
            raise RuntimeError("STOP_DOCKER_PREFLIGHT_NOT_FRESH_AND_COMPATIBLE")
        return {"call_id": result["call_id"], "stage": "schema_preflight",
                "requested_model": result["requested_model"],
                "requested_effort": result["requested_effort"],
                "usage": {field: usage[field] for field in USAGE_FIELDS},
                "model_visible_images": 0}

    return preflight


def run(output_root: Path) -> dict:
    output_root = Path(output_root).resolve()
    plan = json.loads((output_root / "preregistration.json").read_text(encoding="utf-8"))
    image_ref, platform = docker_backend.runtime_identity()
    expected_runtime = plan.get("docker_runtime")
    sources = plan.get("sources")
    if type(sources) is not dict or not REQUIRED_PREREG_SOURCES.issubset(sources):
        raise RuntimeError("STOP_DOCKER_PREREGISTRATION_MISSING_EXECUTION_SOURCES")
    if (type(expected_runtime) is not dict
            or expected_runtime.get("image_ref") != image_ref
            or expected_runtime.get("platform") != platform):
        raise RuntimeError("STOP_DOCKER_RUNTIME_IDENTITY_DIFFERS_FROM_PREREGISTRATION")
    return integrated_runner.main(
        model_call=docker_backend.call,
        schema_preflight=_preflight_for(output_root),
        output_root=output_root)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True,
                        help="fresh candidate directory containing preregistration.json")
    args = parser.parse_args()
    run(args.output_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
