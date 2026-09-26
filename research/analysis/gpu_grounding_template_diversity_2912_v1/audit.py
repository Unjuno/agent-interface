#!/usr/bin/env python3
"""Independent integrity audit for the retained #4546 pre-training STOP."""
import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FILES = ("PREREGISTRATION.md", "FREEZE.json", "environment.json", "CONSTRUCTION.md", "FORMAL_FAILURE.md",
         "evidence/stdout.txt", "evidence/stderr.txt", "evidence/traceback.txt", "evidence/CONSTRUCTION.json")


def audit(root=ROOT):
    root = Path(root)
    freeze_bytes = (root / "FREEZE.json").read_bytes()
    freeze = json.loads(freeze_bytes)
    prereg = (root / "PREREGISTRATION.md").read_bytes()
    env = json.loads((root / "environment.json").read_text(encoding="utf-8"))
    trace = (root / "evidence/traceback.txt").read_text(encoding="utf-8")
    errors = []
    if freeze["formal_invocations_completed"] != 0 or freeze["optimizer_steps_completed"] != 0:
        errors.append("formal training was not zero-step")
    if freeze["stop_code"] != "STOP_CUDA_DETERMINISTIC_ADAPTIVE_POOL_BACKWARD":
        errors.append("unexpected frozen stop code")
    if hashlib.sha256(prereg).hexdigest() != freeze["preregistration_sha256"]:
        errors.append("preregistration hash mismatch")
    if "adaptive_avg_pool2d_backward_cuda does not have a deterministic implementation" not in trace:
        errors.append("canonical CUDA failure evidence missing")
    if (env["docker"]["gpu_visible_in_docker"] is not True or
            env["host"]["pytorch"] != "2.5.1+cu121"):
        errors.append("environment boundary evidence mismatch")
    if env["allocation_commit"] != freeze["allocation_commit"]:
        errors.append("source/allocation commit mismatch")
    checks = json.loads((root / "evidence/CONSTRUCTION.json").read_text(encoding="utf-8"))
    if checks["checks"]["deterministic_full_model_backward"]["passed"] is not False:
        errors.append("frozen full-model backward STOP not retained")
    if checks["checks"]["minimal_adaptive_pool_backward"]["passed"] is not False:
        errors.append("minimal adaptive-pool STOP not retained")
    sums = (root / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
    declared = {}
    for line in sums:
        digest, rel = line.split("  ", 1)
        declared[rel] = digest
    for rel in FILES + ("EVIDENCE_SHA256SUMS.txt",):
        if rel not in declared:
            errors.append(f"missing digest entry: {rel}")
            continue
        p = root / rel
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != declared[rel]:
            errors.append(f"file digest mismatch: {rel}")
    evidence_digests = (root / "EVIDENCE_SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
    for line in evidence_digests:
        digest, rel = line.split("  ", 1)
        p = root / "evidence" / rel
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != digest:
            errors.append(f"evidence digest mismatch: {rel}")
    return {"status": "PASS_STOP_EVIDENCE_INTEGRITY" if not errors else "FAIL_AUDIT",
            "errors": errors,
            "files_checked": len(FILES),
            "raw_result_present": False,
            "formal_training_steps": 0,
            "mutation_controls": "not_applicable_to_preserved_environment_stop"}


if __name__ == "__main__":
    result = audit(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT)
    print(json.dumps(result, sort_keys=True, indent=2))
    raise SystemExit(0 if not result["errors"] else 1)
