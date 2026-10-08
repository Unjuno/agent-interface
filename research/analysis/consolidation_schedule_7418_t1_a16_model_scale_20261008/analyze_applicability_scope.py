"""Read-only, model-free diagnostic of applicability scope in A16 artifacts."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


def load_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, default=Path(__file__).parent)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    package = args.package
    ledger = json.loads((package / "episode_ledger.json").read_text())["episodes"]
    raw_path = package / "results/FORMAL_T1_A16/raw.jsonl"
    rows = load_jsonl(raw_path)
    raw_sha256 = hashlib.sha256(raw_path.read_bytes()).hexdigest()
    expected_raw_sha256 = "5d88e0a1cdfe05a99c5e2e42189fc47be611d7abf237e52fb5e556e3069881dd"
    if raw_sha256 != expected_raw_sha256:
        raise SystemExit(f"raw SHA-256 mismatch: {raw_sha256} != {expected_raw_sha256}")
    by_query = {(r["seed"], r["arm"], r["prefix"], r["query_id"]): r
                for r in rows if r.get("type") == "query"}
    common = next(q for q in json.loads((package / "queries.json").read_text())["queries"]
                  if q["id"] == "q_common_save")

    context_by_episode = {episode["id"]: episode.get("context")
                          for episode in ledger if episode.get("context")}
    mappings = {
        "common_success": ["kind", "key", "value", "source_ids"],
        "rare_exception": ["kind", "key", "value", "source_ids"],
    }
    scope_complete = True
    for row in rows:
        if row.get("type") != "consolidation":
            continue
        try:
            claims = json.loads(row["response"]["response"]).get("claims", [])
        except (KeyError, TypeError, ValueError):
            claims = []
        for claim in claims:
            if claim.get("id") in context_by_episode and "context" not in claim:
                scope_complete = False

    outcomes = Counter()
    scoped_prefix_classes = Counter()
    examples = {}
    for seed in (5601, 5602, 5603):
        for arm in ("episodic_only", "per_episode", "batch_2", "terminal"):
            for prefix in (1, 2, 3, 4, 5, 6):
                row = by_query[(seed, arm, prefix, "q_common_save")]
                response = json.loads(row["response"]["response"])
                expected = common["expected_by_prefix"][str(prefix)]
                correct = (response.get("classification") == expected["classification"]
                           and response.get("answer") == expected["answer"]
                           and sorted(response.get("source_ids", [])) == sorted(expected["source_ids"]))
                outcomes[(arm, "correct" if correct else "incorrect")] += 1
                if prefix >= 3:
                    scoped_prefix_classes[(arm, response.get("classification", "INVALID"))] += 1
                selected_examples = {("per_episode", 1), ("per_episode", 3),
                                     ("batch_2", 4), ("terminal", 6)}
                if (arm, prefix) in selected_examples and (arm, prefix) not in examples:
                    evidence = row.get("evidence", {}).get("claims", [])
                    examples[(arm, prefix)] = {
                        "seed": seed,
                        "oracle": expected,
                        "response": response,
                        "visible_claims": [
                            {field: claim[field] for field in ("id", "kind", "key", "value", "source_ids")
                             if field in claim}
                            for claim in evidence
                        ],
                    }

    result = {
        "diagnostic": "A16 applicability-scope gap",
        "raw_sha256_expected": expected_raw_sha256,
        "raw_sha256_actual": raw_sha256,
        "contextual_episodes": context_by_episode,
        "consolidation_mapping_fields": mappings,
        "context_present_on_contextual_claims": scope_complete,
        "query_family": "q_common_save",
        "correct_by_arm": {arm: outcomes[(arm, "correct")] for arm in
                            ("episodic_only", "per_episode", "batch_2", "terminal")},
        "total_per_arm": 18,
        "q_common_save_classification_prefixes_3_to_6": {
            arm: {label: scoped_prefix_classes[(arm, label)] for label in
                  ("SUPPORTED", "FORBIDDEN", "CONFLICT", "UNKNOWN", "INVALID")}
            for arm in ("episodic_only", "per_episode", "batch_2", "terminal")
        },
        "examples": {f"{arm}/prefix-{prefix}": example
                     for (arm, prefix), example in sorted(examples.items())},
        "interpretation": (
            "The frozen mapping and auditor check effect/value/source provenance, but do not "
            "preserve or validate app/mode/surface applicability. The query oracle uses the "
            "ledger's contextual labels while consolidated arms receive context-free claims. "
            "This is a limitation of A16's faithfulness and answerability measurement; it does "
            "not alter the frozen PASS_METHOD outcome or establish real GUI behavior."
        ),
    }
    text = json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(text)
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
