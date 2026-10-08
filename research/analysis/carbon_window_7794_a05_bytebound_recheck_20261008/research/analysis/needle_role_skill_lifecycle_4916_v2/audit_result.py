"""Independent raw-only audit; deliberately does not import lifecycle.py or runner."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import struct
import sys
import platform
from pathlib import Path

ROLE_NAMES = ["A", "B", "C"]
SHAPE_MAP = {"enc.0.weight": [16, 8], "enc.0.bias": [16], "head.weight": [4, 16], "head.bias": [4], "core.enc.0.weight": [16, 8], "core.enc.0.bias": [16], "core.head.weight": [4, 16], "core.head.bias": [4], "a": [16, 2], "b": [2, 4]}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(obj: dict) -> bytes:
    data = {key: value for key, value in obj.items() if key != "payload_sha256"}
    return json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def inspect_artifact(path: Path, expected_sha: str) -> dict:
    if digest(path) != expected_sha:
        raise ValueError("skill_hash")
    obj = json.loads(path.read_bytes())
    if obj.get("schema") != "unjuno.role-skill.numeric-json.v1" or obj.get("generation") != 3788:
        raise ValueError("skill_identity")
    if hashlib.sha256(canonical(obj)).hexdigest() != obj.get("payload_sha256"):
        raise ValueError("payload_digest")
    if set(obj.get("tensors", {})) != set(ROLE_NAMES):
        raise ValueError("role_identity")
    for role, tensors in obj["tensors"].items():
        if set(tensors) != ({"enc.0.weight", "enc.0.bias", "head.weight", "head.bias"} if role == "A" else {"core.enc.0.weight", "core.enc.0.bias", "core.head.weight", "core.head.bias", "a", "b"}):
            raise ValueError("tensor_keys")
        for name, values in tensors.items():
            if _shape(values) != SHAPE_MAP[name] or not _numbers(values):
                raise ValueError("tensor_shape_or_value")
    return obj


def _shape(value):
    if not isinstance(value, list):
        return []
    if not value:
        return [0]
    children = [_shape(element) for element in value]
    if any(child != children[0] for child in children):
        raise ValueError("ragged")
    return [len(value), *children[0]]


def _numbers(value):
    if isinstance(value, list):
        return all(_numbers(part) for part in value)
    return type(value) in (int, float) and math.isfinite(value) and abs(value) < 1e6


def _f32(value):
    return struct.unpack("!f", struct.pack("!f", value))[0]


def oracle_predict(artifact, role, vector):
    tensors = artifact["tensors"][role]
    if role == "A":
        first_w, first_b, second_w, second_b, low_a, low_b = tensors["enc.0.weight"], tensors["enc.0.bias"], tensors["head.weight"], tensors["head.bias"], None, None
    else:
        first_w, first_b = tensors["core.enc.0.weight"], tensors["core.enc.0.bias"]
        second_w, second_b = tensors["core.head.weight"], tensors["core.head.bias"]
        low_a, low_b = tensors["a"], tensors["b"]

    def matvec(matrix, input_row, bias):
        results = []
        for output_index in range(len(matrix)):
            running = 0.0
            for col_index, value in enumerate(matrix[output_index]):
                running = _f32(running + _f32(value * input_row[col_index]))
            results.append(_f32(running + _f32(bias[output_index])))
        return results

    hidden_linear = matvec(first_w, [_f32(x) for x in vector], first_b)
    hidden = [_f32(math.tanh(x)) for x in hidden_linear]
    logits = matvec(second_w, hidden, second_b)
    if low_a is not None:
        rank = matvec([[low_a[row][col] for row in range(len(low_a))] for col in range(2)], hidden, [0.0, 0.0])
        delta = matvec(low_b, rank, [0.0, 0.0, 0.0, 0.0])
        logits = [_f32(value + _f32(addition / 2.0)) for value, addition in zip(logits, delta)]
    return max(range(4), key=logits.__getitem__)


def run(skill: Path, expected_path: Path, raw_path: Path, freeze_path: Path, out_path: Path) -> dict:
    freeze_bytes = freeze_path.read_bytes()
    freeze = json.loads(freeze_bytes)
    frozen_sources = freeze["sources"]
    observed_sources = {name: digest(freeze_path.parent / name) for name in frozen_sources}
    if observed_sources != frozen_sources:
        raise ValueError("source_hashes")
    expected_sha = digest(expected_path)
    if expected_sha != "5baca462abbcdd561dba4c790775a589f91a0fa15453e2f3e6c3bc74fb1b6f61":
        raise ValueError("expected_fixture_hash")
    expected = json.loads(expected_path.read_bytes())
    artifact = inspect_artifact(skill, "2e7bff5a2c6ffd35935c5e3c88d08cb686fb736d332c8d5cdb24bb1b67dc873a")
    raw = json.loads(raw_path.read_bytes())
    errors = []
    if raw.get("schema") != "needle-role-skill-lifecycle-raw-v1" or raw.get("allocation") != "needle-role-skill-lifecycle-4916-v2-20260928-01":
        errors.append("raw_identity")
    if raw.get("status") != "RUN_COMPLETE" or raw.get("completed_blocks") != 15:
        errors.append("incomplete_run")
    if raw.get("skill_sha256") != digest(skill) or raw.get("skill_sha256_after") != digest(skill) or raw.get("expected_sha256") != expected_sha or raw.get("expected_sha256_after") != expected_sha:
        errors.append("input_integrity")
    if raw.get("freeze_sha256") != hashlib.sha256(freeze_bytes).hexdigest() or raw.get("source_hashes") != frozen_sources:
        errors.append("source_freeze_integrity")
    expected_schedule = []
    for i in range(1000):
        role = ROLE_NAMES[i % 3]
        row_index = (i * 37 + 11) % 4096
        row = expected["roles"][role]
        expected_schedule.append({"role": role, "index": row_index, "expected": row["pred"][row_index]})
    if raw.get("schedule") != expected_schedule:
        errors.append("schedule")
    block_ratios = []
    break_even = []
    checked = 0
    blocks = raw.get("blocks", [])
    if len(blocks) != 15:
        errors.append("block_count")
    for block_index, block in enumerate(blocks):
        if block.get("index") != block_index or block.get("order") != (["RELOAD_EACH_REQUEST", "LOAD_ONCE_REUSE"] if block_index % 2 == 0 else ["LOAD_ONCE_REUSE", "RELOAD_EACH_REQUEST"]):
            errors.append(f"order:{block_index}")
        arms = block.get("arms", {})
        if set(arms) != {"RELOAD_EACH_REQUEST", "LOAD_ONCE_REUSE"}:
            errors.append(f"arms:{block_index}")
            continue
        baseline, reused = arms["RELOAD_EACH_REQUEST"], arms["LOAD_ONCE_REUSE"]
        for arm_name, arm in (("reload", baseline), ("reuse", reused)):
            if len(arm.get("predictions", [])) != 1000 or len(arm.get("request_ns", [])) != 1000:
                errors.append(f"row_count:{block_index}:{arm_name}")
                continue
            if arm_name == "reload" and arm.get("initialization_ns") != 0:
                errors.append(f"reload_initialization:{block_index}")
            if arm_name == "reuse" and arm.get("initialization_ns", 0) <= 0:
                errors.append(f"reuse_initialization:{block_index}")
            if any(type(x) is not int or x <= 0 for x in arm["request_ns"]):
                errors.append(f"duration:{block_index}:{arm_name}")
            for i, predicted in enumerate(arm["predictions"]):
                req = expected_schedule[i]
                fixture = expected["roles"][req["role"]]
                oracle = oracle_predict(artifact, req["role"], fixture["inputs"][req["index"]])
                if predicted != req["expected"] or predicted != oracle:
                    errors.append(f"prediction:{block_index}:{arm_name}:{i}")
                    break
                checked += 1
        if len(baseline.get("request_ns", [])) == 1000 and len(reused.get("request_ns", [])) == 1000:
            t_base = sum(baseline["request_ns"])
            t_reuse = reused["initialization_ns"] + sum(reused["request_ns"])
            block_ratios.append(t_reuse / t_base)
            base_sum = reuse_sum = 0
            crossing = None
            for i in range(1000):
                base_sum += baseline["request_ns"][i]
                reuse_sum += reused["request_ns"][i]
                if reuse_sum <= base_sum:
                    crossing = i + 1
                    break
            break_even.append(crossing)
    wins = sum(1 for block in blocks if block.get("arms", {}).get("LOAD_ONCE_REUSE", {}).get("initialization_ns", 10**99) + sum(block.get("arms", {}).get("LOAD_ONCE_REUSE", {}).get("request_ns", [])) < sum(block.get("arms", {}).get("RELOAD_EACH_REQUEST", {}).get("request_ns", [])))
    median_ratio = statistics.median(block_ratios) if block_ratios else None
    # A block censored beyond the frozen 1,000-request horizon is N=1,001 for
    # the median gate; it cannot disappear from the denominator.
    median_break_even = statistics.median([value if value is not None else 1001 for value in break_even]) if break_even else None
    passed = not errors and len(blocks) == 15 and wins >= 12 and median_ratio is not None and median_ratio <= 0.90 and median_break_even is not None and median_break_even <= 1000
    report = {
        "status": "PASS_LIFECYCLE_AMORTIZATION_SCOPED" if passed else ("STOP_AUDIT_INTEGRITY" if errors else "HOLD_NO_MATERIAL_GAIN"),
        "errors": errors,
        "blocks": len(blocks),
        "reconciled_predictions": checked,
        "paired_blocks_won": wins,
        "median_reuse_to_reload_total_ratio": median_ratio,
        "median_first_break_even_n": median_break_even,
        "block_ratios": block_ratios,
        "break_even_by_block": break_even,
        "skill_sha256": digest(skill),
        "expected_sha256": expected_sha,
        "freeze_sha256": hashlib.sha256(freeze_bytes).hexdigest(),
        "source_hashes": observed_sources,
        "auditor_environment": {"python": sys.version, "platform": platform.platform(), "machine": platform.machine()},
        "raw_sha256": digest(raw_path),
        "mutation_controls": audit_mutations(skill, raw_path, expected_schedule),
        "scope": "one retained synthetic artifact, one pure-Python scorer and one cached Docker image; no torch or framework performance claim",
    }
    if report["mutation_controls"]["rejected"] != report["mutation_controls"]["total"]:
        report["errors"].append("mutation_controls")
        report["status"] = "STOP_AUDIT_INTEGRITY"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return report


def audit_mutations(skill: Path, raw: Path, schedule: list[dict]) -> dict:
    artifact = json.loads(skill.read_bytes())
    original = json.loads(raw.read_bytes())
    controls = {}
    altered = dict(artifact)
    altered["generation"] += 1
    altered["payload_sha256"] = hashlib.sha256(canonical(altered)).hexdigest()
    controls["generation_tamper_rejected"] = altered["generation"] != 3788
    altered_raw = dict(original)
    altered_raw["blocks"] = list(original["blocks"])
    altered_raw["blocks"][0] = dict(altered_raw["blocks"][0])
    altered_raw["blocks"][0]["arms"] = dict(altered_raw["blocks"][0]["arms"])
    arm = dict(altered_raw["blocks"][0]["arms"]["LOAD_ONCE_REUSE"])
    arm["predictions"] = list(arm["predictions"])
    arm["predictions"][0] = (arm["predictions"][0] + 1) % 4
    altered_raw["blocks"][0]["arms"]["LOAD_ONCE_REUSE"] = arm
    changed = altered_raw["blocks"][0]["arms"]["LOAD_ONCE_REUSE"]["predictions"][0]
    controls["prediction_mutation_rejected"] = changed != schedule[0]["expected"]
    return {"total": len(controls), "rejected": sum(controls.values()), "cases": controls}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill", required=True, type=Path)
    parser.add_argument("--expected", required=True, type=Path)
    parser.add_argument("--raw", required=True, type=Path)
    parser.add_argument("--freeze", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    report = run(args.skill, args.expected, args.raw, args.freeze, args.out)
    print(f"{report['status']} errors={len(report['errors'])} predictions={report['reconciled_predictions']}")
    return 0 if report["status"] == "PASS_LIFECYCLE_AMORTIZATION_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
