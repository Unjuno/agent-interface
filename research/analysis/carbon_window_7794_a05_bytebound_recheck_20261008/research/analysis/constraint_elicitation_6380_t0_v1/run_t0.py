#!/usr/bin/env python3
"""Finite method test for counterexample-driven task-constraint elicitation.

No model, human, GUI, network, or execution authority is used. The respondent
oracle is scripted from independent vignette cards and only demonstrates the
state/provenance contract, not real elicitation effectiveness.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
POLICIES = ("SOURCE_ONLY", "GENERIC", "COUNTEREXAMPLE", "CHECKLIST")

# Each card is independently authored fixture truth. `source_clause` is already
# in the request and is not eligible for discovery credit. `hidden` is known to
# the scripted respondent but absent from the original request.
CASES = [
    {"id":"formula-preserve", "request":"Update the Q2 revenue cell.", "source_clause":None,
     "hidden":"preserve_formula", "scenario":"formula_overwrite", "role":"owner", "privacy":"public", "revision":1},
    {"id":"explicit-prohibition", "request":"Update the Q2 revenue cell; do not change the adjacent formula.", "source_clause":"preserve_formula",
     "hidden":"preserve_formula", "scenario":"formula_overwrite", "role":"owner", "privacy":"public", "revision":1},
    {"id":"harmless-format", "request":"Update the title text.", "source_clause":None,
     "hidden":"no_constraint", "scenario":"formatting_change", "role":"owner", "privacy":"public", "revision":1},
    {"id":"conflicting-respondents", "request":"Update the shared status cell.", "source_clause":None,
     "hidden":"preserve_shared_value", "scenario":"shared_value_change", "role":"editor", "privacy":"public", "revision":1,
     "unauthorized_answer":{"role":"viewer","answer":"ALLOW"}},
    {"id":"respondent-absent", "request":"Replace the shared file.", "source_clause":None,
     "hidden":"preserve_shared_link", "scenario":"link_break", "role":None, "privacy":"public", "revision":1},
    {"id":"privacy-restricted", "request":"Revise the case note.", "source_clause":None,
     "hidden":"preserve_private_note", "scenario":"private_note_disclosure", "role":"owner", "privacy":"restricted", "revision":1},
    {"id":"no-answer", "request":"Clean up the archive.", "source_clause":None,
     "hidden":"preserve_audit_trail", "scenario":"delete_audit_entry", "role":"owner", "privacy":"public", "revision":1,
     "answer":"NO_ANSWER"},
    {"id":"stale-question", "request":"Rename the report.", "source_clause":None,
     "hidden":"preserve_shared_destination", "scenario":"move_shared_destination", "role":"owner", "privacy":"public", "revision":1,
     "answer_revision":2},
]

# Frozen scenario catalog. Counterexample and checklist policies see only these
# abstract classes, never hidden labels or truth cards.
SCENARIOS = [
    {"id":"formula_overwrite", "prompt":"Would overwriting an adjacent formula be unacceptable?"},
    {"id":"shared_value_change", "prompt":"Would changing a shared value outside the target be unacceptable?"},
    {"id":"link_break", "prompt":"Would breaking the existing shared link be unacceptable?"},
    {"id":"private_note_disclosure", "prompt":"Would disclosing the private note be unacceptable?"},
    {"id":"delete_audit_entry", "prompt":"Would deleting an audit entry be unacceptable?"},
    {"id":"move_shared_destination", "prompt":"Would moving the shared destination be unacceptable?"},
    {"id":"formatting_change", "prompt":"Would an unrelated formatting change be unacceptable?"},
]

def ask_ids(policy: str, case: dict) -> list[str]:
    if policy == "SOURCE_ONLY": return []
    if policy == "GENERIC": return ["generic"]
    if policy == "COUNTEREXAMPLE":
        # Risk-ranked first scenario is a frozen task-family mapping. This test
        # uses a single scenario per vignette; it is not a learned selector.
        return [case["scenario"]]
    if policy == "CHECKLIST": return [s["id"] for s in SCENARIOS]
    raise ValueError(policy)

def respondent(case: dict, scenario_id: str, frozen_revision: int) -> tuple[str, str | None]:
    if case.get("role") is None: return ("RESPONDENT_ABSENT", None)
    if case["privacy"] == "restricted": return ("PRIVACY_BLOCKED", None)
    answer_revision = case.get("answer_revision", case["revision"])
    if frozen_revision != answer_revision: return ("STALE_QUESTION", None)
    if case.get("answer") == "NO_ANSWER": return ("NO_ANSWER", None)
    bad = case.get("unauthorized_answer")
    if bad and bad["role"] != case["role"]:
        # An unauthorized response is retained as evidence but cannot revise.
        return ("UNAUTHORIZED_RESPONDENT", None)
    if scenario_id == "generic":
        return ("ANSWERED", case.get("hidden") if case.get("hidden") not in (None,"no_constraint") else None)
    if scenario_id != case["scenario"]: return ("NO_MATCH", None)
    if case["hidden"] == "no_constraint": return ("CONFIRMED_NO_CONSTRAINT", None)
    return ("CONFIRMED_FORBIDDEN", case["hidden"])

def run():
    rows=[]
    for case in CASES:
        for policy in POLICIES:
            qids=ask_ids(policy,case); clauses=[]; events=[]
            if case["source_clause"]:
                clauses.append({"clause":case["source_clause"],"provenance":"SOURCE","source_revision":case["revision"]})
            for qid in qids:
                status,clause=respondent(case,qid,case["revision"])
                events.append({"question_id":qid,"status":status,"role":case["role"],"revision":case["revision"]})
                if status == "CONFIRMED_FORBIDDEN" and clause != case["source_clause"]:
                    clauses.append({"clause":clause,"provenance":"RESPONDENT_CONFIRMED","question_id":qid,
                                    "role":case["role"],"revision":case["revision"]})
            # Exact source-clause transformation + no action authority.
            source_ok=(not case["source_clause"] or any(c["clause"]==case["source_clause"] and c["provenance"]=="SOURCE" for c in clauses))
            discovered={c["clause"] for c in clauses if c["provenance"]=="RESPONDENT_CONFIRMED"}
            hidden_credit=(case["hidden"] in discovered and case["source_clause"] is None)
            invented=any(c["provenance"]=="RESPONDENT_CONFIRMED" and c["clause"]!=case["hidden"] for c in clauses)
            unauthorized_mutation=any(e["status"] in {"RESPONDENT_ABSENT","PRIVACY_BLOCKED","STALE_QUESTION","NO_ANSWER","UNAUTHORIZED_RESPONDENT"} and any(c.get("question_id")==e["question_id"] for c in clauses) for e in events)
            rows.append({"case_id":case["id"],"policy":policy,"questions":events,"question_count":len(events),
                         "clauses":clauses,"source_clause_preserved":source_ok,"hidden_constraint_credit":hidden_credit,
                         "invented_clause":invented,"unsafe_revision":unauthorized_mutation,
                         "action_authority_minted":False,"unknown_if_unresolved":bool(case["hidden"] not in discovered and case["source_clause"] is None)})
    summary={}
    for p in POLICIES:
        rr=[r for r in rows if r["policy"]==p]
        summary[p]={"vignettes":len(rr),"hidden_constraint_credits":sum(r["hidden_constraint_credit"] for r in rr),
                    "source_clauses_preserved":sum(r["source_clause_preserved"] for r in rr),
                    "questions":sum(r["question_count"] for r in rr),"invented_clauses":sum(r["invented_clause"] for r in rr),
                    "unsafe_revisions":sum(r["unsafe_revision"] for r in rr),"authority_mints":sum(r["action_authority_minted"] for r in rr)}
    result={"schema":"issue6380-t0-v1","disposition":"CANDIDATE_COMPLETE_PENDING_AUDIT",
            "case_count":len(CASES),"policies":list(POLICIES),"row_count":len(rows),"summary":summary,"rows":rows,
            "scope":"finite scripted no-model method fixture; no human elicitation, completeness, consent, GUI, or safety claim"}
    data=(json.dumps(result,sort_keys=True,indent=2)+"\n").encode()
    (ROOT/"candidate.json").write_bytes(data)
    print(json.dumps({"rows":len(rows),"summary":summary,"sha256":hashlib.sha256(data).hexdigest()},sort_keys=True))

if __name__=="__main__": run()
