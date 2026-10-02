import argparse
import hashlib
import json
from pathlib import Path

from candidates import candidates_from_state
from protocol import SCHEMA, expected_bound, make_rows, simulate_bound

SEED = 4792962
COUNT = 32


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    rows = make_rows(SEED, "heldout", COUNT)
    payload = {"schema": SCHEMA, "seed": SEED, "split": "heldout", "rows": []}
    for row in rows:
        row["expected_bound"] = expected_bound(row)
        row["expected_effect"] = simulate_bound(row["expected_bound"], row["state"])
        payload["rows"].append({"row": row, "candidates": candidates_from_state(row["state"])})
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8") + b"\n"
    path.write_bytes(data)
    print(json.dumps({"schema": payload["schema"], "seed": SEED, "rows": len(rows),
                      "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                      "optimizer_updates": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
