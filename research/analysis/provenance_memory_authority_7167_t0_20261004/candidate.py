#!/usr/bin/env python3
"""Finite provenance-carrying object-memory pipeline for Issue #7167."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TRUSTED = "USER_INSTRUCTION"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def pipeline(fixture):
    stored = []
    for row in fixture["records"]:
        known = bool(row.get("source")) and row["origin"] != "UNKNOWN"
        stored.append({**row, "source_refs": [row["source"]] if known else [],
                       "source_status": "BOUND" if known else "UNKNOWN",
                       "kind": "ATOM", "authority_class": row["origin"]})

    groups = {}
    for row in stored:
        if row["origin"] == "APPLICATION_CONTENT":
            groups.setdefault(row["text"], []).append(row)
    summaries = []
    for index, (text, rows) in enumerate(sorted(groups.items()), 1):
        summaries.append({"id": f"summary{index}", "text": text,
                          "origin": "DERIVED_SUMMARY", "source": None,
                          "revision": None, "key": None,
                          "source_refs": sorted({ref for row in rows for ref in row["source_refs"]}),
                          "source_status": "BOUND" if all(row["source_status"] == "BOUND" for row in rows) else "UNKNOWN",
                          "kind": "SUMMARY", "authority_class": "DESCRIPTIVE_ONLY",
                          "members": sorted(row["id"] for row in rows)})

    latest = {}
    for row in stored:
        if row["origin"] == TRUSTED and row["source_status"] == "BOUND" and row["key"]:
            previous = latest.get(row["key"])
            if previous is None or row["revision"] > previous["revision"]:
                latest[row["key"]] = row
    query_words = set(fixture["retrieval_query"].lower().split())
    retrieved = []
    for row in stored + summaries:
        if query_words.intersection(row["text"].lower().split()):
            retrieved.append({"id": row["id"], "text": row["text"], "origin": row["origin"],
                              "source_refs": row["source_refs"], "source_status": row["source_status"],
                              "authority_class": row["authority_class"], "kind": row["kind"]})
    intents = [{"id": row["id"], "text": row["text"], "key": row["key"],
                "revision": row["revision"], "source_refs": row["source_refs"]}
               for row in sorted(latest.values(), key=lambda item: item["key"])
               if query_words.intersection(row["text"].lower().split())]
    return {"schema": "unjuno.issue7167.t0.candidate.v1", "stored": stored,
            "summaries": summaries, "retrieved": retrieved,
            "authorized_intents": intents,
            "unknown_source_authority_count": sum(
                1 for row in stored if row["source_status"] == "UNKNOWN" and row["authority_class"] == TRUSTED)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    fixture = json.loads((HERE / "fixture.json").read_text(encoding="utf-8"))
    raw = pipeline(fixture)
    raw["fixture_sha256"] = hashlib.sha256((HERE / "fixture.json").read_bytes()).hexdigest()
    raw["candidate_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"schema": raw["schema"], "stored": len(raw["stored"]),
                      "summaries": len(raw["summaries"]), "retrieved": len(raw["retrieved"]),
                      "authorized_intents": len(raw["authorized_intents"])}))


if __name__ == "__main__":
    main()
