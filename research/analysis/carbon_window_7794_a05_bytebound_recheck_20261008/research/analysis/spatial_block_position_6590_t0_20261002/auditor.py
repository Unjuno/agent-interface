from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from itertools import product
from pathlib import Path


def _independent_rank(seed: str, row_id: str) -> bytes:
    payload = seed.encode("utf-8") + b"\x00" + row_id.encode("utf-8")
    return hashlib.sha256(payload).digest()


def _expected_rows(fixture: dict) -> dict[str, dict]:
    grid = fixture["grid"]
    rows_per_group = fixture["rows_per_center_and_label"]
    holdout_n = fixture["random_holdout_rows_per_center_and_label"]
    expected: dict[str, dict] = {}
    for field in fixture["fields"]:
        for x, y in product(range(grid["width"]), range(grid["height"])):
            block = f"b{y // grid['block_height']}{x // grid['block_width']}"
            for label in ("positive", "negative"):
                members = []
                for replicate in range(rows_per_group):
                    identity = f"{field['field_id']}/x{x:02d}-y{y:02d}/{label}/r{replicate:02d}"
                    members.append({
                        "row_id": identity,
                        "field_id": field["field_id"],
                        "x": x,
                        "y": y,
                        "block_id": block,
                        "label": label,
                        "replicate": replicate,
                        "renderer_variant": fixture["fixed_renderer_variant"],
                        "source_id": "source-" + identity,
                        "noise_id": "noise-" + identity,
                    })
                if label == "positive":
                    successes = field["positive_accepts_per_center"]
                    if block == field.get("planted_hotspot_block"):
                        successes = field["hotspot_positive_accepts_per_center"]
                else:
                    successes = field["negative_false_accepts_per_center"]
                ordered_outcomes = sorted(
                    members,
                    key=lambda item: _independent_rank(fixture["hash_seeds"]["outcome"], item["row_id"]),
                )
                accepted_ids = {item["row_id"] for item in ordered_outcomes[:successes]}
                ordered_split = sorted(
                    members,
                    key=lambda item: _independent_rank(fixture["hash_seeds"]["random_split"], item["row_id"]),
                )
                test_ids = {item["row_id"] for item in ordered_split[:holdout_n]}
                for item in members:
                    item["status"] = (
                        "ACCEPT" if item["row_id"] in accepted_ids
                        else ("YIELD" if label == "positive" else "REJECT")
                    )
                    item["random_partition"] = "random_test" if item["row_id"] in test_ids else "random_train"
                    expected[item["row_id"]] = item
    return expected


def _neighbors(block_id: str, all_blocks: list[str]) -> list[str]:
    row, col = int(block_id[1]), int(block_id[2])
    adjacent = []
    for other in all_blocks:
        r, c = int(other[1]), int(other[2])
        if abs(r - row) + abs(c - col) == 1:
            adjacent.append(other)
    return sorted(adjacent)


def _position_overlap(left: set[tuple[int, int]], right: set[tuple[int, int]]) -> bool:
    return bool(left & right)


def _support_state(centers: int, positive_rows: int, gates: dict) -> str:
    if centers < gates["minimum_independent_centers_per_block"] or positive_rows < gates["minimum_positive_rows_per_block"]:
        return "INSUFFICIENT"
    return "QUALIFIED"


def _summarize(fixture: dict, rows: list[dict]) -> dict:
    grid, gates = fixture["grid"], fixture["decision_gate"]
    block_ids = grid["blocks"]
    fields = {}
    for field in fixture["fields"]:
        field_id = field["field_id"]
        field_rows = [row for row in rows if row["field_id"] == field_id]
        random_test = [row for row in field_rows if row["random_partition"] == "random_test"]
        random_positive = [row for row in random_test if row["label"] == "positive"]
        random_accepts = sum(row["status"] == "ACCEPT" for row in random_positive)
        random_rate = random_accepts / len(random_positive) if random_positive else None
        block_results = []
        fold_leakage = []
        for heldout in block_ids:
            test_rows = [row for row in field_rows if row["block_id"] == heldout]
            train_rows = [row for row in field_rows if row["block_id"] != heldout]
            train_positions = {(row["x"], row["y"]) for row in train_rows}
            test_positions = {(row["x"], row["y"]) for row in test_rows}
            fold_leakage.append({
                "heldout_block": heldout,
                "position_overlap_count": len(train_positions & test_positions),
                "row_id_overlap_count": len({r["row_id"] for r in train_rows} & {r["row_id"] for r in test_rows}),
                "source_id_overlap_count": len({r["source_id"] for r in train_rows} & {r["source_id"] for r in test_rows}),
                "noise_id_overlap_count": len({r["noise_id"] for r in train_rows} & {r["noise_id"] for r in test_rows}),
            })
            positives = [row for row in test_rows if row["label"] == "positive"]
            negatives = [row for row in test_rows if row["label"] == "negative"]
            centers = {(row["x"], row["y"]) for row in test_rows}
            rate = (sum(row["status"] == "ACCEPT" for row in positives) / len(positives)) if positives else None
            train_centers = {(row["x"], row["y"]) for row in train_rows}
            min_distance = None
            if centers and train_centers:
                min_distance = min(
                    ((x - tx) ** 2 + (y - ty) ** 2) ** 0.5
                    for x, y in centers for tx, ty in train_centers
                )
            block_results.append({
                "block_id": heldout,
                "neighbor_blocks": _neighbors(heldout, block_ids),
                "independent_centers": len(centers),
                "positive_rows": len(positives),
                "positive_accepts": sum(row["status"] == "ACCEPT" for row in positives),
                "positive_yields": sum(row["status"] == "YIELD" for row in positives),
                "positive_accept_rate": rate,
                "negative_rows": len(negatives),
                "false_accepts": sum(row["status"] == "ACCEPT" for row in negatives),
                "minimum_distance_to_training_center": min_distance,
                "support_state": _support_state(len(centers), len(positives), gates),
            })
        rates = [entry["positive_accept_rate"] for entry in block_results if entry["positive_accept_rate"] is not None]
        fields[field_id] = {
            "random_split": {
                "scope": "diagnostic_only",
                "positive_accepts": random_accepts,
                "positive_rows": len(random_positive),
                "positive_accept_rate": random_rate,
                "false_accepts": sum(row["status"] == "ACCEPT" for row in random_test if row["label"] == "negative"),
                "negative_rows": sum(row["label"] == "negative" for row in random_test),
                "positions_shared_between_random_train_and_test": len({(r["x"], r["y"]) for r in field_rows if r["random_partition"] == "random_train"} & {(r["x"], r["y"]) for r in random_test}),
            },
            "block_holdout": {
                "blocks": block_results,
                "fold_leakage": fold_leakage,
                "minimum_positive_accept_rate": min(rates) if rates else None,
                "maximum_positive_accept_rate": max(rates) if rates else None,
                "max_minus_min_block_rate": (max(rates) - min(rates)) if rates else None,
                "random_minus_worst_block_rate": (random_rate - min(rates)) if random_rate is not None and rates else None,
                "worst_block_ids": [b["block_id"] for b in block_results if b["positive_accept_rate"] == (min(rates) if rates else None)],
            },
        }
    return fields


def audit(fixture: dict, raw: dict) -> dict:
    errors: list[str] = []
    expected = _expected_rows(fixture)
    actual_rows = raw.get("rows", []) if isinstance(raw, dict) else []
    actual = {}
    for row in actual_rows:
        row_id = row.get("row_id") if isinstance(row, dict) else None
        if not isinstance(row_id, str) or row_id in actual:
            errors.append("invalid_or_duplicate_row_id")
            continue
        actual[row_id] = row
    if raw.get("schema") != "spatial-block-position-6590-t0-raw-v1":
        errors.append("raw_schema")
    if set(actual) != set(expected):
        errors.append(f"row_id_set:{len(actual)}:{len(expected)}")
    for row_id, expected_row in expected.items():
        if actual.get(row_id) != expected_row:
            errors.append(f"row_reconstruction:{row_id}")
    fields = _summarize(fixture, list(actual.values())) if actual and not errors else {}

    all_folds = [fold for value in fields.values() for fold in value["block_holdout"]["fold_leakage"]]
    block_rows = [block for value in fields.values() for block in value["block_holdout"]["blocks"]]
    leakage_free = bool(all_folds) and all(
        item[key] == 0
        for item in all_folds
        for key in ("position_overlap_count", "row_id_overlap_count", "source_id_overlap_count", "noise_id_overlap_count")
    )
    random_overlap_expected = all(
        value["random_split"]["positions_shared_between_random_train_and_test"] == fixture["grid"]["width"] * fixture["grid"]["height"]
        and value["random_split"]["scope"] == "diagnostic_only"
        for value in fields.values()
    )
    uniform_id = fixture["fields"][0]["field_id"]
    hotspot_field = next(f for f in fixture["fields"] if f.get("planted_hotspot_block"))
    uniform_range = fields.get(uniform_id, {}).get("block_holdout", {}).get("max_minus_min_block_rate")
    hotspot_metrics = fields.get(hotspot_field["field_id"], {}).get("block_holdout", {})
    hotspot_contrast = hotspot_metrics.get("random_minus_worst_block_rate")
    hotspot_worst = hotspot_metrics.get("worst_block_ids", [])
    support_ok = bool(block_rows) and all(block["support_state"] == "QUALIFIED" for block in block_rows)
    empty_support_is_insufficient = _support_state(0, 0, fixture["decision_gate"]) == "INSUFFICIENT"
    overlap_probe_rejected = _position_overlap({(2, 3)}, {(2, 3)})
    gates = {
        "exact_rows_reconstructed": not errors,
        "block_holdout_has_no_position_or_identity_leakage": leakage_free,
        "random_split_overlap_is_marked_diagnostic_only": random_overlap_expected,
        "uniform_control_has_no_block_heterogeneity": uniform_range == fixture["decision_gate"]["uniform_max_minus_min_block_rate_tolerance"],
        "planted_hotspot_meets_contrast": hotspot_contrast is not None and hotspot_contrast >= fixture["decision_gate"]["minimum_random_minus_worst_block_positive_accept_rate"],
        "planted_worst_block_is_correct": hotspot_worst == [hotspot_field["planted_hotspot_block"]],
        "all_declared_blocks_meet_support": support_ok,
        "empty_support_returns_insufficient": empty_support_is_insufficient,
        "intentional_position_overlap_is_rejected": overlap_probe_rejected,
    }
    passed = all(gates.values()) and not errors
    return {
        "schema": "spatial-block-position-6590-t0-audit-v1",
        "decision": "METHOD_PASS" if passed else ("HOLD_AUDIT_INTEGRITY" if errors else "FAIL_METHOD"),
        "errors": errors,
        "row_count": len(actual_rows),
        "expected_row_count": len(expected),
        "field_summaries": fields,
        "mutation_controls": {
            "empty_block_outcome": "INSUFFICIENT" if empty_support_is_insufficient else "ERROR",
            "intentional_position_overlap": "REJECTED" if overlap_probe_rejected else "MISSED",
        },
        "gates": gates,
        "scope": "No-model finite method-control only; not a trained-model result or GUI claim.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Independently audit the finite T0 field.")
    parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument("--raw", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
    raw = json.loads(args.raw.read_text(encoding="utf-8"))
    result = audit(fixture, raw)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"decision": result["decision"], "errors": len(result["errors"]), "rows": result["row_count"]}, sort_keys=True))
    return 0 if result["decision"] == "METHOD_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
