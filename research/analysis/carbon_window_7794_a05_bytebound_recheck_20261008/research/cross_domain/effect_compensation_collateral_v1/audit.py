from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

INITIAL = ("old", "preserve")
TARGET = ("target", "preserve")
VERIFIED = "EFFECT_VERIFIED"
COMPENSATED = "EFFECT_CONTRADICTED_COMPENSATED"
INCOMPLETE = "EFFECT_CONTRADICTED_COMPENSATION_INCOMPLETE"


def labels(state, history):
    first = history[0]
    primary = VERIFIED if (first[2], first[3]) == TARGET else (COMPENSATED if state[0] == INITIAL[0] else INCOMPLETE)
    full = VERIFIED if (first[2], first[3]) == TARGET else (COMPENSATED if state == INITIAL else INCOMPLETE)
    return primary, full


def truth(scenario):
    return {
        "correct": VERIFIED,
        "wrong_compensated_clean": COMPENSATED,
        "wrong_compensated_collateral": INCOMPLETE,
    }[scenario]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--plan", required=True, type=Path)
    p.add_argument("--evidence", required=True, type=Path)
    p.add_argument("--result", required=True, type=Path)
    p.add_argument("--audit-result", required=True, type=Path)
    a = p.parse_args()
    plan = json.loads(a.plan.read_text())
    published = json.loads(a.result.read_text())
    errors=[]
    seen=set()
    primary_truth=0
    full_truth=0
    rows=[]
    published_by_id={row["id"]:row for row in published["rows"]}
    for case in plan["cases"]:
        cid=case["id"]
        if cid in seen: errors.append(f"duplicate plan id {cid}")
        seen.add(cid)
        db=a.evidence/cid/"state.sqlite"
        conn=sqlite3.connect(db)
        state=tuple(conn.execute("SELECT primary_value,collateral_value FROM state WHERE id=1").fetchone())
        history=conn.execute("SELECT seq,kind,primary_value,collateral_value FROM events ORDER BY seq").fetchall()
        conn.close()
        if not history or history[0][1] != "effect": errors.append(f"{cid}: missing primary effect")
        if any(x[0] != i+1 for i,x in enumerate(history)): errors.append(f"{cid}: sequence gap")
        if tuple(history[-1][2:4]) != state: errors.append(f"{cid}: final event/state mismatch")
        primary,full=labels(state,history)
        expected=truth(case["scenario"])
        primary_truth += primary == expected
        full_truth += full == expected
        retained=published_by_id.get(cid)
        if retained is None: errors.append(f"{cid}: missing published row")
        else:
            if retained["primary_only"] != primary: errors.append(f"{cid}: primary label mismatch")
            if retained["full_invariant"] != full: errors.append(f"{cid}: full label mismatch")
            if (retained["state"]["primary"],retained["state"]["collateral"]) != state: errors.append(f"{cid}: retained state mismatch")
            if len(retained["history"]) != len(history): errors.append(f"{cid}: retained history length mismatch")
        rows.append((cid,case["scenario"],state,primary,full,expected))
    if len(seen) != 30: errors.append(f"expected 30 unique ids, got {len(seen)}")
    damaged=[r for r in rows if r[1]=="wrong_compensated_collateral"]
    if len(damaged)!=10: errors.append("damaged stratum count")
    if any(r[2] != ("old","damaged") for r in damaged): errors.append("damaged final state")
    if any(r[3] != COMPENSATED for r in damaged): errors.append("primary-only discriminator")
    if any(r[4] != INCOMPLETE for r in damaged): errors.append("full-invariant discriminator")
    if primary_truth != 20: errors.append(f"primary truth expected 20 got {primary_truth}")
    if full_truth != 30: errors.append(f"full truth expected 30 got {full_truth}")
    audit={
        "schema":"effect-compensation-collateral-audit-v1",
        "cases":len(rows),
        "primary_only_truthful_count":primary_truth,
        "full_invariant_truthful_count":full_truth,
        "errors":errors,
        "pass":not errors,
    }
    a.audit_result.write_text(json.dumps(audit,indent=2,sort_keys=True)+"\n")
    if errors:
        raise SystemExit("AUDIT_FAIL: " + "; ".join(errors))
    print("PASS_INDEPENDENT_AUDIT")

if __name__ == "__main__":
    main()
