#!/usr/bin/env python3
"""Blind measurement pass over authored first-pass event ledgers."""
import argparse
import hashlib
import json
from pathlib import Path


def summarize_reviewer(reviewer, required_sources, evidence_pool, per_reviewer_cap):
    requests = reviewer.get("requests", [])
    events = reviewer.get("tool_events", [])
    exact_pairs = sum(1 for q in requests if any(
        e.get("request_id") == q.get("request_id")
        and e.get("context_sha256") == q.get("context_sha256")
        and e.get("source_id") == q.get("source_id") for e in events))
    return {
        "reviewer_id": reviewer.get("reviewer_id"),
        "request_count": len(requests),
        "tool_event_count": len(events),
        "matched_request_event_count": exact_pairs,
        "all_context_hashes_valid": all(
            hashlib.sha256(q.get("context", "").encode()).hexdigest() == q.get("context_sha256")
            for q in requests),
        "all_requests_within_cap": len(requests) <= per_reviewer_cap,
        "verdict": reviewer.get("verdict"),
        "commit_seq": reviewer.get("commit_seq"),
        "peer_content_visible_before_commit": reviewer.get("peer_content_visible_before_commit"),
        "first_peer_content_seq": reviewer.get("first_peer_content_seq"),
        "peer_reviewer_id": reviewer.get("peer_reviewer_id"),
        "peer_verdict_digest": reviewer.get("peer_verdict_digest"),
        "requests": requests,
        "tool_events": events,
        "requested_required_source_ids": sorted({q.get("source_id") for q in requests} & set(required_sources)),
        "returned_required_source_ids": sorted({e.get("source_id") for e in events} & set(required_sources)),
        "out_of_pool_source_ids": sorted(({q.get("source_id") for q in requests} | {e.get("source_id") for e in events}) - set(evidence_pool)),
    }


def summarize(attempt):
    return {
        "case_id": attempt.get("case_id"),
        "condition": attempt.get("condition"),
        "assigned": attempt.get("assigned"),
        "actual_reviewers": attempt.get("actual_reviewers"),
        "per_reviewer_cap": attempt.get("per_reviewer_cap"),
        "reducer_policy_id": attempt.get("reducer_policy_id"),
        "roster_fact_disclosed": attempt.get("roster_fact_disclosed"),
        "individual_accounting_disclosed": attempt.get("individual_accounting_disclosed"),
        "required_sources": attempt.get("required_sources"),
        "evidence_pool": attempt.get("evidence_pool"),
        "truth_ref": attempt.get("truth_ref"),
        "reviewers": [summarize_reviewer(r, attempt.get("required_sources", []), attempt.get("evidence_pool", []), attempt.get("per_reviewer_cap", -1)) for r in attempt.get("reviewers", [])],
    }


def run(data):
    return {"protocol": "issue-7059-t0-a01-v1", "attempt_count": len(data["cases"]),
            "attempts": [summarize(a) for a in data["cases"]]}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    output = run(json.loads(Path(args.input).read_text()))
    Path(args.output).write_text(json.dumps(output, sort_keys=True, indent=2) + "\n")
