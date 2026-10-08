"""Separate raw-only integrity and invariant auditor for the T2 run."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parent
RAW = ROOT / "results" / "t2-01" / "raw.json"
OUT = ROOT / "results" / "t2-01" / "AUDIT.json"
EXPECTED_POLICIES = {"quota", "siphon", "banker", "global_lock"}


def _has_cycle(graph):
    finished = set()
    for start in graph:
        stack = [(start, iter(graph[start]), {start})]
        while stack:
            node, children, path = stack[-1]
            child = next(children, None)
            if child is None:
                finished.add(node)
                stack.pop()
                continue
            if child in path:
                return True
            if child not in finished:
                stack.append((child, iter(graph.get(child, ())), path | {child}))
    return False


def audit(raw):
    errors = []
    if raw.get("schema") != "safe-state-admission-t2-raw-v1":
        errors.append("schema")
    if set(raw.get("policies", [])) != EXPECTED_POLICIES:
        errors.append("policy_inventory")
    rows = raw.get("rows")
    if not isinstance(rows, list) or len(rows) != 24:
        return ["row_count" if isinstance(rows, list) else "rows_type"]
    counts = Counter((r.get("scenario"), r.get("policy")) for r in rows)
    if any(n != 1 for n in counts.values()) or len(counts) != 24:
        errors.append("duplicate_or_missing_cell")
    for index, row in enumerate(rows):
        prefix = f"row:{index}"
        graph = row.get("terminal_wait_graph")
        if not isinstance(graph, dict) or _has_cycle(graph) != bool(row.get("metrics", {}).get("unrecovered_deadlocks")):
            errors.append(f"{prefix}:terminal_cycle_mismatch")
        if row.get("policy") == "banker":
            for event in row.get("event_log", []):
                if event.get("kind") == "grant" and event.get("witness") is None:
                    errors.append(f"{prefix}:banker_grant_without_witness")
                if event.get("kind") == "abort" and event.get("reason") == "declared_maximum_claim_exceeded":
                    if row.get("metrics", {}).get("claim_expansion_invalidations") != 1:
                        errors.append(f"{prefix}:claim_invalidation_count")
        for resource, generation in enumerate(row.get("resource_generation", [])):
            if generation:
                for event in row.get("event_log", []):
                    if event.get("kind") == "grant" and event.get("resource") == resource:
                        later_fault = any(e.get("kind") == "shared_fault" and e.get("resource") == resource
                                          and e.get("generation", 0) > 0 for e in row["event_log"])
                        if later_fault:
                            idx = row["event_log"].index(event)
                            if any(e.get("kind") == "grant" and e.get("resource") == resource
                                   and row["event_log"].index(e) > idx
                                   and row["event_log"].index(e) < next(i for i, x in enumerate(row["event_log"])
                                       if x.get("kind") == "shared_fault" and x.get("resource") == resource)
                                   for e in row["event_log"]):
                                errors.append(f"{prefix}:stale_generation_grant")
    return errors


def main():
    if not RAW.is_file() or OUT.exists():
        raise SystemExit("raw missing or audit output already exists")
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    errors = audit(raw)
    result = {"schema": "safe-state-admission-t2-audit-v1",
              "status": "PASS" if not errors else "FAIL",
              "row_count": len(raw.get("rows", [])), "errors": errors}
    OUT.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
                   encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
