"""Independent read-only oracle: does not import or run the receiver/runner."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import sqlite3
from collections import Counter
from pathlib import Path

SCENARIOS = {"applied_stable", "applied_then_revoked", "applied_then_replaced",
             "applied_then_unrelated", "rejected_then_allowed", "precommit_then_revoked",
             "changed_payload", "new_id_after_revocation"}

def require(test, message):
    if not test:
        raise AssertionError(message)

def fingerprint(req):
    return hashlib.sha256(json.dumps(req, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()

def inspect_row(row):
    s, p = row["scenario"], row["policy"]
    require(s in SCENARIOS and p in ("validate_first", "outcome_first"), "unknown case")
    first, second, third = [row[k] for k in ("first", "second", "third")]
    require(first["returncode"] == (74 if s == "precommit_then_revoked" else 73), "crash exit")
    require(first["response"] is None and first["stdout"] == "", "absent acknowledgement")
    require(len({a["pid"] for a in (first, second, third)}) == 3, "restart identity")
    require(first["started_ns"] < first["ended_ns"] <= row["mutation_started_ns"] <= row["mutation_ended_ns"] <= second["started_ns"] < second["ended_ns"] <= third["started_ns"] < third["ended_ns"], "causal order")
    require(all(a["stderr"] == "" for a in (first, second, third)), "stderr")
    start = row["start"]
    original = {"singleton": 1, "context_id": "A", "generation": 1,
                "allowed": 0 if s == "rejected_then_allowed" else 1, "unrelated": 0}
    require(start == {"context": [original], "decisions": [], "effects": []}, "initial state")
    af = row["after_first"]
    require(af["context"] == [original], "initial context changed")
    applied = s not in ("precommit_then_revoked", "rejected_then_allowed")
    require(len(af["effects"]) == int(applied), "initial committed effect count")
    require(len(af["decisions"]) == int(s != "precommit_then_revoked"), "initial decision count")
    if af["decisions"]:
        d = af["decisions"][0]
        require(d["fingerprint"] == fingerprint(row["request"]), "initial payload binding")
        saved = json.loads(d["receipt"])
        require(saved["outcome"] == ("APPLIED" if applied else "REJECTED"), "persisted outcome")
    expected_ctx = dict(original)
    if s in ("applied_then_revoked", "precommit_then_revoked", "new_id_after_revocation"):
        expected_ctx["allowed"] = 0
    elif s == "applied_then_replaced":
        expected_ctx["generation"] = 2
    elif s == "applied_then_unrelated":
        expected_ctx["unrelated"] = 1
    elif s == "rejected_then_allowed":
        expected_ctx["allowed"] = 1
    require(row["before_retry"] == {**af, "context": [expected_ctx]}, "intervention")
    for snap in (row["after_second"], row["final"]):
        require(snap["effects"] == af["effects"], "duplicate or new stale effect")
        require(snap["context"] == [expected_ctx], "replay changed context")
        for d in af["decisions"]:
            require(d in snap["decisions"], "historical decision overwritten")
        expected_n = len(af["decisions"]) + int(s in ("precommit_then_revoked", "new_id_after_revocation"))
        require(len(snap["decisions"]) == expected_n, "terminal decision count")
    require(row["after_second"] == row["final"], "second replay mutated durable state")
    historical_case = s not in ("precommit_then_revoked", "changed_payload", "new_id_after_revocation")
    contradiction = False
    for attempt in (second, third):
        require(attempt["returncode"] == 0, "recovery process")
        response = attempt["response"]
        require(json.loads(attempt["stdout"]) == response, "stdout/response disagreement")
        require(response["grants_authority"] is False and response["new_effects"] == 0, "replay authority/effect")
        current = response["current_semantics"]
        require(current["context"] == {k: v for k,v in expected_ctx.items() if k != "singleton"}, "current diagnostics")
        require(current["valid"] == (expected_ctx["allowed"] == 1 and expected_ctx["generation"] == 1), "current validity")
        if historical_case:
            contradiction = response["receipt"] != saved
            if p == "outcome_first":
                require(not contradiction and response["historical"] is True, "candidate did not replay original outcome")
        elif s == "changed_payload":
            require(response["receipt"]["outcome"] == "CONFLICT", "content conflict not refused")
        else:
            require(response["receipt"]["outcome"] == "REJECTED", "new command must validate current context")
    repeat_drift = second["response"]["receipt"] != third["response"]["receipt"]
    if p == "outcome_first":
        require(not repeat_drift, "candidate replay response drift")
    return {"contradiction": int(contradiction), "historical_case": int(historical_case),
            "effects": int(applied), "new_stale_effects": 0, "duplicate_effects": 0,
            "repeat_response_shape_drift": int(repeat_drift)}

def main(root):
    manifest = json.loads((root/"manifest.json").read_text())
    for path, expected in manifest.items():
        require(hashlib.sha256((root/path).read_bytes()).hexdigest() == expected, "file hash: "+path)
    rows = [json.loads(l) for l in (root/"records.jsonl").read_text().splitlines()]
    freeze = json.loads((root/"protocol.json").read_text())
    require(len(rows) == 80 and len(freeze["schedule"]) == 80, "finite budget")
    counts = {p: Counter() for p in ("validate_first", "outcome_first")}
    per_scenario = {p: {} for p in counts}
    for i, row in enumerate(rows):
        require({k: row[k] for k in ("policy","scenario","rep")} == freeze["schedule"][i], "schedule mismatch")
        require(row["ordinal"] == i+1, "ordinal mismatch")
        result = inspect_row(row)
        con = sqlite3.connect(f"file:{root/row['db_path']}?mode=ro", uri=True)
        con.row_factory = sqlite3.Row
        actual = {t: [dict(r) for r in con.execute("SELECT * FROM "+t+" ORDER BY rowid")]
                  for t in ("context", "effects", "decisions")}
        require(con.execute("PRAGMA integrity_check").fetchone()[0] == "ok", "SQLite integrity")
        con.close()
        require(actual == row["final"], "retained database/snapshot mismatch")
        case = root/Path(row["db_path"]).parent
        require(json.loads((case/"record.json").read_text()) == row, "case/ledger mismatch")
        for phase in ("first","second","third"):
            require(json.loads((case/(phase+".process.json")).read_text()) == row[phase], "process record mismatch")
            events = [json.loads(l) for l in (case/(phase+".events.jsonl")).read_text().splitlines()]
            kinds = [e["event"] for e in events]
            expected = ["transaction_started", "decision_prepared", "committed"]
            if phase == "first":
                expected = (["transaction_started", "decision_prepared", "exit_before_commit"]
                            if row["scenario"] == "precommit_then_revoked"
                            else expected+["exit_after_commit_before_response"])
            require(kinds == expected, "event sequence")
            require(all(e["pid"] == row[phase]["pid"] for e in events), "event process identity")
            require(all(row[phase]["started_ns"] <= e["ns"] <= row[phase]["ended_ns"] for e in events), "event clock bracket")
        counts[row["policy"]].update({"cases": 1, **result})
        cell = per_scenario[row["policy"]].setdefault(row["scenario"], Counter())
        cell.update({"cases": 1, **result})
    base = next(r for r in rows if r["policy"] == "outcome_first" and r["scenario"] == "applied_then_revoked")
    corruptions = {
        "lost_ack_relabelled": lambda r: r["first"].update(response={"receipt":"SAFE_YIELD"}),
        "historical_result_changed": lambda r: r["second"]["response"]["receipt"].update(outcome="REJECTED"),
        "duplicate_effect": lambda r: r["final"]["effects"].append(dict(r["final"]["effects"][0])),
        "authority_in_receipt": lambda r: r["second"]["response"].update(grants_authority=True),
        "bad_causal_order": lambda r: r["second"].update(started_ns=0),
    }
    checks = {}
    for name, corrupt in corruptions.items():
        bad = copy.deepcopy(base)
        corrupt(bad)
        try:
            inspect_row(bad)
        except AssertionError:
            checks[name] = "REJECTED"
        else:
            raise AssertionError("corruption passed: "+name)
    summary = {"status": "PASS_SCOPED_CANDIDATE", "audited_cases": len(rows),
               "receiver_processes": len(rows)*3, "manifest_files_verified": len(manifest),
               "policies": counts, "by_scenario": per_scenario,
               "corruption_controls": checks,
               "scope": "private cooperative SQLite process-restart reliability; not production or GUI safety"}
    print(json.dumps(summary, indent=2, sort_keys=True))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    main(parser.parse_args().root)
