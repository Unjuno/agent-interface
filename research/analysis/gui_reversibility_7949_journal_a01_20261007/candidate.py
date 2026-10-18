"""Candidate reconciliation policy; all conclusions derive from DB observations."""

import shutil
import sqlite3
from pathlib import Path

import protocol


def chain_is_complete(before, after):
    b, a = before["state"], after["state"]
    events = after["journal"]
    if a["revision"] - b["revision"] != len(events):
        return False
    expected_seq = 1
    expected_rev = b["revision"]
    values = {"x": b["x"], "y": b["y"]}
    for e in events:
        if e["seq"] != expected_seq or e["rev_before"] != expected_rev or e["rev_after"] != expected_rev + 1:
            return False
        if e["field"] not in values or values[e["field"]] != e["old_value"]:
            return False
        values[e["field"]] = e["new_value"]
        expected_seq += 1
        expected_rev += 1
    return expected_rev == a["revision"] and values == {"x": a["x"], "y": a["y"]}


def run_case(case, dbdir):
    dbdir = Path(dbdir)
    dbdir.mkdir(parents=True, exist_ok=True)
    path = dbdir / f"{case['id']}.sqlite"
    protocol.initialize(path)
    before = protocol.observer_process(path)
    shutil.copy2(path, dbdir / f"{case['id']}.before.sqlite")
    protocol.writer_process(path, case["external_write"])
    after_external = protocol.observer_process(path)
    shutil.copy2(path, dbdir / f"{case['id']}.external.sqlite")
    old_state = before["state"]
    changed_x = after_external["state"]["x"] != old_state["x"]
    valid = chain_is_complete(before, after_external)
    if changed_x:
        decision = "UNKNOWN_SAME_FIELD_CONFLICT"
    elif not valid:
        decision = "UNKNOWN_JOURNAL_STATE_MISMATCH"
    else:
        decision = "COMPENSATED_BASELINE" if after_external == before else "COMPENSATED_DISJOINT"

    fresh_revision = None
    if decision.startswith("COMPENSATED_"):
        fresh_revision = after_external["state"]["revision"]
        # One compare-and-compensate transaction: never overwrite a newer state.
        with sqlite3.connect(path) as db:
            current = db.execute("SELECT revision,x FROM artifact WHERE object_id='doc'").fetchone()
            if current != (after_external["state"]["revision"], old_state["x"]):
                decision = "UNKNOWN_CONCURRENT_CHANGE"
            else:
                rev = current[0]
                db.execute("UPDATE artifact SET x=0, revision=? WHERE object_id='doc' AND revision=? AND x=?", (rev + 1, rev, old_state["x"]))
                db.execute("INSERT INTO journal VALUES ((SELECT COALESCE(MAX(seq),0)+1 FROM journal),?,?, 'x',?,0,'agent','compensate-1')", (rev, rev + 1, old_state["x"]))
    final = protocol.observer_process(path)
    shutil.copy2(path, dbdir / f"{case['id']}.final.sqlite")
    return {"id": case["id"], "decision": decision,
            "stale_certificate": "CERTIFICATE_CURRENT" if after_external == before else "UNKNOWN_STALE_CERTIFICATE",
            "fresh_certificate_revision": fresh_revision, "before": before,
            "after_external": after_external, "final": final}
