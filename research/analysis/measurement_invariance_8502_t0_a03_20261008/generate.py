"""Generate the fixed-seed synthetic A03 fixtures; no external dependencies."""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any


def generate(config: dict[str, Any]) -> dict[str, Any]:
    fixtures = []
    for fixture_id, seed in config["seeds"].items():
        groups = {}
        for group_index, group in enumerate(("A", "B")):
            rng = random.Random(seed + group_index * 100_000)
            n = config["sample_sizes_per_group"][fixture_id]
            rows = []
            for _ in range(n):
                common = rng.gauss(0.0, 1.0)
                factors = (rng.gauss(0.0, 1.0), rng.gauss(0.0, 1.0))
                response = []
                for item in range(config["item_count"]):
                    loading = config["common_loading"]
                    latent = common
                    if fixture_id == "F03" and group == "B" and item == 2:
                        loading = config["altered_loading"]
                    if fixture_id == "F04" and group == "B":
                        latent = factors[item // 3]
                    residual = rng.gauss(0.0, (1.0 - loading * loading) ** 0.5)
                    value = loading * latent + residual
                    cuts = list(config["cutpoints"])
                    if fixture_id == "F02" and group == "B" and item == 2:
                        cuts = [cut + config["threshold_shift"] for cut in cuts]
                    response.append(sum(value > cut for cut in cuts))
                rows.append(response)
            groups[group] = rows
        fixtures.append({"fixture_id": fixture_id, "seed": seed, "groups": groups})
    return {"schema": "issue8502-t0-a03-fixtures-v1", "item_count": config["item_count"], "fixtures": fixtures}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=".")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    out = Path(args.out_dir).resolve()
    config = json.loads((root / "config.json").read_text(encoding="utf-8"))
    truth = {"schema": "issue8502-t0-a03-truth-v1", "cases": config["expected"]}
    for name, payload in (("fixtures.json", generate(config)), ("truth.json", truth)):
        data = (json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode()
        with (out / name).open("xb") as stream:
            stream.write(data)
    print(json.dumps({"fixtures": len(config["seeds"]), "created": ["fixtures.json", "truth.json"]}, sort_keys=True))


if __name__ == "__main__":
    main()
