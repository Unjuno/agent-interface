#!/usr/bin/env python3
"""Build authored development fixtures. Formal fixture is generated once before freeze."""
import json
import hashlib
from pathlib import Path


HERE = Path(__file__).parent


def pair(case_id, routine_checks, disclosed_checks, routine_verdict, disclosed_verdict,
         truth, expected, complete=True):
    rows = []
    for condition, checks, verdict in (("routine", routine_checks, routine_verdict),
                                        ("disclosed", disclosed_checks, disclosed_verdict)):
        context = (f"Synthetic first-pass context for {case_id}; routine shared task; no peer content is available."
                   if condition == "routine" else
                   f"Synthetic first-pass context for {case_id}; another isolated reviewer is independently checking the same claim; no peer content is available.")
        context_hash = hashlib.sha256(context.encode()).hexdigest()
        reviewers = []
        for reviewer in ("reviewer-A", "reviewer-B"):
            reqs = [{"request_id": f"{case_id}-{condition}-{reviewer}-q{i}", "context": context,
                     "context_sha256": context_hash, "source_id": f"source-{i}", "seq": i * 2}
                    for i in range(checks)]
            tools = [{"request_id": q["request_id"], "context_sha256": q["context_sha256"],
                      "source_id": q["source_id"], "result_id": f"result-{q['request_id']}", "seq": q["seq"] + 1}
                     for q in reqs]
            if not complete and condition == "disclosed" and reviewer == "reviewer-A":
                tools = tools[:-1]
            reviewers.append({"reviewer_id": reviewer, "requests": reqs, "tool_events": tools,
                              "verdict": verdict, "commit_seq": checks * 2,
                              "peer_content_visible_before_commit": False,
                              "first_peer_content_seq": checks * 2 + 1,
                              "peer_reviewer_id": "reviewer-B" if reviewer == "reviewer-A" else "reviewer-A",
                              "peer_verdict_digest": hashlib.sha256(verdict.encode()).hexdigest()})
        rows.append({"case_id": case_id, "condition": condition, "assigned": True,
                     "actual_reviewers": ["reviewer-A", "reviewer-B"], "per_reviewer_cap": 3,
                     "reducer_policy_id": "fixed-two-reviewer-reduction-v1",
                     "roster_fact_disclosed": condition == "disclosed",
                     "individual_accounting_disclosed": False,
                     "evidence_pool": ["source-0", "source-1", "source-2"],
                     "required_sources": ["source-0", "source-1"], "reviewers": reviewers,
                     "truth_ref": case_id})
    truth_row = {"case_id": case_id, "effect_truth": truth, "expected_ledger_class": expected}
    return rows, truth_row


def make_fixture():
    cases = [
        pair("null", 2, 2, "PASS", "PASS", "valid", "NO_MATERIAL_CHANGE"),
        pair("harmful_missed_check", 2, 1, "FAIL", "PASS", "faulty", "HARMFUL_MISSED_CHECK"),
        pair("efficient_fewer_checks", 2, 1, "PASS", "PASS", "valid", "FEWER_CHECKS_SAME_CORRECTNESS"),
        pair("legitimate_unknown", 2, 1, "UNKNOWN", "UNKNOWN", "ambiguous", "UNKNOWN_PRESERVED"),
        pair("missing_tool_log", 2, 2, "FAIL", "PASS", "faulty", "HOLD_MISSING_TOOL_LOG", complete=False),
    ]
    rows, truth = [], []
    for pair_rows, truth_row in cases:
        rows.extend(pair_rows)
        truth.append(truth_row)
    return {"protocol": "issue-7059-t0-a01-v1", "cases": rows, "auditor_truth": truth}


if __name__ == "__main__":
    fixture = make_fixture()
    (HERE / "formal_input.json").write_text(json.dumps({"cases": fixture["cases"]}, indent=2) + "\n")
    (HERE / "auditor_truth.json").write_text(json.dumps({"truth": fixture["auditor_truth"]}, indent=2) + "\n")
