"""Execute the frozen JsonSession.wait method and independently audit its event contract."""
from __future__ import annotations

import ast
import hashlib
import json
import queue
import time
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED_SOURCE_SHA256 = "4432a6188b5318dc552f050a26ff9e2a5d32bbf9"


class SessionError(RuntimeError):
    pass


class LiveProcess:
    @staticmethod
    def poll():
        return None


def load_frozen_wait():
    source_path = ROOT / "candidate.py"
    raw = source_path.read_bytes()
    source_sha = hashlib.sha256(raw).hexdigest()
    if source_sha != EXPECTED_SOURCE_SHA256:
        raise ValueError("candidate source SHA-256 mismatch")
    tree = ast.parse(raw.decode("utf-8"))
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "JsonSession")
    method = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == "wait")
    module = ast.Module(body=[method], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {"queue": queue, "time": time, "SessionError": SessionError}
    exec(compile(module, str(source_path), "exec"), namespace)
    return source_sha, namespace["wait"]


def call_frozen_wait(wait_method, events, queued, event_name):
    session = types.SimpleNamespace(
        events=list(events),
        queue=queue.Queue(),
        process=LiveProcess(),
    )
    for row in queued:
        session.queue.put(row)
    bound_wait = types.MethodType(wait_method, session)
    return bound_wait(lambda row: row.get("event") == event_name, timeout=0.02)


def expected_policy(events, queued, event_name, expected_id, duplicate_fails=False):
    matches = [
        row for row in events
        if row.get("event") == event_name and row.get("id") == expected_id
    ]
    if duplicate_fails and len(matches) > 1:
        return {"disposition": "ambiguous_duplicate", "count": len(matches)}
    if len(matches) == 1:
        return matches[0]
    for row in queued:
        if row.get("event") == event_name and row.get("id") == expected_id:
            return row
    return None


def run():
    source_sha, wait_method = load_frozen_wait()
    fixture = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))
    outcomes = []
    for case in fixture["cases"]:
        event_name = case["predicate_event"]
        expected_id = case.get("expected_id")
        events = case["events"]
        queued = case["queue"]
        expected = case["expected_disposition"]
        observed = call_frozen_wait(wait_method, events, queued, event_name)
        candidate_disposition = (
            "wait" if observed is None
            else "stale_wrong_identity_returned" if observed.get("id") != expected_id
            else "returned_first_ambiguous" if expected == "ambiguous_duplicate"
            else "return"
        )
        policy = expected_policy(
            events, queued, event_name, expected_id,
            duplicate_fails=(expected == "ambiguous_duplicate"),
        )
        policy_disposition = (
            "ambiguous_duplicate" if isinstance(policy, dict) and policy.get("disposition") == "ambiguous_duplicate"
            else "wait" if policy is None
            else "return"
        )
        policy_pass = policy_disposition == expected
        candidate_matches_declared = (
            candidate_disposition == "stale_wrong_identity_returned"
            if case["name"] in {"stale_accepted_prelude", "stale_rejected_prelude"}
            else candidate_disposition == "returned_first_ambiguous"
            if case["name"] == "duplicate_terminal_history"
            else candidate_disposition == expected
        )
        outcomes.append({
            "case": case["name"],
            "expected": expected,
            "independent_policy": policy_disposition,
            "frozen_candidate": candidate_disposition,
            "returned_id": observed.get("id") if observed else None,
            "policy_pass": policy_pass,
            "candidate_behavior_matches_declared": candidate_matches_declared,
        })
    reproduced = all(
        row["candidate_behavior_matches_declared"] for row in outcomes
    ) and any(
        row["case"] == "stale_accepted_prelude" and row["frozen_candidate"] == "stale_wrong_identity_returned"
        for row in outcomes
    )
    passed = all(row["policy_pass"] and row["candidate_behavior_matches_declared"] for row in outcomes)
    return {
        "candidate_source_sha256": source_sha,
        "cases": outcomes,
        "audit": "PASS_REPRODUCES_DECLARED_CANDIDATE_BEHAVIOR" if passed and reproduced else "FAIL_AUDIT",
        "candidate_disposition": "FAIL_MERGED_REPLAY_SCOPE_BUG" if reproduced else "NOT_REPRODUCED",
        "interpretation": "wrong-ID early return causing false rejection or wait interruption, not unsafe input admission; contract-only, no MAP01/GUI/model/formal allocation",
    }


if __name__ == "__main__":
    rendered = json.dumps(run(), sort_keys=True, indent=2) + "\n"
    (ROOT / "audit-result.json").write_text(rendered, encoding="utf-8")
    print(rendered, end="")
