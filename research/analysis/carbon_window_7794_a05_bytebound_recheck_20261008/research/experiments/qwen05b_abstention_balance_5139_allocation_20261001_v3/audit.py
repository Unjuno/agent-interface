"""Independent raw-only CPU audit using the pinned main reference oracle."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
SOURCE = PACKAGE.parent / "qwen05b_abstention_balance_5139_v1"
sys.path.insert(0, str(SOURCE))

from audit_reference import REFERENCE_CLASSES, reconstruct_dataset  # noqa: E402

ALLOCATION = "QWEN-SUPPORT-BALANCE-5139-20261001-03-CPU-CONSTRUCTION"
SEEDS = (914728361, 672904183, 385167429)


def audit(document: object, expected_seeds: tuple[int, int, int] = SEEDS) -> list[str]:
    errors: list[str] = []
    if not isinstance(document, dict):
        return ["document_not_object"]
    if document.get("allocation") != ALLOCATION:
        errors.append("allocation_identity")
    if document.get("schema") != "qwen-intent-envelope-v1-balanced-support-v2":
        errors.append("schema")
    if tuple(document.get(k) for k in ("formal_seed", "support_seed", "heldout_seed")) != expected_seeds:
        errors.append("seed_identity")
    if document.get("classes") != list(REFERENCE_CLASSES):
        errors.append("class_order")
    if document.get("split_contract") != (
        "support and heldout use disjoint pools, seeds, case ids, scopes, and task strings"
    ):
        errors.append("split_contract")
    errors.extend(reconstruct_dataset(document))
    return sorted(set(errors))


def corruption_controls(document: dict) -> dict[str, bool]:
    variants = {}

    item = copy.deepcopy(document)
    item["support_pool"].pop()
    variants["missing_support_row"] = item

    item = copy.deepcopy(document)
    item["supports"]["balanced"][0]["case_id"] = "forged-case"
    variants["forged_selected_support_id"] = item

    item = copy.deepcopy(document)
    item["heldout"][0]["task"] += " forged"
    variants["changed_heldout_row"] = item

    item = copy.deepcopy(document)
    item["support_seed"] += 1
    variants["changed_support_seed"] = item

    item = copy.deepcopy(document)
    item["allocation"] = "other-allocation"
    variants["forged_allocation_id"] = item

    return {name: bool(audit(variant)) for name, variant in variants.items()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    raw = Path(args.data).read_bytes()
    document = json.loads(raw)
    errors = audit(document)
    controls = corruption_controls(document) if isinstance(document, dict) else {}
    rejected = sum(controls.values())
    report = {
        "allocation": ALLOCATION,
        "data_bytes": len(raw),
        "data_sha256": hashlib.sha256(raw).hexdigest(),
        "decision": "PASS_DATASET_RECONSTRUCTION" if not errors else "STOP_AUDIT_MISMATCH",
        "errors": errors,
        "corruption_controls": controls,
        "corruption_controls_rejected": rejected,
        "corruption_controls_total": 5,
        "formal_fit_invocations": 0,
        "independent_reference": "research/experiments/qwen05b_abstention_balance_5139_v1/audit_reference.py",
        "model_loaded": False,
        "cuda_invocations": 0,
        "docker_invocations": 0,
    }
    output = Path(args.out)
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(report, sort_keys=True) + "\n")
    print(json.dumps(report, sort_keys=True))
    return 0 if not errors and rejected == 5 else 1


if __name__ == "__main__":
    raise SystemExit(main())
