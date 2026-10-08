"""Score retained proposals in a separate process using the sealed target key."""

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

ALLOCATION = "5749-ACTION-ONLY-LABEL-BLIND-A02-20261007"


def score(raw, key):
    if raw.get("schema") != "5749-a02-policy-output-v1" or raw.get("allocation") != ALLOCATION:
        raise ValueError("candidate_output_identity")
    if key.get("schema") != "5749-a02-scoring-key-v1":
        raise ValueError("scoring_key_identity")
    targets = {(x["episode_id"], x["tick"]): x["target"] for x in key["targets"]}
    expected_ids = {(r["episode_id"], r["tick"]) for r in raw["rows"]}
    if len(targets) != len(key["targets"]) or set(targets) != expected_ids:
        raise ValueError("scoring_key_roster")
    scored = []
    summary = defaultdict(lambda: {"proposals": 0, "correct": 0, "wrong": 0, "yields": 0, "queries": 0})
    for row in raw["rows"]:
        target = targets[(row["episode_id"], row["tick"])]
        choice = row["proposal"]
        outcome = "YIELD" if choice is None else "MATCH" if choice == target else "MISMATCH"
        scored.append({"episode_id": row["episode_id"], "tick": row["tick"],
                       "policy": row["policy"], "target": target,
                       "proposal": choice, "outcome": outcome})
        counts = summary[row["policy"]]
        counts["queries"] += row["query_count"]
        if choice is None:
            counts["yields"] += 1
        else:
            counts["proposals"] += 1
            counts["correct" if outcome == "MATCH" else "wrong"] += 1
    return {"schema": "5749-a02-score-v1", "allocation": ALLOCATION,
            "rows": scored, "summary": dict(summary)}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("raw_output")
    parser.add_argument("scoring_key")
    parser.add_argument("score_output")
    parser.add_argument("--freeze", default=str(Path(__file__).with_name("FREEZE.json")))
    args = parser.parse_args(argv)
    try:
        freeze = json.loads(Path(args.freeze).read_text())
        key_bytes = Path(args.scoring_key).read_bytes()
        if hashlib.sha256(key_bytes).hexdigest() != freeze["scoring_key_sha256"]:
            raise ValueError("scoring_key_hash_mismatch")
        result = score(json.loads(Path(args.raw_output).read_text()), json.loads(key_bytes))
        Path(args.score_output).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
