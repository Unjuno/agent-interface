"""Independent read-only checker. Deliberately does not import candidate/writer."""

import sqlite3
from pathlib import Path


def read_snapshot(path):
    with sqlite3.connect(f"file:{Path(path).resolve()}?mode=ro", uri=True) as db:
        s = db.execute("SELECT object_id,revision,x,y FROM artifact").fetchone()
        es = db.execute("SELECT seq,rev_before,rev_after,field,old_value,new_value,actor,txid FROM journal ORDER BY seq").fetchall()
    names = ("object_id", "revision", "x", "y")
    event_names = ("seq", "rev_before", "rev_after", "field", "old_value", "new_value", "actor", "txid")
    return {"state": dict(zip(names, s)), "journal": [dict(zip(event_names, e)) for e in es]}


def replay_is_valid(before, observed):
    state = dict(before["state"])
    events = observed["journal"]
    if observed["state"]["revision"] - state["revision"] != len(events):
        return False
    for i, e in enumerate(events, 1):
        if (e["seq"], e["rev_before"], e["rev_after"]) != (i, state["revision"], state["revision"] + 1):
            return False
        if e["field"] not in ("x", "y") or state[e["field"]] != e["old_value"]:
            return False
        state[e["field"]] = e["new_value"]
        state["revision"] += 1
    return state == observed["state"]


def verify_case(row, dbdir):
    errors = []
    dbdir = Path(dbdir)
    expected_files = (f"{row['id']}.before.sqlite", f"{row['id']}.external.sqlite", f"{row['id']}.final.sqlite")
    try:
        before, external, final = [read_snapshot(dbdir / f) for f in expected_files]
    except Exception as exc:
        return [f"snapshot_read:{type(exc).__name__}"]
    if row["before"] != before or row["after_external"] != external or row["final"] != final:
        errors.append("raw_observation_mismatch")
    if not replay_is_valid(before, external):
        expected = "UNKNOWN_JOURNAL_STATE_MISMATCH"
    elif external["state"]["x"] != before["state"]["x"]:
        expected = "UNKNOWN_SAME_FIELD_CONFLICT"
    else:
        expected = "COMPENSATED_BASELINE" if external == before else "COMPENSATED_DISJOINT"
    if row["decision"] != expected:
        errors.append("decision_mismatch")
    if expected.startswith("COMPENSATED_"):
        if final["state"]["x"] != 0 or final["state"]["y"] != external["state"]["y"]:
            errors.append("compensation_scope_or_final_state")
        if final["state"]["revision"] != external["state"]["revision"] + 1:
            errors.append("compensation_revision")
        if final["journal"][:-1] != external["journal"]:
            errors.append("external_journal_changed_during_compensation")
        if not final["journal"]:
            errors.append("missing_compensation_event")
        else:
            event = final["journal"][-1]
            if (event["seq"], event["rev_before"], event["rev_after"], event["field"],
                event["old_value"], event["new_value"], event["actor"]) != (
                    len(external["journal"]) + 1, external["state"]["revision"],
                    external["state"]["revision"] + 1, "x", external["state"]["x"], 0, "agent"):
                errors.append("compensation_event_mismatch")
        if row["fresh_certificate_revision"] != external["state"]["revision"]:
            errors.append("certificate_revision")
    else:
        if final != external:
            errors.append("unknown_case_mutated_state")
        if row["fresh_certificate_revision"] is not None:
            errors.append("unknown_case_fresh_certificate")
    stale = "CERTIFICATE_CURRENT" if external == before else "UNKNOWN_STALE_CERTIFICATE"
    if row["stale_certificate"] != stale:
        errors.append("stale_certificate_classification")
    return errors
