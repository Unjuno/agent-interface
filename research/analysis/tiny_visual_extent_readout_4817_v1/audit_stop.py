from __future__ import annotations

import json
import sys
from pathlib import Path


def main(stop_path, freeze_path):
    stop = json.loads(Path(stop_path).read_text(encoding="utf-8"))
    freeze = json.loads(Path(freeze_path).read_text(encoding="utf-8"))
    errors = []
    if stop.get("schema") != "tiny-visual-extent-readout-stop-v1": errors.append("schema")
    if stop.get("issue") != 4828 or stop.get("allocation") != freeze.get("allocation"): errors.append("lineage")
    if stop.get("disposition") != "STOP_NUMPY_MISSING_FROM_FROZEN_IMAGE": errors.append("disposition")
    if stop.get("stage") != "construction_preflight_before_any_model_fit": errors.append("stage")
    if stop.get("formal_fits") != 0 or stop.get("construction_fits") != 0 or stop.get("retries") != 0: errors.append("fit_discipline")
    if stop.get("image_substitution") is not False: errors.append("image_substitution")
    expected = stop.get("expected_image", {})
    observed = stop.get("observed_image", {})
    if expected.get("id") != freeze.get("image", {}).get("id") or observed.get("id") != expected.get("id"): errors.append("image_identity")
    if expected.get("numpy") != "1.24.2" or observed.get("numpy_spec") is not None: errors.append("numpy_observation")
    runtime = stop.get("runtime_probe", {})
    if runtime.get("exit_code") != 0 or "3.11.16" not in runtime.get("stdout", "") or "numpy None" not in runtime.get("stdout", ""):
        errors.append("runtime_probe")
    preflight = stop.get("preflight", {})
    if preflight.get("exit_code") != 1 or "ModuleNotFoundError: No module named 'numpy'" not in preflight.get("stderr", ""): errors.append("preflight_trace")
    if preflight.get("training_started") is not False or preflight.get("gpu_requested") is not False: errors.append("execution_boundary")
    if preflight.get("network") != "none" or preflight.get("source_mount") != "read-only" or preflight.get("rootfs") != "read-only": errors.append("sandbox")
    if preflight.get("cpu_limit") != 1 or preflight.get("memory_limit") != "2g" or preflight.get("pids_limit") != 64: errors.append("resource_limits")
    result = {"schema": "tiny-visual-extent-readout-stop-audit-v1", "decision": "PASS_STOP_EVIDENCE_INTEGRITY" if not errors else "FAIL_STOP_EVIDENCE_INTEGRITY", "checks": 12, "errors": errors, "formal_fits": 0, "construction_fits": 0}
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: audit_stop.py STOP.json FREEZE.json")
    raise SystemExit(main(*sys.argv[1:]))
