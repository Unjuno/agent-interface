import argparse
import hashlib
import json
from pathlib import Path

from candidates import candidates_from_state
from protocol import SCHEMA, expected_bound, make_rows, simulate_bound

SEED = 4792963
COUNT = 32


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    rows = make_rows(SEED, "heldout", COUNT)
    payload = {"schema": SCHEMA, "seed": SEED, "split": "heldout", "rows": []}
    for row in rows:
        # Candidate creation deliberately consumes only visible state. Gold labels
        # and oracle effects are attached only after the allowed set is fixed.
        candidates = candidates_from_state(row["state"])
        if candidates != sorted(set(candidates)) or not candidates:
            raise RuntimeError("candidate_set_not_canonical")
        row["expected_bound"] = expected_bound(row)
        row["expected_effect"] = simulate_bound(row["expected_bound"], row["state"])
        payload["rows"].append({"row": row, "candidates": candidates})
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False).encode("utf-8") + b"\n"
    path = Path(args.out)
    if path.exists():
        raise SystemExit("STOP_INPUT_OUTPUT_EXISTS")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded)
    print(json.dumps({"schema": payload["schema"], "seed": SEED, "rows": len(rows),
                      "bytes": len(encoded), "sha256": hashlib.sha256(encoded).hexdigest(),
                      "fit_count": 0, "optimizer_updates": 0}, sort_keys=True))


if __name__ == "__main__":
    main()


