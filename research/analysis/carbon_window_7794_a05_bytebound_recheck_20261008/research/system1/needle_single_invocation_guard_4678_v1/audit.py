#!/usr/bin/env python3
"""Independent raw-only validation of Issue #4678 preflight stop evidence."""
import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_IMAGE = "sha256:69f3c6830fda67fc5e8d3f6d8c09bbf730dffca043e3dfb70e433c84bc9db2a5"
EXPECTED_CHECKPOINT = "c234c70dccc7a9115e7c41ac2e41d3655fea3b85c245dd898b46179fb90c6c0c"
EXPECTED_CHECKPOINT_BYTES = 242047978
ALTERNATE_ARTIFACT = "c9d915eca282ed42d1a09b143b592adb4cc6744ffe2d294adf5cfc5548170c38"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def audit(doc):
    errors = []
    if doc.get("schema") != "needle-single-invocation-guard-4678-preflight.v1": errors.append("schema")
    if doc.get("issue") != 4678 or doc.get("source_issue") != 4205: errors.append("issue_lineage")
    src = doc.get("source_freeze", {})
    if src.get("expected_checkpoint_sha256") != EXPECTED_CHECKPOINT or src.get("expected_checkpoint_bytes") != EXPECTED_CHECKPOINT_BYTES:
        errors.append("frozen_checkpoint_identity")
    runtime = doc.get("runtime", {})
    if runtime.get("expected_image_id") != EXPECTED_IMAGE or runtime.get("observed_image_id") != EXPECTED_IMAGE or runtime.get("image_match") is not True:
        errors.append("image_identity")
    checkpoint = doc.get("checkpoint", {})
    if checkpoint.get("expected_present") is not False or checkpoint.get("observed_exact_sha256") is not None or checkpoint.get("observed_exact_bytes") is not None:
        errors.append("checkpoint_absence")
    alternate = checkpoint.get("substitute_observed", {})
    if alternate.get("sha256") != ALTERNATE_ARTIFACT or alternate.get("substitution_allowed") is not False:
        errors.append("substitute_confusion")
    gpu = doc.get("gpu", {})
    if gpu.get("name") != "NVIDIA GeForce RTX 3080 Laptop GPU" or gpu.get("memory_free_mib", 0) <= 0 or gpu.get("gpu_compute_invocations") != 0:
        errors.append("gpu_identity_or_availability")
    ran = doc.get("formal_or_smoke", {})
    if ran.get("training_image_docker_run_invocations") != 0 or ran.get("checkpoint_loads") != 0 or ran.get("optimizer_steps") != 0 or ran.get("guard_wrapper_started") is not False or ran.get("allocation_consumed") is not False:
        errors.append("no_run_boundary")
    if doc.get("decision") != "STOP_LOCAL_IMAGE_OR_GPU_UNAVAILABLE" or doc.get("stop_reason") != "PINNED_CHECKPOINT_NOT_CACHED_OR_EMBEDDED":
        errors.append("typed_stop")
    if doc.get("retry_count") != 0: errors.append("retry_count")
    return errors


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--preflight", required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args()
    doc = json.loads(Path(a.preflight).read_text(encoding="utf-8"))
    errors = audit(doc)
    result = {"schema": "needle-single-invocation-guard-4678-audit.v1",
              "decision": "AUDIT_STOP_RECORD_VALIDATED" if not errors else "HOLD_AUDIT",
              "errors": errors, "preflight_sha256": sha(a.preflight),
              "training_image_docker_run_invocations": doc.get("formal_or_smoke", {}).get("training_image_docker_run_invocations"),
              "independent_audit_docker_run_invocations": doc.get("formal_or_smoke", {}).get("independent_audit_docker_run_invocations"),
              "optimizer_steps": doc.get("formal_or_smoke", {}).get("optimizer_steps")}
    Path(a.out).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    raise SystemExit(0 if not errors else 2)


if __name__ == "__main__": main()

