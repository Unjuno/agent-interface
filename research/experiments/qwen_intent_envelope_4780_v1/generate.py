import argparse
import json
from pathlib import Path

from protocol import SCHEMA, make_rows, expected_bound, simulate_bound


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    support_seed = args.seed ^ 0xA5A5A5A5
    document = {"schema": SCHEMA, "seed": args.seed, "support_seed": support_seed,
                "support": make_rows(support_seed, "support", 32),
                "heldout": make_rows(args.seed, "heldout", 64)}
    for row in document["support"] + document["heldout"]:
        row["expected_bound"] = expected_bound(row)
        row["expected_effect"] = simulate_bound(row["expected_bound"], row["state"])
    Path(args.out).write_text(json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
