#!/usr/bin/env python3
"""Read-only, standard-library audit of Issue #4895's retained raw bytes.

This checks byte identity, frozen invocation bindings, row structure, recorded
predictions/labels, and the exact-vs-semantic distinction for B_ONLY and
B_DUPLICATE_CONTROL. It does not import runner.py/audit.py, use torch, fit a
model, or change any predecessor artifact.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import sys
from pathlib import Path

EXPECTED_RAW_SHA256 = "ed4560d01c99adb74230758c6c6bb22458159d1b76e790836c0936c3cac15349"
EXPECTED_RAW_BYTES = 964_795
EXPECTED_GZIP_SHA256 = "8754ceac5be2c46bb876ca0703a824337e395409caa8a69fef2eea72a1b00ab8"
EXPECTED_GZIP_BYTES = 361_312
EXPECTED_GZIP_GIT_BLOB = "fa2c21de7f55fa9c5c50c06c01e450120106efce"
EXPECTED_FREEZE_SHA256 = "cffa4feaf36cdaeaf899e0f4ddadefb30ae2d0c59059a87dc76dd7b93c705d9b"
EXPECTED_AUDIT_GIT_BLOB = "697c6068cbfe878338f78347fd4fa1e7b7e9a651"
EXPECTED_AUDIT_SHA256 = "02d9a98a6eee494ef8f04edee22b84224312dfc8cd33f26ba96039f197f49b32"
EXPECTED_ALLOCATION = "needle-online-lora-role-rehearsal-20260927-v1"
EXPECTED_SEEDS = [735211, 735311, 735411]
EXPECTED_ARMS = ["B_ONLY", "B_DUPLICATE_CONTROL", "A_REHEARSAL"]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def strict_json(data: bytes):
    def no_duplicates(pairs):
        out = {}
        for key, value in pairs:
            if key in out:
                raise ValueError(f"duplicate_json_key:{key}")
            out[key] = value
        return out

    return json.loads(data, object_pairs_hook=no_duplicates,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"nonfinite:{value}")))


def leaves(value, prefix=""):
    if isinstance(value, dict):
        for key in sorted(value):
            yield from leaves(value[key], f"{prefix}.{key}" if prefix else key)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from leaves(item, f"{prefix}[{index}]")
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        yield prefix, float(value)


def max_abs_diff(left, right):
    a, b = dict(leaves(left)), dict(leaves(right))
    if a.keys() != b.keys():
        return None
    return max((abs(a[key] - b[key]) for key in a), default=0.0)


def accuracy(predictions, labels):
    if not isinstance(predictions, list) or not isinstance(labels, list) or len(predictions) != len(labels) or not labels:
        raise ValueError("prediction_label_shape")
    if any(type(value) is not int for value in predictions + labels):
        raise ValueError("prediction_label_type")
    return sum(pred == label for pred, label in zip(predictions, labels)) / len(labels)


def audit(root: Path):
    freeze_bytes = (root / "FREEZE.json").read_bytes()
    sidecar = (root / "FREEZE.sha256").read_text(encoding="ascii").strip().split()
    freeze_sha = sha(freeze_bytes)
    gzip_bytes = (root / "formal" / "formal_result.json.gz").read_bytes()
    raw_bytes = gzip.decompress(gzip_bytes)
    invocation = strict_json((root / "formal" / "FORMAL_INVOCATION.json").read_bytes())
    audit_record = strict_json((root / "formal" / "audit" / "AUDIT.json").read_bytes())
    stdout = (root / "formal" / "docker.stdout.bin").read_bytes()
    stderr = (root / "formal" / "docker.stderr.bin").read_bytes()
    freeze = strict_json(freeze_bytes)
    raw = strict_json(raw_bytes)
    errors = []
    audit_source_bytes = (root / "audit.py").read_bytes()
    audit_source_sha = sha(audit_source_bytes)
    audit_source_git_blob = git_blob_sha(audit_source_bytes)

    if (len(gzip_bytes), sha(gzip_bytes)) != (EXPECTED_GZIP_BYTES, EXPECTED_GZIP_SHA256):
        errors.append("retained_gzip_identity")
    if git_blob_sha(gzip_bytes) != EXPECTED_GZIP_GIT_BLOB:
        errors.append("retained_gzip_git_blob")
    if (len(raw_bytes), sha(raw_bytes)) != (EXPECTED_RAW_BYTES, EXPECTED_RAW_SHA256):
        errors.append("expanded_raw_identity")
    if freeze_sha != EXPECTED_FREEZE_SHA256:
        errors.append("freeze_bytes_identity")
    if audit_source_sha != EXPECTED_AUDIT_SHA256 or audit_source_git_blob != EXPECTED_AUDIT_GIT_BLOB:
        errors.append("registered_auditor_source_identity")
    if freeze.get("source_sha256", {}).get("audit.py") != audit_source_sha:
        errors.append("registered_auditor_freeze_manifest")
    if not sidecar or sidecar[0] != freeze_sha:
        errors.append("freeze_sidecar_digest_token")
    if freeze.get("allocation") != EXPECTED_ALLOCATION or freeze.get("seeds") != EXPECTED_SEEDS:
        errors.append("freeze_identity")
    if (invocation.get("allocation") != EXPECTED_ALLOCATION
            or invocation.get("freeze_sha256") != freeze_sha
            or invocation.get("exit_code") != 0
            or invocation.get("formal_orchestrations") != 1
            or invocation.get("retries") != 0
            or invocation.get("raw_bytes") != len(raw_bytes)
            or invocation.get("raw_sha256") != sha(raw_bytes)
            or invocation.get("stdout_bytes") != len(stdout)
            or invocation.get("stdout_sha256") != sha(stdout)
            or invocation.get("stderr_bytes") != len(stderr)
            or invocation.get("stderr_sha256") != sha(stderr)
            or "--gpus" in invocation.get("command_argv", [])):
        errors.append("invocation_raw_binding")
    if (raw.get("allocation") != EXPECTED_ALLOCATION
            or raw.get("seeds") != EXPECTED_SEEDS
            or raw.get("arms") != EXPECTED_ARMS
            or raw.get("schema") != "needle-role-rehearsal-raw-v1"
            or len(raw.get("runs", [])) != len(EXPECTED_SEEDS)):
        errors.append("raw_identity_or_denominator")
    if [row.get("seed") for row in raw.get("runs", [])] != EXPECTED_SEEDS:
        errors.append("run_seed_order_or_uniqueness")

    argv = invocation.get("command_argv", [])
    required_argv = {
        "docker", "run", "--rm", "--pull=never", "--network=none", "--read-only",
        "--cpus=1", "--memory=2g", "--pids-limit=64", "--security-opt=no-new-privileges",
        "sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e",
        "runner.py", "NEEDLE_SEEDS=735211,735311,735411",
    }
    mounts = [argv[index + 1] for index, item in enumerate(argv[:-1]) if item == "--mount"]
    destinations = [mount.split(",dst=", 1)[1] if ",dst=" in mount else "" for mount in mounts]
    if (not required_argv.issubset(set(argv))
            or any(item == "--gpus" or item.startswith("--gpus=") for item in argv)
            or invocation.get("image_id") != "sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e"
            or invocation.get("inspected_image") != "sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e linux/amd64"
            or len(mounts) != 2 or destinations != ["/src,readonly", "/out"]):
        errors.append("formal_invocation_image_argv_or_mounts")

    expected_registered_errors = {"freeze_hash"} | {
        f"{seed}:duplicate_control_not_equivalent" for seed in EXPECTED_SEEDS
    }
    registered = audit_record.get("errors", [])
    if set(registered) != expected_registered_errors or len(registered) != len(expected_registered_errors):
        errors.append("registered_audit_error_set_differs_from_report")

    seed_results = []
    total_rows = 0
    all_exact_prediction_matches = True
    duplicate_diff_checkpoints = 0
    duplicate_checkpoints = 0
    maximum_adapter_delta = 0.0
    maximum_optimizer_delta = 0.0
    for run in raw.get("runs", []):
        seed = run.get("seed")
        arms = {arm.get("arm"): arm for arm in run.get("arms", [])}
        if seed not in EXPECTED_SEEDS or set(arms) != set(EXPECTED_ARMS):
            errors.append(f"seed_{seed}:arm_set")
            continue
        if (len(run.get("test_a_y", [])) != 256 or len(run.get("test_b_y", [])) != 256
                or len({tuple(row) for row in run.get("test_a_x", [])}) != 256
                or len({tuple(row) for row in run.get("test_b_x", [])}) != 256):
            errors.append(f"seed_{seed}:heldout_shape_or_unique_rows")
        if run.get("base_immutable") is not True or run.get("base_sha256") != run.get("base_after_sha256"):
            errors.append(f"seed_{seed}:base_immutable_receipt")

        final = {}
        curves = {}
        for arm_name in EXPECTED_ARMS:
            arm = arms[arm_name]
            arrivals = arm.get("arrivals", [])
            total_rows += len(arrivals)
            if len(arrivals) != 16 or arm.get("optimizer_steps") != 128 or len(arm.get("update_ns", [])) != 128:
                errors.append(f"seed_{seed}:{arm_name}:schedule_shape")
            if any(type(value) is not int or not 0 < value < 60_000_000 for value in arm.get("update_ns", [])):
                errors.append(f"seed_{seed}:{arm_name}:update_duration")
            arm_curve = {"A": [], "B": []}
            for index, row in enumerate(arrivals):
                if row.get("arrival") != index + 1:
                    errors.append(f"seed_{seed}:{arm_name}:arrival_order")
                arm_curve["A"].append(accuracy(row.get("pred_a"), run["test_a_y"]))
                arm_curve["B"].append(accuracy(row.get("pred_b"), run["test_b_y"]))
            curves[arm_name] = arm_curve
            final[arm_name] = {"A": arm_curve["A"][-1], "B": arm_curve["B"][-1]}

        one, duplicate = arms["B_ONLY"]["arrivals"], arms["B_DUPLICATE_CONTROL"]["arrivals"]
        for left, right in zip(one, duplicate):
            duplicate_checkpoints += 1
            if left != right:
                duplicate_diff_checkpoints += 1
            if left.get("pred_a") != right.get("pred_a") or left.get("pred_b") != right.get("pred_b"):
                all_exact_prediction_matches = False
            adapter_delta = max_abs_diff(left.get("adapter", {}), right.get("adapter", {}))
            optimizer_delta = max_abs_diff(left.get("optimizer", {}), right.get("optimizer", {}))
            if adapter_delta is None or optimizer_delta is None:
                errors.append(f"seed_{seed}:duplicate_state_shape")
            else:
                maximum_adapter_delta = max(maximum_adapter_delta, adapter_delta)
                maximum_optimizer_delta = max(maximum_optimizer_delta, optimizer_delta)

        delta_a = final["A_REHEARSAL"]["A"] - final["B_DUPLICATE_CONTROL"]["A"]
        b_gap = final["B_DUPLICATE_CONTROL"]["B"] - final["A_REHEARSAL"]["B"]
        seed_results.append({
            "seed": seed,
            "final_accuracy_recomputed_from_recorded_predictions": final,
            "rehearsal_A_gain_vs_duplicate_control": delta_a,
            "rehearsal_B_gap_vs_duplicate_control": b_gap,
            "passes_per_seed_quality_gate": (
                final["A_REHEARSAL"]["A"] >= 0.90
                and final["A_REHEARSAL"]["B"] >= 0.90
                and b_gap <= 0.10
            ),
        })

    if total_rows != 144:
        errors.append("checkpoint_denominator")
    if not all_exact_prediction_matches:
        errors.append("duplicate_predictions_differ")
    mean_a_gain = (sum(item["rehearsal_A_gain_vs_duplicate_control"] for item in seed_results)
                   / len(seed_results) if len(seed_results) == 3 else None)
    report = {
        "audit_schema": "issue4895-readonly-stdlib-raw-audit-v1",
        "allocation": EXPECTED_ALLOCATION,
        "decision": "PASS_RAW_IDENTITY_AND_DESCRIPTIVE_RECOMPUTATION" if not errors else "HOLD_READONLY_AUDIT",
        "scope": "Retained bytes and recorded predictions only; no optimizer replay, model fit, GPU, Docker, or change to registered audit/source/raw.",
        "source_identity": {
            "audit_py_sha256": audit_source_sha,
            "audit_py_git_blob": audit_source_git_blob,
            "frozen_audit_py_sha256": freeze.get("source_sha256", {}).get("audit.py"),
            "matches": audit_source_sha == freeze.get("source_sha256", {}).get("audit.py"),
            "freeze_sha256": freeze_sha,
            "sidecar_digest_token": sidecar[0] if sidecar else None,
            "sidecar_has_sha256sum_filename_suffix": len(sidecar) >= 2 and sidecar[-1] == "FREEZE.json",
        },
        "retained_artifacts": {
            "gzip_bytes": len(gzip_bytes), "gzip_sha256": sha(gzip_bytes),
            "gzip_git_blob": git_blob_sha(gzip_bytes),
            "raw_bytes": len(raw_bytes), "raw_sha256": sha(raw_bytes),
            "formal_exit_code": invocation.get("exit_code"),
            "formal_orchestrations": invocation.get("formal_orchestrations"),
            "retries": invocation.get("retries"),
            "inspected_image": invocation.get("inspected_image"),
            "formal_command_has_gpu_request": any(item == "--gpus" or item.startswith("--gpus=") for item in argv),
            "mount_destinations": destinations,
            "checkpoint_rows": total_rows,
        },
        "registered_audit_errors": registered,
        "duplicate_control_comparison": {
            "checkpoints": duplicate_checkpoints,
            "exact_full_record_differences": duplicate_diff_checkpoints,
            "predictions_identical_at_every_checkpoint": all_exact_prediction_matches,
            "maximum_adapter_scalar_absolute_difference": maximum_adapter_delta,
            "maximum_optimizer_scalar_absolute_difference": maximum_optimizer_delta,
            "interpretation": "Exact trajectory JSON equality is stronger than prediction equivalence; this read-only comparison does not declare the formal allocation valid or revise its HOLD.",
        },
        "seed_results": seed_results,
        "mean_rehearsal_A_gain_vs_duplicate_control": mean_a_gain,
        "all_three_per_seed_quality_gates_pass": len(seed_results) == 3 and all(item["passes_per_seed_quality_gate"] for item in seed_results),
        "errors": errors,
    }
    return report


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: audit_raw_stdlib.py ARTIFACT_ROOT OUTPUT_JSON")
    result = audit(Path(sys.argv[1]))
    output = Path(sys.argv[2])
    output.write_text(json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"decision": result["decision"], "errors": result["errors"],
                      "checkpoint_rows": result["retained_artifacts"]["checkpoint_rows"],
                      "duplicate_full_record_differences": result["duplicate_control_comparison"]["exact_full_record_differences"],
                      "predictions_identical": result["duplicate_control_comparison"]["predictions_identical_at_every_checkpoint"]}, sort_keys=True))
    raise SystemExit(0 if not result["errors"] else 2)
