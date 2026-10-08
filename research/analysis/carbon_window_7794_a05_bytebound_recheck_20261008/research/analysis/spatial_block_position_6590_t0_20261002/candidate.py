from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path


def _rank(seed: str, value: str) -> str:
    return hashlib.sha256((seed + "\0" + value).encode("utf-8")).hexdigest()


def generate(fixture: dict) -> dict:
    grid = fixture["grid"]
    width, height = grid["width"], grid["height"]
    block_w, block_h = grid["block_width"], grid["block_height"]
    count = fixture["rows_per_center_and_label"]
    split_n = fixture["random_holdout_rows_per_center_and_label"]
    rows: list[dict] = []

    for field in fixture["fields"]:
        field_id = field["field_id"]
        for y in range(height):
            for x in range(width):
                block_id = f"b{y // block_h}{x // block_w}"
                for label in ("positive", "negative"):
                    group = []
                    for replicate in range(count):
                        row_id = f"{field_id}/x{x:02d}-y{y:02d}/{label}/r{replicate:02d}"
                        group.append({
                            "row_id": row_id,
                            "field_id": field_id,
                            "x": x,
                            "y": y,
                            "block_id": block_id,
                            "label": label,
                            "replicate": replicate,
                            "renderer_variant": fixture["fixed_renderer_variant"],
                            "source_id": "source-" + row_id,
                            "noise_id": "noise-" + row_id,
                        })

                    if label == "positive":
                        accepted_n = field["positive_accepts_per_center"]
                        if block_id == field.get("planted_hotspot_block"):
                            accepted_n = field["hotspot_positive_accepts_per_center"]
                    else:
                        accepted_n = field["negative_false_accepts_per_center"]

                    accepted = {
                        row["row_id"]
                        for row in sorted(
                            group,
                            key=lambda row: _rank(
                                fixture["hash_seeds"]["outcome"], row["row_id"]
                            ),
                        )[:accepted_n]
                    }
                    random_test = {
                        row["row_id"]
                        for row in sorted(
                            group,
                            key=lambda row: _rank(
                                fixture["hash_seeds"]["random_split"], row["row_id"]
                            ),
                        )[:split_n]
                    }
                    for row in group:
                        if label == "positive":
                            row["status"] = "ACCEPT" if row["row_id"] in accepted else "YIELD"
                        else:
                            row["status"] = "ACCEPT" if row["row_id"] in accepted else "REJECT"
                        row["random_partition"] = (
                            "random_test" if row["row_id"] in random_test else "random_train"
                        )
                        rows.append(row)

    rows.sort(key=lambda row: row["row_id"])
    return {"schema": "spatial-block-position-6590-t0-raw-v1", "rows": rows}


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the frozen finite T0 field.")
    parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
    raw = generate(fixture)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"schema": raw["schema"], "rows": len(raw["rows"]), "status": "CANDIDATE_COMPLETE"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
