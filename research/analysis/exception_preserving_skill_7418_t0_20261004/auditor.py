#!/usr/bin/env python3
"""Independent contract auditor for Issue #7418; intentionally imports no candidate code."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def independent_reconstruction(fixture):
    episodes = fixture["episodes"]
    vocab = fixture["predicate_vocabulary"]
    groups = {}
    for episode in episodes:
        key = tuple((field, episode["context"].get(field)) for field in vocab)
        groups.setdefault(key, []).append(episode)
    rules = []
    for n, (key, rows) in enumerate(sorted(groups.items()), 1):
        outcomes = {r["outcome"] for r in rows}
        if outcomes == {"SAFE"}:
            decision, provenance = "ACCEPT", "DERIVED_FROM_OBSERVED"
        elif outcomes == {"FORBIDDEN"}:
            decision, provenance = "REJECT", "OBSERVED_EXCEPTION"
        else:
            decision, provenance = "UNKNOWN", "CONFLICTING_OBSERVATIONS"
        rules.append({"id": f"rule-{n}",
                      "conditions": dict(key), "decision": decision,
                      "source_episode_ids": sorted(r["id"] for r in rows),
                      "provenance_kind": provenance})
    episodes_rep = [{"id": r["id"], "context": r["context"], "outcome": r["outcome"],
                     "source_episode_ids": [r["id"]], "provenance_kind": "OBSERVED"}
                    for r in episodes]
    safe = sum(r["outcome"] == "SAFE" for r in episodes)
    forbidden = sum(r["outcome"] == "FORBIDDEN" for r in episodes)
    majority = "ACCEPT" if safe >= forbidden else "REJECT"
    ids = sorted(r["id"] for r in episodes)
    return {
        "episode_retrieval": {"records": episodes_rep},
        "unqualified_consolidation": {"records": [{"id": "majority-skill", "conditions": {},
            "decision": majority, "source_episode_ids": ids, "provenance_kind": "INFERENCE"}]},
        "exception_preserving": {"records": rules},
    }


def reconstruct_decision(name, representation, query):
    context = query["context"]
    rows = representation["records"]
    if name == "episode_retrieval":
        matches = [r for r in rows if r["context"] == context]
        outcomes = {r["outcome"] for r in matches}
        outcome = next(iter(outcomes)) if len(outcomes) == 1 else "UNKNOWN"
        decision = {"SAFE": "ACCEPT", "FORBIDDEN": "REJECT"}.get(outcome, "UNKNOWN")
    elif name == "unqualified_consolidation":
        matches = rows
        decision = rows[0]["decision"]
    else:
        matches = [r for r in rows if all(context.get(k) == v for k, v in r["conditions"].items())]
        decision = matches[0]["decision"] if len(matches) == 1 else "UNKNOWN"
    return {"decision": decision,
            "source_episode_ids": sorted({i for r in matches for i in r["source_episode_ids"]}),
            "matched_record_ids": sorted(r["id"] for r in matches)}


def audit(raw, fixture, fixture_bytes, candidate_bytes):
    errors = []
    if raw.get("fixture_sha256") != hashlib.sha256(fixture_bytes).hexdigest():
        errors.append("fixture hash mismatch")
    if raw.get("candidate_sha256") != hashlib.sha256(candidate_bytes).hexdigest():
        errors.append("candidate hash mismatch")
    expected = independent_reconstruction(fixture)
    if raw.get("representations", {}).keys() != expected.keys():
        errors.append("representation set mismatch")
        return errors
    budget = fixture["budget"]
    for name, rebuilt in expected.items():
        submitted = raw["representations"][name]
        if submitted.get("records") != rebuilt["records"]:
            errors.append(f"{name}: records/provenance differ from independent reconstruction")
        blob = canonical({"records": submitted.get("records", [])}).encode("utf-8")
        if submitted.get("stored_records") != len(submitted.get("records", [])):
            errors.append(f"{name}: record count mismatch")
        if len(submitted.get("records", [])) > budget["max_records"]:
            errors.append(f"{name}: record budget exceeded")
        if submitted.get("serialized_bytes") != len(blob):
            errors.append(f"{name}: serialized byte count mismatch")
        if len(blob) > budget["max_serialized_bytes"]:
            errors.append(f"{name}: byte budget exceeded")
        source_ids = {r["id"] for r in fixture["episodes"]}
        referenced = {sid for rec in submitted.get("records", [])
                      for sid in rec.get("source_episode_ids", [])}
        if referenced != source_ids:
            errors.append(f"{name}: source ID coverage mismatch")

    desired = sorted(expected["exception_preserving"]["records"],
                     key=lambda r: canonical(r["conditions"]))
    oracle = sorted(fixture["applicability_oracle"],
                    key=lambda r: canonical(r["conditions"]))
    fields = ("conditions", "decision", "source_episode_ids", "provenance_kind")
    normalize = lambda row: {**{k: row[k] for k in fields},
                             "source_episode_ids": sorted(row["source_episode_ids"])}
    if [normalize(row) for row in desired] != [normalize(row) for row in oracle]:
        errors.append("fixture applicability oracle inconsistent with independent reconstruction")
    observed_rows = raw.get("rows", [])
    expected_count = len(fixture["queries"]) * len(expected)
    if len(observed_rows) != expected_count:
        errors.append(f"decision row count {len(observed_rows)} != {expected_count}")
    index = {(r.get("representation"), r.get("query_id")): r for r in observed_rows}
    if len(index) != len(observed_rows):
        errors.append("duplicate decision rows")
    for name in expected:
        for query in fixture["queries"]:
            row = index.get((name, query["id"]))
            if row is None:
                errors.append(f"missing row {name}/{query['id']}")
                continue
            got = {key: row.get(key) for key in ("decision", "source_episode_ids", "matched_record_ids")}
            want = reconstruct_decision(name, expected[name], query)
            if got != want:
                errors.append(f"{name}/{query['id']}: decision/provenance mismatch")
    return errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    raw = json.loads(args.raw.read_text(encoding="utf-8"))
    fixture_path = HERE / "fixture.json"
    candidate_path = HERE / "candidate.py"
    fixture_bytes = fixture_path.read_bytes()
    errors = audit(raw, json.loads(fixture_bytes), fixture_bytes, candidate_path.read_bytes())
    report = {"status": "PASS_METHOD_SCOPED" if not errors else "FAIL",
              "independently_audited_rows": len(raw.get("rows", [])), "errors": errors}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
