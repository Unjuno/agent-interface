#!/usr/bin/env python3
"""Independently reconstruct provenance invariants and mutation outcomes."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected(fixture):
    atoms = []
    for item in fixture["records"]:
        has_source = item.get("source") is not None and item["origin"] != "UNKNOWN"
        atoms.append({**item, "source_refs": [item["source"]] if has_source else [],
                      "source_status": "BOUND" if has_source else "UNKNOWN",
                      "kind": "ATOM", "authority_class": item["origin"]})
    app_groups = {}
    for atom in atoms:
        if atom["origin"] == "APPLICATION_CONTENT":
            app_groups.setdefault(atom["text"], []).append(atom)
    summaries = []
    for ordinal, text in enumerate(sorted(app_groups), 1):
        group = app_groups[text]
        sources = {source for item in group for source in item["source_refs"]}
        summaries.append({"id": "summary" + str(ordinal), "text": text,
                          "origin": "DERIVED_SUMMARY", "source": None,
                          "revision": None, "key": None,
                          "source_refs": sorted(sources),
                          "source_status": "BOUND" if all(x["source_status"] == "BOUND" for x in group) else "UNKNOWN",
                          "kind": "SUMMARY", "authority_class": "DESCRIPTIVE_ONLY",
                          "members": sorted(x["id"] for x in group)})
    newest = {}
    for atom in atoms:
        if atom["origin"] != "USER_INSTRUCTION" or atom["source_status"] != "BOUND" or not atom["key"]:
            continue
        key = atom["key"]
        if key not in newest or atom["revision"] > newest[key]["revision"]:
            newest[key] = atom
    words = set(fixture["retrieval_query"].lower().split())
    result_rows = []
    for atom in atoms + summaries:
        if words & set(atom["text"].lower().split()):
            result_rows.append({key: atom[key] for key in
                                ("id", "text", "origin", "source_refs", "source_status", "authority_class", "kind")})
    active = [{key: atom[key] for key in ("id", "text", "key", "revision", "source_refs")}
              for atom in sorted(newest.values(), key=lambda x: x["key"])
              if words & set(atom["text"].lower().split())]
    return atoms, summaries, result_rows, active


def audit(raw, fixture):
    errors = []
    atoms, summaries, rows, active = expected(fixture)
    if raw.get("fixture_sha256") != digest(HERE / "fixture.json"):
        errors.append("fixture digest mismatch")
    if raw.get("candidate_sha256") != digest(HERE / "candidate.py"):
        errors.append("candidate digest mismatch")
    if raw.get("stored") != atoms:
        errors.append("stored atoms do not preserve exact source/origin binding")
    if raw.get("summaries") != summaries:
        errors.append("summary/consolidation provenance or members mismatch")
    if raw.get("retrieved") != rows:
        errors.append("retrieved evidence/provenance projection mismatch")
    if raw.get("authorized_intents") != active:
        errors.append("active user-intent set/revision mismatch")
    if raw.get("unknown_source_authority_count") != 0:
        errors.append("missing-source record acquired instruction authority")
    for item in raw.get("retrieved", []):
        if item.get("authority_class") == "USER_INSTRUCTION" and not (
                item.get("origin") == "USER_INSTRUCTION" and item.get("kind") == "ATOM"
                and item.get("source_status") == "BOUND" and item.get("source_refs")):
            errors.append("non-user or derived content promoted to user authority")
    return errors


def mutations(raw):
    variants = {}
    app = copy.deepcopy(raw)
    next(x for x in app["stored"] if x["id"] == "app2")["authority_class"] = "USER_INSTRUCTION"
    variants["promote_application_text"] = app
    summary = copy.deepcopy(raw)
    summary["summaries"][0]["source_refs"] = []
    variants["drop_summary_sources"] = summary
    stale = copy.deepcopy(raw)
    old = next(x for x in stale["stored"] if x["id"] == "u2")
    stale["authorized_intents"] = [{"id": old["id"], "text": old["text"], "key": old["key"],
                                    "revision": old["revision"], "source_refs": old["source_refs"]}]
    variants["resurrect_superseded_revision"] = stale
    unknown = copy.deepcopy(raw)
    unknown_atom = next(x for x in unknown["stored"] if x["id"] == "unknown1")
    unknown_atom["source_status"] = "BOUND"
    unknown_atom["authority_class"] = "USER_INSTRUCTION"
    unknown["unknown_source_authority_count"] = 1
    variants["trust_missing_source"] = unknown
    return variants


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    fixture = json.loads((HERE / "fixture.json").read_text(encoding="utf-8"))
    raw = json.loads(args.raw.read_text(encoding="utf-8"))
    errors = audit(raw, fixture)
    controls = {}
    for name, changed in mutations(raw).items():
        found = audit(changed, fixture)
        controls[name] = {"rejected": bool(found), "error_count": len(found)}
        if not found:
            errors.append("mutation accepted: " + name)
    count = len(fixture["records"])
    result = {"status": "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD",
              "records_reconstructed": count, "transforms_checked": fixture["transforms"],
              "authorized_intents": len(raw.get("authorized_intents", [])),
              "mutation_controls": controls, "errors": errors,
              "scope": "finite synthetic provenance pipeline; no model or live security claim"}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
