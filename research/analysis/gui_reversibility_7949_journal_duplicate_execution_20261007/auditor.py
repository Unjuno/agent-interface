import json
import pathlib
import sqlite3
import sys


def expected_from_db(db_path):
    db = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    s = db.execute("SELECT revision, agent_value, external_value FROM artifact WHERE id=1").fetchone()
    c = db.execute("SELECT base_revision, agent_field, agent_original, baseline_state FROM recovery_certificate WHERE id=1").fetchone()
    j = db.execute("SELECT seq, revision, field, before_value, after_value FROM journal ORDER BY seq").fetchall()
    db.close()
    state = dict(zip(("revision", "agent_value", "external_value"), s))
    cert = {"base_revision": c[0], "agent_field": c[1], "agent_original": c[2], "baseline_state": json.loads(c[3])}
    rows = [dict(zip(("seq", "revision", "field", "before_value", "after_value"), row)) for row in j]
    return {"state": state, "certificate": cert, "journal": rows}


def independent_decision(raw):
    s, c, journal = raw["state"], raw["certificate"], raw["journal"]
    delta = s["revision"] - c["base_revision"]
    baseline = c["baseline_state"]
    if delta == 0 and len(journal) == 0 and s == baseline:
        return {"decision": "NO_CHANGE", "proposal": None}
    if delta < 0 or len(journal) != delta:
        return {"decision": "UNKNOWN", "proposal": None}
    if any(row["seq"] != c["base_revision"] + n or row["revision"] != c["base_revision"] + n
           for n, row in enumerate(journal, 1)):
        return {"decision": "UNKNOWN", "proposal": None}
    replay = {"agent_value": baseline["agent_value"], "external_value": baseline["external_value"]}
    for row in journal:
        key = row["field"]
        if key not in replay or row["before_value"] != replay[key]:
            return {"decision": "UNKNOWN", "proposal": None}
        replay[key] = row["after_value"]
    if replay["agent_value"] != s["agent_value"] or replay["external_value"] != s["external_value"]:
        return {"decision": "UNKNOWN", "proposal": None}
    if any(row["field"] == c["agent_field"] for row in journal):
        return {"decision": "UNKNOWN", "proposal": None}
    return {"decision": "PROPOSE_COMPENSATION", "proposal": {
        "restore_field": c["agent_field"], "restore_value": c["agent_original"],
        "preserve_field": "external_value", "preserve_value": s["external_value"], "bind_revision": s["revision"]}}


def unique_rows(rows, expected_ids, label, errors):
    ids = [r.get("case_id") for r in rows]
    if len(ids) != len(set(ids)):
        errors.append(f"{label}:duplicate")
    if set(ids) != set(expected_ids) or len(ids) != len(expected_ids):
        errors.append(f"{label}:missing_or_unexpected")
    return {r.get("case_id"): r for r in rows}


def check(observations, candidate, expected_ids, db_root):
    errors = []
    obs = unique_rows(observations, expected_ids, "observations", errors)
    cand = unique_rows(candidate, expected_ids, "candidate", errors)
    for case_id in expected_ids:
        path = db_root / f"{case_id}.sqlite"
        raw = expected_from_db(path)
        if obs.get(case_id) != {"case_id": case_id, **raw}:
            errors.append(f"observer_mismatch:{case_id}")
        expected = independent_decision(raw)
        got = cand.get(case_id)
        if got is None or got != {"case_id": case_id, **expected}:
            errors.append(f"decision_mismatch:{case_id}")
    return errors


def main(root, output_path):
    root = pathlib.Path(root)
    cases = json.loads((root / "cases.json").read_text())["cases"]
    ids = [c["id"] for c in cases]
    observations = json.loads((root / "out/observations.json").read_text())["observations"]
    candidate = json.loads((root / "out/candidate.json").read_text())["decisions"]
    candidate_doc = json.loads((root / "out/candidate.json").read_text())
    errors = check(observations, candidate, ids, root / "out/db")
    if candidate_doc.get("allocation") != "GUI-REVERSIBILITY-7949-JOURNAL-A01-20261007":
        errors.append("candidate_allocation_mismatch")
    # Auditor self-controls: exact output cardinality, identity, action, and protected external value.
    base = [r.copy() for r in candidate]
    mutants = []
    mutants.append(("duplicate", base + [base[0].copy()]))
    extra = base + [{"case_id": "unexpected", "decision": "NO_CHANGE", "proposal": None}]
    mutants.append(("unexpected", extra))
    wrong_action = [r.copy() for r in base]
    wrong_action[1] = {**wrong_action[1], "decision": "NO_CHANGE", "proposal": None}
    mutants.append(("wrong_decision", wrong_action))
    wrong_preserve = [r.copy() for r in base]
    wrong_preserve[1] = {**wrong_preserve[1], "proposal": {**wrong_preserve[1]["proposal"], "preserve_value": "overwritten"}}
    mutants.append(("external_value_mutation", wrong_preserve))
    controls = []
    for name, mutant in mutants:
        rejected = bool(check(observations, mutant, ids, root / "out/db"))
        controls.append({"name": name, "rejected": rejected})
        if not rejected:
            errors.append(f"mutation_survived:{name}")
    raw_mutants = []
    duplicate_raw = [r.copy() for r in observations] + [observations[0].copy()]
    raw_mutants.append(("duplicate_raw_row", duplicate_raw))
    missing_raw = [r.copy() for r in observations if r["case_id"] != "state_mismatch"]
    raw_mutants.append(("missing_raw_row", missing_raw))
    altered_state = json.loads(json.dumps(observations))
    altered_state[1]["state"]["external_value"] = "mutated"
    raw_mutants.append(("altered_observed_state", altered_state))
    altered_journal = json.loads(json.dumps(observations))
    altered_journal[1]["journal"][0]["after_value"] = "mutated"
    raw_mutants.append(("altered_observed_journal", altered_journal))
    raw_controls = []
    for name, mutant in raw_mutants:
        rejected = bool(check(mutant, candidate, ids, root / "out/db"))
        raw_controls.append({"name": name, "rejected": rejected})
        if not rejected:
            errors.append(f"raw_mutation_survived:{name}")
    result = {"allocation": "GUI-REVERSIBILITY-7949-JOURNAL-A01-20261007",
              "verdict": "PASS_JOURNAL_STATE_RECONCILIATION_SCOPED" if not errors else "FAIL_OR_STOP_AUDIT",
              "case_count": len(ids), "errors": errors, "mutation_controls": controls,
              "raw_mutation_controls": raw_controls,
              "base_database_cases_reconstructed": len(ids), "authority_or_external_actions": 0}
    pathlib.Path(output_path).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"verdict": result["verdict"], "case_count": len(ids), "errors": len(errors),
                      "output_mutations_rejected": sum(x["rejected"] for x in controls),
                      "raw_mutations_rejected": sum(x["rejected"] for x in raw_controls)}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
