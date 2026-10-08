"""Second-process recomputation for the frozen Issue #3349 contract receipts."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import queue
import time
import types
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SessionError(RuntimeError):
    pass


class LiveProcess:
    @staticmethod
    def poll():
        return None


def load_wait(candidate: Path):
    raw = candidate.read_bytes()
    if sha256(candidate) != "4e700b05c60626e73070eb6f5883d9341c8b1374996d45f08e5766fc6cb0f463":
        raise ValueError("frozen candidate source digest mismatch")
    tree = ast.parse(raw.decode("utf-8"))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "JsonSession")
    method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "wait")
    module = ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[]))
    scope = {"queue": queue, "time": time, "SessionError": SessionError}
    exec(compile(module, str(candidate), "exec"), scope)
    return scope["wait"]


def invoke(wait, retained, queued, event_name):
    session = types.SimpleNamespace(events=list(retained), queue=queue.Queue(), process=LiveProcess())
    for row in queued:
        session.queue.put(row)
    try:
        return types.MethodType(wait, session)(lambda r: r.get("event") == event_name, timeout=0.01)
    except TimeoutError:
        return None


def policy(events, queued, event_name, expected_id, duplicate):
    matches = [r for r in events if r.get("event") == event_name and r.get("id") == expected_id]
    if duplicate and len(matches) > 1:
        return "ambiguous_duplicate"
    if len(matches) == 1:
        return "return"
    return "return" if any(r.get("event") == event_name and r.get("id") == expected_id for r in queued) else "wait"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--result", type=Path, required=True)
    ap.add_argument("--cases", type=Path, default=Path("/study/cases.json"))
    ap.add_argument("--candidate", type=Path, default=Path("/study/candidate.py"))
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    receipt = json.loads(a.result.read_text(encoding="utf-8"))
    fixture = json.loads(a.cases.read_text(encoding="utf-8"))
    wait = load_wait(a.candidate)
    observed = []
    for case in fixture["cases"]:
        row = invoke(wait, case["events"], case["queue"], case["predicate_event"])
        exp_id = case["expected_id"]
        candidate_disposition = (
            "wait" if row is None else "stale_wrong_identity_returned" if row.get("id") != exp_id
            else "returned_first_ambiguous" if case["expected_disposition"] == "ambiguous_duplicate"
            else "return"
        )
        policy_disposition = policy(
            case["events"], case["queue"], case["predicate_event"], exp_id,
            case["expected_disposition"] == "ambiguous_duplicate",
        )
        observed.append({
            "case": case["name"],
            "expected": case["expected_disposition"],
            "candidate": candidate_disposition,
            "policy": policy_disposition,
            "candidate_matches_declared": candidate_disposition == case["expected_candidate_behavior"],
            "policy_matches_declared": policy_disposition == case["expected_disposition"],
        })
    source_sha = sha256(a.candidate)
    valid = (
        receipt.get("candidate_source_sha256") == source_sha
        and len(observed) == 7
        and all(r["candidate_matches_declared"] and r["policy_matches_declared"] for r in observed)
        and receipt.get("candidate_disposition") == "FAIL_MERGED_REPLAY_SCOPE_BUG"
        and receipt.get("audit") == "PASS_REPRODUCES_DECLARED_CANDIDATE_BEHAVIOR"
        and [r["case"] for r in receipt.get("cases", [])] == [r["case"] for r in observed]
        and all(
            x.get("frozen_candidate") == y["candidate"]
            and x.get("independent_policy") == y["policy"]
            for x, y in zip(receipt["cases"], observed)
        )
    )
    result = {
        "status": "PASS_INDEPENDENT_REPLAY_CONTRACT_AUDIT" if valid else "FAIL_INDEPENDENT_REPLAY_CONTRACT_AUDIT",
        "candidate_source_sha256": source_sha,
        "formal_result_sha256": sha256(a.result),
        "case_count": len(observed),
        "recomputed_cases": observed,
        "errors": [] if valid else ["independent recomputation differs from frozen source, formal receipt, or Issue contract"],
    }
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True, indent=2))
    if not valid:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
