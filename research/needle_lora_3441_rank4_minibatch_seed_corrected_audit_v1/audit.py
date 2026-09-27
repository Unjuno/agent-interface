"""Independent CPU reconstruction of Issue #3887 retained evidence.

This module intentionally does not import SOURCE_RUNNER.py or the predecessor
audit.py. It performs no optimizer/model evaluation and never requests CUDA.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
from typing import Any

import torch


SOURCE_DIR = Path("research/needle_lora_3441_rank4_minibatch_seed_corrected_v1")
AUDIT_DIR = Path("research/needle_lora_3441_rank4_minibatch_seed_corrected_audit_v1")
SEEDS = [3451, 3452, 3453, 3454, 3455]
ROLES = ["rank4_legacy_seed35", "rank4_shared_seed31"]
YIELDS = {
    "unknown_role": "YIELD",
    "stale_epoch": "YIELD",
    "wrong_version": "YIELD",
    "missing_adapter": "YIELD",
    "missing_epoch": "YIELD",
}
EXPECTED_DESIGN = {
    "base_rows": 512,
    "support_rows": 16,
    "heldout_rows": 4096,
    "base_steps": 400,
    "updates_per_arrival": 8,
    "total_updates": 128,
    "arms": ROLES,
    "seeds": SEEDS,
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encode_labels(labels: list[int]) -> bytes:
    if len(labels) % 4:
        raise ValueError("four 2-bit labels are required per byte")
    packed = bytearray()
    for pos in range(0, len(labels), 4):
        group = labels[pos : pos + 4]
        if any(type(x) is not int or not 0 <= x <= 3 for x in group):
            raise ValueError("label outside two-bit class range")
        packed.append((group[0] << 6) | (group[1] << 4) | (group[2] << 2) | group[3])
    return bytes(packed)


def decode_labels(packed: bytes, count: int) -> list[int]:
    values: list[int] = []
    for byte in packed:
        values.extend(((byte >> 6) & 3, (byte >> 4) & 3, (byte >> 2) & 3, byte & 3))
    if count < 0 or count > len(values):
        raise ValueError("declared label count exceeds packed data")
    return values[:count]


def tensor_digest(tensor: torch.Tensor) -> str:
    value = tensor.detach().to(device="cpu").contiguous()
    h = hashlib.sha256()
    h.update(str(value.dtype).encode("ascii"))
    h.update(str(tuple(value.shape)).encode("ascii"))
    h.update(value.numpy().tobytes())
    return h.hexdigest()


def percentile95(values: list[float]) -> float | None:
    if not values:
        return None
    return sorted(values)[math.ceil(0.95 * len(values)) - 1]


def check_metric(
    metric: dict[str, Any], expected: list[int], role: str, context: str
) -> tuple[list[str], list[int] | None, int | None]:
    """Decode one retained row and recompute its route, digest and score."""
    errors: list[str] = []
    required_route = {
        "requested_role": role,
        "selected_adapter": role,
        "decision": "PROPOSE",
        "epoch": 1,
        "version": 16,
        "n": len(expected),
    }
    for field, value in required_route.items():
        if metric.get(field) != value:
            errors.append(f"{context}:route_or_{field}")

    try:
        packed = base64.b64decode(metric.get("predicted_b64", ""), validate=True)
        predicted = decode_labels(packed, len(expected))
    except (binascii.Error, ValueError, TypeError):
        errors.append(f"{context}:prediction_encoding")
        return errors, None, None

    actual_hash = digest(packed)
    if len(packed) != len(expected) // 4:
        errors.append(f"{context}:prediction_bytes")
    if metric.get("predicted_sha256") != actual_hash:
        errors.append(f"{context}:metric_prediction_hash")

    correct = sum(left == right for left, right in zip(expected, predicted))
    accuracy = correct / len(expected) if expected else 0.0
    if metric.get("correct") != correct:
        errors.append(f"{context}:correct_count")
    if metric.get("accuracy") != accuracy:
        errors.append(f"{context}:accuracy")
    return errors, predicted, correct


def regenerate(seed: int) -> dict[str, torch.Tensor]:
    """Regenerate the frozen CPU datasets from their declared seeds."""
    def randn(rows: int, cols: int, offset: int) -> torch.Tensor:
        generator = torch.Generator(device="cpu").manual_seed(seed + offset)
        return torch.randn(rows, cols, generator=generator, device="cpu")

    return {
        "base_x": randn(512, 8, 1),
        "support_x": randn(16, 8, 2),
        "heldout_A_x": randn(4096, 8, 3),
        "heldout_B_x": randn(4096, 8, 4),
    }


def labels_for(data: dict[str, torch.Tensor]) -> dict[str, list[int]]:
    xa, xb = data["base_x"], data["support_x"]
    ea, eb = data["heldout_A_x"], data["heldout_B_x"]
    base_y = (xa[:, 0] > 0).long() * 2 + (xa[:, 1] > 0).long()
    support_y = (1 - (xb[:, 0] > 0).long()) * 2 + (xb[:, 1] > 0).long()
    heldout_A_y = (ea[:, 0] > 0).long() * 2 + (ea[:, 1] > 0).long()
    heldout_B_y = (1 - (eb[:, 0] > 0).long()) * 2 + (eb[:, 1] > 0).long()
    return {
        "base_y": base_y.tolist(),
        "support_y": support_y.tolist(),
        "heldout_A_y": heldout_A_y.tolist(),
        "heldout_B_y": heldout_B_y.tolist(),
    }


def expected_tensor_hashes(
    data: dict[str, torch.Tensor], labels: dict[str, list[int]]
) -> dict[str, str]:
    tensors = {
        "base_x": data["base_x"],
        "base_y": torch.tensor(labels["base_y"], dtype=torch.int64),
        "support_x": data["support_x"],
        "support_y": torch.tensor(labels["support_y"], dtype=torch.int64),
        "heldout_A_x": data["heldout_A_x"],
        "heldout_A_y": torch.tensor(labels["heldout_A_y"], dtype=torch.int64),
        "heldout_B_x": data["heldout_B_x"],
        "heldout_B_y": torch.tensor(labels["heldout_B_y"], dtype=torch.int64),
    }
    return {name: tensor_digest(tensor) for name, tensor in tensors.items()}


def expected_feedback_order(seed: int) -> list[int]:
    gen = torch.Generator(device="cpu").manual_seed(seed + 30)
    return torch.randperm(16, generator=gen, device="cpu").tolist()


def expected_sampler_hash(seed: int, role: str, feedback_order: list[int]) -> str:
    offset = 35 if role == ROLES[0] else 31
    gen = torch.Generator(device="cpu").manual_seed(seed + offset)
    visible: list[int] = []
    sampled: list[int] = []
    for row_id in feedback_order:
        visible.append(row_id)
        for _ in range(8):
            picks = torch.randint(len(visible), (32,), generator=gen, device="cpu").tolist()
            sampled.extend(visible[index] for index in picks)
    return digest(bytes(sampled))


def _hex_digest(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(ch in "0123456789abcdef" for ch in value)
    )


def audit_result(result: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    records = result.get("records")
    if result.get("allocation") != "needle-lora-3441-rank4-minibatch-seed-corrected-index-v1":
        errors.append("allocation")
    if result.get("seeds") != SEEDS:
        errors.append("seed_list")
    if result.get("frozen_design") != EXPECTED_DESIGN:
        errors.append("design")
    if not isinstance(records, list) or [r.get("seed") for r in records] != SEEDS:
        errors.append("record_seed_order_or_denominator")
        records = records if isinstance(records, list) else []

    env = result.get("environment", {})
    frozen_env = {
        "device": "NVIDIA GeForce RTX 3080 Laptop GPU",
        "cuda": "12.1",
        "torch": "2.5.1+cu121",
        "python": "3.11.9",
        "threads": 1,
        "deterministic": True,
        "tf32": False,
        "cublas_workspace_config": ":4096:8",
    }
    for field, value in frozen_env.items():
        if env.get(field) != value:
            errors.append(f"environment:{field}")

    per_seed: dict[str, Any] = {}
    legacy_scores: list[float] = []
    shared_scores: list[float] = []
    timings: list[float] = []
    curve_predictions = 0

    for index, record in enumerate(records):
        seed = SEEDS[index] if index < len(SEEDS) else record.get("seed", -1)
        label = str(seed)
        data = regenerate(seed) if seed in SEEDS else None
        if data is None:
            errors.append(f"{label}:unexpected_seed")
            continue
        labels = labels_for(data)
        expected_b = labels["heldout_B_y"]
        expected_a = labels["heldout_A_y"]

        if record.get("arm_order") != (
            [ROLES[0], ROLES[1]] if index % 2 == 0 else [ROLES[1], ROLES[0]]
        ):
            errors.append(f"{label}:balanced_arm_order")
        feedback_order = expected_feedback_order(seed)
        if record.get("feedback_order") != feedback_order:
            errors.append(f"{label}:feedback_order")
        if record.get("data_sha256") != expected_tensor_hashes(data, labels):
            errors.append(f"{label}:regenerated_data_hashes")

        packed_truth = encode_labels(expected_b)
        try:
            stored_truth = base64.b64decode(record.get("expected_B_labels_b64", ""), validate=True)
        except (binascii.Error, TypeError):
            stored_truth = b""
        if stored_truth != packed_truth:
            errors.append(f"{label}:expected_B_labels")
        if record.get("expected_B_labels_sha256") != digest(packed_truth):
            errors.append(f"{label}:expected_B_labels_hash")

        base = record.get("base_A", {})
        for field, value in {
            "requested_role": "A",
            "role": "A",
            "decision": "PROPOSE",
            "epoch": 1,
            "version": 0,
            "n": 4096,
        }.items():
            if base.get(field) != value:
                errors.append(f"{label}:base_route_{field}")
        try:
            base_packed = base64.b64decode(base.get("predicted_b64", ""), validate=True)
            base_predicted = decode_labels(base_packed, 4096)
        except (binascii.Error, ValueError, TypeError):
            base_packed, base_predicted = b"", []
            errors.append(f"{label}:base_prediction_encoding")
        base_correct = sum(a == b for a, b in zip(expected_a, base_predicted))
        if len(base_packed) != 1024:
            errors.append(f"{label}:base_prediction_length")
        if base.get("predicted_sha256") != digest(base_packed):
            errors.append(f"{label}:base_prediction_hash")
        if base.get("correct") != base_correct or base.get("accuracy") != base_correct / 4096:
            errors.append(f"{label}:base_metric")
        if record.get("base_immutable") is not True:
            errors.append(f"{label}:base_immutable")
        if record.get("base_initial_sha256") != record.get("initial_adapter_sha256"):
            errors.append(f"{label}:base_initial_digest")
        if record.get("invalid_routes") != YIELDS:
            errors.append(f"{label}:yield_controls")

        curve_accuracy: dict[str, float] = {}
        arms = record.get("arms", {})
        if set(arms) != set(ROLES):
            errors.append(f"{label}:arm_set")
        for role in ROLES:
            arm = arms.get(role, {})
            if arm.get("initial_sha256") != record.get("initial_adapter_sha256"):
                errors.append(f"{label}:{role}:initial_digest")
            if arm.get("initial_state_exact") is not True:
                errors.append(f"{label}:{role}:initial_state_copy")
            for name in ("adapter_setup_ms", "optimizer_setup_ms"):
                value = arm.get(name)
                if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                    errors.append(f"{label}:{role}:{name}")
            times = arm.get("feedback_ms", [])
            if (
                not isinstance(times, list)
                or len(times) != 16
                or any(type(t) not in (int, float) or not math.isfinite(t) or t < 0 for t in times)
            ):
                errors.append(f"{label}:{role}:timings")
            else:
                timings.extend(times)

            if arm.get("sampler_schedule_sha256") != expected_sampler_hash(seed, role, feedback_order):
                errors.append(f"{label}:{role}:sampler_schedule")
            curve = arm.get("curve", [])
            if not isinstance(curve, list) or len(curve) != 16:
                errors.append(f"{label}:{role}:curve_denominator")
                curve = curve if isinstance(curve, list) else []
            accuracies: list[float] = []
            for ordinal, row in enumerate(curve, start=1):
                if row.get("feedback_seen") != ordinal:
                    errors.append(f"{label}:{role}:{ordinal}:arrival")
                metric = row.get("metrics", {})
                row_errors, predicted, correct = check_metric(
                    metric, expected_b, role, f"{label}:{role}:{ordinal}"
                )
                errors.extend(row_errors)
                if predicted is not None and correct is not None:
                    curve_predictions += len(predicted)
                    accuracy = correct / 4096
                    accuracies.append(accuracy)
                    packed = base64.b64decode(metric["predicted_b64"], validate=True)
                    if row.get("predicted_sha256") != digest(packed):
                        errors.append(f"{label}:{role}:{ordinal}:row_prediction_hash")
                else:
                    accuracies.append(float("nan"))

            final_metric = record.get("final", {}).get(role, {})
            if curve and final_metric.get("predicted_b64") != curve[-1].get("metrics", {}).get("predicted_b64"):
                errors.append(f"{label}:{role}:final_prediction_mismatch")
            if curve and final_metric.get("accuracy") != accuracies[-1]:
                errors.append(f"{label}:{role}:final_accuracy_mismatch")
            if curve and len(curve) == 16:
                curve_accuracy[role] = accuracies[-1]

        snapshot = record.get("snapshot", {})
        if snapshot.get("roundtrip_exact") is not True or snapshot.get("rollback_exact") is not True:
            errors.append(f"{label}:snapshot_claims")
        if snapshot.get("initial_sha256") != record.get("initial_adapter_sha256"):
            errors.append(f"{label}:snapshot_initial_digest")
        if not all(_hex_digest(snapshot.get(key)) for key in ("initial_sha256", "learned_sha256", "serialized_sha256")):
            errors.append(f"{label}:snapshot_digest_shape")
        if type(snapshot.get("bytes")) is not int or snapshot["bytes"] <= 0:
            errors.append(f"{label}:snapshot_bytes")

        if set(curve_accuracy) == set(ROLES):
            legacy_scores.append(curve_accuracy[ROLES[0]])
            shared_scores.append(curve_accuracy[ROLES[1]])
            per_seed[label] = {
                "legacy": curve_accuracy[ROLES[0]],
                "shared": curve_accuracy[ROLES[1]],
            }

    mean_legacy = sum(legacy_scores) / len(legacy_scores) if legacy_scores else None
    mean_shared = sum(shared_scores) / len(shared_scores) if shared_scores else None
    gain = mean_shared - mean_legacy if mean_legacy is not None and mean_shared is not None else None
    p95 = percentile95(timings)
    if len(legacy_scores) != len(SEEDS) or len(shared_scores) != len(SEEDS):
        errors.append("final_score_denominator")
    if curve_predictions != 5 * 2 * 16 * 4096:
        errors.append("heldout_prediction_denominator")
    if len(timings) != 5 * 2 * 16:
        errors.append("timing_denominator")

    if errors:
        decision = "FAIL_ROUTE_OR_STATE_INTEGRITY"
    elif mean_legacy is not None and mean_legacy > 0.10:
        decision = "HOLD_LEGACY_COLLAPSE_NOT_REPRODUCED"
    elif (
        mean_legacy is not None
        and mean_shared is not None
        and all(value >= 0.90 for value in shared_scores)
        and gain is not None
        and gain >= 0.50
        and p95 is not None
        and p95 <= 60
    ):
        decision = "PASS_SAMPLER_SEED_EXPLAINS_COLLAPSE_SCOPED"
    else:
        decision = "FAIL_SAMPLER_SEED_NOT_SUFFICIENT"

    return {
        "disposition": decision,
        "integrity": not errors,
        "errors": sorted(errors),
        "records": len(records),
        "curves_per_arm_per_seed": 16,
        "audited_curve_predictions": curve_predictions,
        "expected_curve_predictions": 5 * 2 * 16 * 4096,
        "regenerated_expected_labels": True,
        "per_seed": per_seed,
        "legacy_mean": mean_legacy,
        "shared_mean": mean_shared,
        "paired_mean_gain": gain,
        "timing_count": len(timings),
        "feedback_p95_ms": p95,
        "snapshot_note": "Recorded tensor roundtrip/rollback assertions and digests were validated structurally; tensor payloads are not in the raw bundle for independent byte replay.",
    }


def git_blob(repo: Path, commit: str, path: str) -> tuple[bytes, str]:
    oid = subprocess.check_output(
        ["git", "rev-parse", f"{commit}:{path}"], cwd=repo, text=True
    ).strip()
    content = subprocess.check_output(["git", "cat-file", "blob", oid], cwd=repo)
    return content, oid


def load_evidence(repo: Path, freeze: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, str], list[str], dict[str, str]]:
    errors: list[str] = []
    hashes: dict[str, str] = {}
    blobs: dict[str, str] = {}
    pinned_commit = freeze["input_main_commit"]
    pinned_blobs = freeze["input_git_blob_sha1"]

    def read(name: str) -> bytes:
        path = (SOURCE_DIR / name).as_posix()
        try:
            content, oid = git_blob(repo, pinned_commit, path)
        except subprocess.CalledProcessError:
            errors.append(f"missing_git_blob:{name}")
            return b""
        blobs[name] = oid
        expected_oid = pinned_blobs.get(name)
        if oid != expected_oid:
            errors.append(f"git_blob_pin_mismatch:{name}")
        actual_sha = digest(content)
        hashes[name] = actual_sha
        expected_sha = freeze["input_sha256"].get(name)
        if expected_sha and actual_sha != expected_sha:
            errors.append(f"sha256_pin_mismatch:{name}")
        return content

    names = [
        "FREEZE.json", "FORMAL_METADATA.json", "FORMAL_STDOUT.json",
        "FORMAL_STDERR.txt", "RAW_RESULT.json.gz.b64", "SOURCE_RUNNER.py",
        "SOURCE_3807_BASELINE.py", "audit.py", "AUDIT.json", "REPORT.md",
        "TEST_CONSTRUCTION.py", "SHA256SUMS.txt",
    ]
    inputs = {name: read(name) for name in names}
    try:
        original_freeze = json.loads(inputs["FREEZE.json"].decode("utf-8"))
        metadata = json.loads(inputs["FORMAL_METADATA.json"].decode("utf-8"))
        formal = json.loads(inputs["FORMAL_STDOUT.json"].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        errors.append(f"input_parse_error:{type(exc).__name__}")
        return None, hashes, sorted(set(errors)), blobs

    expected_reference_blob = original_freeze.get("reference_3807_runner_git_blob")
    baseline_oid = blobs.get("SOURCE_3807_BASELINE.py")
    if baseline_oid != expected_reference_blob:
        errors.append("reference_baseline_git_blob_mismatch")
    for name, expected in original_freeze.get("source_sha256", {}).items():
        if hashes.get(name) != expected:
            errors.append(f"predecessor_freeze_source_sha256_mismatch:{name}")

    manifest = inputs["SHA256SUMS.txt"].decode("utf-8", errors="replace").splitlines()
    manifest_entries: dict[str, str] = {}
    malformed_manifest_lines: list[str] = []
    for line in manifest:
        match = re.fullmatch(r"([0-9a-f]{64})  ([^\t]+)", line)
        if match:
            manifest_entries[match.group(2)] = match.group(1)
        elif line.strip():
            malformed_manifest_lines.append(line)
    for name, expected in manifest_entries.items():
        if name in hashes and hashes[name] != expected:
            errors.append(f"sha256_manifest_mismatch:{name}")
    if malformed_manifest_lines:
        errors.append("malformed_sha256_manifest_preamble")

    try:
        envelope_gzip = base64.b64decode(formal["result_gzip_b64"], validate=True)
        sidecar_gzip = base64.b64decode(inputs["RAW_RESULT.json.gz.b64"].strip(), validate=True)
        if envelope_gzip != sidecar_gzip:
            errors.append("compressed_sidecar_mismatch")
        raw = gzip.decompress(envelope_gzip)
        raw_sha = digest(raw)
        hashes["decompressed_raw"] = raw_sha
        if len(raw) != formal.get("result_bytes") or raw_sha != formal.get("result_sha256"):
            errors.append("envelope_raw_hash_mismatch")
        if len(raw) != metadata.get("rawPayloadBytes") or raw_sha != metadata.get("rawPayloadSha256"):
            errors.append("metadata_raw_hash_mismatch")
        result = json.loads(raw.decode("utf-8"))
    except (binascii.Error, OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
        errors.append(f"raw_payload_decode_error:{type(exc).__name__}")
        result = None

    diagnostic = {
        "input_main_commit": pinned_commit,
        "expected_reference_runner_blob": expected_reference_blob,
        "observed_reference_runner_blob": baseline_oid,
        "malformed_manifest_lines": malformed_manifest_lines,
        "manifest_entries": len(manifest_entries),
        "errors": sorted(set(errors)),
    }
    hashes["manifest_expected_entries"] = str(len(manifest_entries))
    return result, hashes, sorted(set(errors)), {**blobs, "_diagnostic": json.dumps(diagnostic, sort_keys=True)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise SystemExit("STOP_OUTPUT_EXISTS")
    freeze_path = args.repo.resolve() / AUDIT_DIR / "FREEZE.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    audit_source = args.repo.resolve() / AUDIT_DIR / "audit.py"
    test_source = args.repo.resolve() / AUDIT_DIR / "test_audit.py"
    if digest(audit_source.read_bytes()) != freeze["audit_code_sha256"]:
        raise SystemExit("STOP_AUDIT_SOURCE_HASH")
    if digest(test_source.read_bytes()) != freeze["construction_test_sha256"]:
        raise SystemExit("STOP_TEST_SOURCE_HASH")

    result, hashes, provenance_errors, blob_details = load_evidence(args.repo.resolve(), freeze)
    if provenance_errors:
        verdict = {
            "disposition": "STOP_INPUT_PROVENANCE",
            "integrity": False,
            "errors": provenance_errors,
            "audit_not_run": True,
            "scientific_verdict": None,
            "available_raw_payload_verified": result is not None and "decompressed_raw" in hashes,
        }
    elif result is None:
        verdict = {
            "disposition": "STOP_INPUT_PROVENANCE",
            "integrity": False,
            "errors": ["raw_result_unavailable"],
            "audit_not_run": True,
            "scientific_verdict": None,
        }
    else:
        verdict = audit_result(result)
        scientific_verdict = verdict["disposition"]
        verdict["disposition"] = (
            "PASS_INDEPENDENT_AUDIT_SCOPED" if verdict["integrity"] else "FAIL_INDEPENDENT_AUDIT"
        )
        verdict["audit_not_run"] = False
        verdict["scientific_verdict"] = scientific_verdict
    verdict["input_sha256"] = hashes
    verdict["input_git_blobs"] = blob_details
    verdict["audit_runtime"] = {
        "python_torch": torch.__version__,
        "device": "cpu",
        "cuda_visible_devices": "hidden by invocation environment",
        "optimizer_steps": 0,
        "model_evaluations": 0,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(verdict, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")
    with output.open("xb") as stream:
        stream.write(payload)
    print(json.dumps(verdict, sort_keys=True, separators=(",", ":")))
    return 0 if verdict["integrity"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
