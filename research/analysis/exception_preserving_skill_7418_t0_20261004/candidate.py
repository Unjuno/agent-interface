#!/usr/bin/env python3
"""Finite proposal-only episode consolidation candidate for Issue #7418."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def build_memories(fixture):
    episodes = fixture["episodes"]
    ids = sorted(row["id"] for row in episodes)
    vocabulary = fixture["predicate_vocabulary"]
    buckets = {}
    for row in episodes:
        signature = tuple((key, row["context"].get(key)) for key in vocabulary)
        buckets.setdefault(signature, []).append(row)

    rules = []
    for index, (signature, rows) in enumerate(sorted(buckets.items()), 1):
        outcomes = {row["outcome"] for row in rows}
        decision = next(iter(outcomes)) if len(outcomes) == 1 else "UNKNOWN"
        conditions = {key: value for key, value in signature}
        if decision == "SAFE":
            proposal = "ACCEPT"
            kind = "DERIVED_FROM_OBSERVED"
        elif decision == "FORBIDDEN":
            proposal = "REJECT"
            kind = "OBSERVED_EXCEPTION"
        else:
            proposal = "UNKNOWN"
            kind = "CONFLICTING_OBSERVATIONS"
        rules.append({
            "id": f"rule-{index}", "conditions": conditions,
            "decision": proposal,
            "source_episode_ids": sorted(row["id"] for row in rows),
            "provenance_kind": kind,
        })

    votes = {label: sum(row["outcome"] == label for row in episodes)
             for label in ("SAFE", "FORBIDDEN")}
    majority = "ACCEPT" if votes["SAFE"] >= votes["FORBIDDEN"] else "REJECT"
    all_sources = sorted(ids)
    return {
        "episode_retrieval": {
            "records": [{"id": row["id"], "context": row["context"],
                         "outcome": row["outcome"],
                         "source_episode_ids": [row["id"]],
                         "provenance_kind": "OBSERVED"}
                        for row in episodes],
        },
        "unqualified_consolidation": {
            "records": [{"id": "majority-skill", "conditions": {},
                         "decision": majority, "source_episode_ids": all_sources,
                         "provenance_kind": "INFERENCE"}],
        },
        "exception_preserving": {"records": rules},
    }


def decide(representation, query):
    context = query["context"]
    records = representation["records"]
    if representation is None:
        return {"decision": "UNKNOWN", "source_episode_ids": [], "matched_record_ids": []}

    if query.get("representation") == "episode_retrieval":
        matches = [row for row in records if row["context"] == context]
        outcomes = {row["outcome"] for row in matches}
        if not matches or len(outcomes) != 1:
            decision = "UNKNOWN"
        else:
            decision = {"SAFE": "ACCEPT", "FORBIDDEN": "REJECT"}.get(next(iter(outcomes)), "UNKNOWN")
        return {"decision": decision,
                "source_episode_ids": sorted({src for row in matches for src in row["source_episode_ids"]}),
                "matched_record_ids": sorted(row["id"] for row in matches)}

    if query.get("representation") == "unqualified_consolidation":
        row = records[0]
        return {"decision": row["decision"],
                "source_episode_ids": row["source_episode_ids"],
                "matched_record_ids": [row["id"]]}

    matches = [row for row in records
               if all(context.get(key) == value for key, value in row["conditions"].items())]
    if len(matches) != 1:
        return {"decision": "UNKNOWN", "source_episode_ids": [], "matched_record_ids": []}
    row = matches[0]
    return {"decision": row["decision"],
            "source_episode_ids": row["source_episode_ids"],
            "matched_record_ids": [row["id"]]}


def pipeline(fixture):
    memories = build_memories(fixture)
    reps = {}
    for name, value in memories.items():
        blob = canonical(value).encode("utf-8")
        reps[name] = {**value, "stored_records": len(value["records"]),
                      "serialized_bytes": len(blob)}

    rows = []
    for name, representation in reps.items():
        for query in fixture["queries"]:
            q = {**query, "representation": name}
            result = decide(representation, q)
            rows.append({"representation": name, "query_id": query["id"],
                         **result})
    return {"schema": "unjuno.issue7418.t0.candidate.v1",
            "representations": reps, "rows": rows,
            "fixture_sha256": hashlib.sha256((HERE / "fixture.json").read_bytes()).hexdigest(),
            "candidate_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    fixture = json.loads((HERE / "fixture.json").read_text(encoding="utf-8"))
    raw = pipeline(fixture)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(raw, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
    print(json.dumps({"rows": len(raw["rows"]),
                      "representations": list(raw["representations"])}))


if __name__ == "__main__":
    main()
