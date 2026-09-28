"""Post-review raw-only correction for the -04 break-even accumulator/report.

This supplemental audit never changes or replaces audit-04/audit.json and does
not rerun the consumed formal allocation. The frozen candidate-independent
oracle and mutation validator are reused from the byte-pinned original auditor;
the corrected cumulative-cost calculation below is implemented independently.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
sys.path.insert(0, str(ROOT))
from audit_raw import ALLOCATION, altered, oracle, validate  # noqa: E402


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def first_break_even(reload_ns: list[int], reuse_ns: list[int], initialization_ns: int) -> int:
    """First request where cumulative reuse lifetime cost is strictly lower."""
    if len(reload_ns) != len(reuse_ns):
        raise ValueError("paired_request_count_mismatch")
    reuse_total = initialization_ns
    reload_total = 0
    for index, (reload_cost, reuse_cost) in enumerate(zip(reload_ns, reuse_ns), 1):
        reuse_total += reuse_cost
        reload_total += reload_cost
        if reuse_total < reload_total:
            return index
    return len(reload_ns) + 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True, type=Path)
    parser.add_argument("--prior-audit", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    freeze_path = ROOT / "FREEZE.json"
    freeze_bytes = freeze_path.read_bytes()
    freeze = json.loads(freeze_bytes)
    raw_bytes = args.raw.read_bytes()
    raw = json.loads(raw_bytes)
    prior_audit = json.loads(args.prior_audit.read_bytes())
    expected_path = REPO / freeze["inputs"]["expected.json"]
    skill_path = REPO / freeze["inputs"]["skill.json"]
    expected = json.loads(expected_path.read_bytes())
    tensors = json.loads(skill_path.read_bytes())["tensors"]

    source_hashes = {name: sha(ROOT / name) for name in freeze["sources"]}
    reference_hashes = {
        name: sha(REPO / path) for name, path in freeze["reference_sources"].items()
    }
    input_hashes = {"skill.json": sha(skill_path), "expected.json": sha(expected_path)}
    freeze_sha = hashlib.sha256(freeze_bytes).hexdigest()
    raw_sha = hashlib.sha256(raw_bytes).hexdigest()

    errors: list[str] = []
    if raw.get("allocation") != ALLOCATION or raw.get("status") != "RUN_COMPLETE":
        errors.append("raw_identity_or_completion")
    if raw.get("freeze_sha256") != freeze_sha or prior_audit.get("freeze_sha256") != freeze_sha:
        errors.append("freeze_identity")
    if prior_audit.get("raw_sha256") != raw_sha:
        errors.append("prior_audit_raw_identity")
    if raw.get("source_hashes") != freeze["sources"] or source_hashes != freeze["sources"]:
        errors.append("source_identity")
    if raw.get("reference_hashes") != reference_hashes or reference_hashes != freeze["reference_sources_sha256"]:
        errors.append("reference_identity")
    if raw.get("input_hashes") != input_hashes or input_hashes != freeze["inputs_sha256"]:
        errors.append("input_identity")
    if raw.get("environment", {}).get("image_id") != freeze["container"]["image_id"]:
        errors.append("image_identity")

    blocks = raw.get("blocks", [])
    requests = raw.get("requests_per_arm_block")
    if (type(requests) is not int or requests != freeze["treatment"]["requests_per_arm_per_block"]
            or len(blocks) != freeze["treatment"]["blocks"]
            or len(blocks) != raw.get("blocks_expected")):
        errors.append("sample_shape")
        requests = 0

    schedule = raw.get("schedule", [])
    if len(schedule) != requests:
        errors.append("schedule_length")
    else:
        for row_index, item in enumerate(schedule):
            role = ("A", "B", "C")[row_index % 3]
            expected_index = (row_index * 37 + 11) % 4096
            expected_value = expected["roles"][role]["pred"][expected_index]
            if item != {"role": role, "index": expected_index, "expected": expected_value}:
                errors.append(f"schedule:{row_index}")
                break

    # Reconstruct every retained prediction with the oracle, without importing
    # or calling the candidate lifecycle implementation.
    reconciled = 0
    for block_index, block in enumerate(blocks):
        if block.get("index") != block_index:
            errors.append(f"block_index:{block_index}")
        expected_order = (["RELOAD_EACH_REQUEST", "LOAD_ONCE_REUSE"] if block_index % 2 == 0
                          else ["LOAD_ONCE_REUSE", "RELOAD_EACH_REQUEST"])
        if block.get("order") != expected_order:
            errors.append(f"block_order:{block_index}")
        for arm_name in ("RELOAD_EACH_REQUEST", "LOAD_ONCE_REUSE"):
            arm = block.get("arms", {}).get(arm_name, {})
            predictions = arm.get("predictions", [])
            if len(predictions) != requests:
                errors.append(f"prediction_count:{block_index}:{arm_name}")
                continue
            for row_index, predicted in enumerate(predictions):
                item = schedule[row_index]
                role = item["role"]
                actual = oracle(
                    tensors[role], role,
                    expected["roles"][role]["inputs"][item["index"]],
                )
                reconciled += 1
                if predicted != item["expected"] or predicted != actual:
                    errors.append(f"prediction:{block_index}:{arm_name}:{row_index}")
                    break

    block_break_even: list[int] = []
    block_ratios: list[float] = []
    wins = 0
    for block_index, block in enumerate(blocks):
        arms = block.get("arms", {})
        reload_arm = arms.get("RELOAD_EACH_REQUEST", {})
        reuse_arm = arms.get("LOAD_ONCE_REUSE", {})
        reload_ns = reload_arm.get("request_ns", [])
        reuse_ns = reuse_arm.get("request_ns", [])
        init_ns = reuse_arm.get("initialization_ns")
        if (len(reload_ns) != requests or len(reuse_ns) != requests
                or type(init_ns) is not int or init_ns <= 0
                or reload_arm.get("initialization_ns") != 0
                or any(type(value) is not int or value <= 0 for value in reload_ns + reuse_ns)):
            errors.append(f"timing_shape:{block_index}")
            continue
        reload_total = sum(reload_ns)
        reuse_total = init_ns + sum(reuse_ns)
        block_ratios.append(reuse_total / reload_total)
        wins += reuse_total < reload_total
        block_break_even.append(first_break_even(reload_ns, reuse_ns, init_ns))

    # Verify the originally frozen mutation suite still rejects every control.
    freeze = json.loads(freeze_bytes)
    oracle_errors = []
    for case in ("prediction", "truncate", "block", "allocation", "source", "schedule", "duration"):
        candidate = altered(raw, case)
        if not validate(candidate, expected, tensors, freeze, freeze_sha,
                        source_hashes, reference_hashes, input_hashes):
            oracle_errors.append(case)
    median_ratio = statistics.median(block_ratios) if block_ratios else None
    median_break_even = statistics.median(block_break_even) if block_break_even else None
    mutation_rejections = 7 - len(oracle_errors)
    passed = (
        not errors and not oracle_errors and reconciled == 2 * len(blocks) * requests
        and wins >= 12 and median_ratio is not None and median_ratio <= 0.90
        and median_break_even is not None and median_break_even <= requests
    )
    report = {
        "schema": "needle-role-skill-lifecycle-audit-correction-v1",
        "allocation": ALLOCATION,
        "status": "PASS_CORRECTED_RAW_REAUDIT_SCOPED" if passed else "STOP_CORRECTION_AUDIT",
        "not_a_formal_rerun": True,
        "errors": errors,
        "prior_audit_status_preserved": prior_audit.get("status"),
        "prior_audit_sha256": sha(args.prior_audit),
        "raw_sha256": raw_sha,
        "freeze_sha256": freeze_sha,
        "source_hashes": source_hashes,
        "reference_hashes": reference_hashes,
        "input_hashes": input_hashes,
        "blocks": len(blocks),
        "requests_per_arm_per_block": requests,
        "reconciled_predictions": reconciled,
        "block_first_break_even_request": block_break_even,
        "median_first_break_even_request": median_break_even,
        "block_lifetime_ratios": block_ratios,
        "median_reuse_to_reload_lifetime_ratio": median_ratio,
        "paired_blocks_won": wins,
        "mutation_controls_rejected": mutation_rejections,
        "mutation_controls_total": 7,
        "mutation_controls_not_rejected": oracle_errors,
        "scope": (
            f"single synthetic seed-3788 formal raw; {len(blocks)} paired blocks; "
            f"{requests} requests per arm per block; post-review audit correction only"
        ),
        "auditor_source_sha256": sha(Path(__file__)),
        "auditor_python": sys.version,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"CORRECTION_AUDIT_STATUS={report['status']} ROWS={reconciled} WINS={wins}/{len(blocks)} BREAK_EVEN={median_break_even} MUTATIONS={mutation_rejections}/7")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
