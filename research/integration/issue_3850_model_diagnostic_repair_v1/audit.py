from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    root = Path(sys.argv[1]).resolve()
    cases = json.loads((root / "cases.json").read_text(encoding="utf-8"))
    schema = json.loads((root / "response.schema.json").read_text(encoding="utf-8"))
    by_case = {case["id"]: case for case in cases["cases"]}
    errors: list[str] = []
    rows = []
    seen = set()
    dirs = sorted(path for path in (root / "results" / "formal01").iterdir() if path.is_dir())
    fail(errors, len(dirs) == 8, "expected exactly eight row directories")
    for rowdir in dirs:
        try:
            allocation = json.loads((rowdir / "allocation.json").read_text(encoding="utf-8"))
            events = [json.loads(line) for line in (rowdir / "events.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
            broker = json.loads((rowdir / "broker.json").read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{rowdir.name}: malformed/missing artifact {type(exc).__name__}")
            continue
        rid = allocation.get("request_id")
        fail(errors, isinstance(rid, str) and rid not in seen, f"{rowdir.name}: duplicate/missing request id")
        if isinstance(rid, str):
            seen.add(rid)
        fail(errors, broker.get("request_id") == rid, f"{rowdir.name}: broker identity mismatch")
        fail(errors, broker.get("returncode") == 0, f"{rowdir.name}: broker nonzero")
        messages, turns, failed = [], [], False
        for event in events:
            kind = event.get("type")
            if kind in ("error", "turn.failed"):
                failed = True
            elif kind == "item.completed":
                item = event.get("item")
                if isinstance(item, dict) and item.get("type") == "agent_message":
                    messages.append(item.get("text"))
                elif isinstance(item, dict) and item.get("type") == "error":
                    failed = True
            elif kind == "turn.completed":
                turns.append(event)
        fail(errors, not failed, f"{rowdir.name}: failure event")
        fail(errors, len(messages) == 1, f"{rowdir.name}: assistant message count")
        fail(errors, len(turns) == 1 and isinstance(turns[0].get("usage"), dict), f"{rowdir.name}: completed turn/usage missing")
        if len(turns) != 1 or not isinstance(turns[0].get("usage"), dict):
            continue
        usage = turns[0]["usage"]
        fail(errors, bool(usage) and all(type(v) is int and v >= 0 for v in usage.values()), f"{rowdir.name}: invalid usage")
        response = None
        if len(messages) == 1:
            try:
                response = json.loads(messages[0])
            except Exception:
                errors.append(f"{rowdir.name}: assistant response invalid JSON")
        fail(errors, isinstance(response, dict), f"{rowdir.name}: response not object")
        if isinstance(response, dict):
            fail(errors, set(response) == {"status", "program", "reason"}, f"{rowdir.name}: response fields mismatch")
            fail(errors, response.get("status") in ("READY", "YIELD"), f"{rowdir.name}: status invalid")
        case = by_case.get(allocation.get("case"), {})
        exact = isinstance(response, dict) and response.get("status") == "READY" and response.get("program") == case.get("expected_repair")
        false_ready = isinstance(response, dict) and response.get("status") == "READY" and not exact
        rows.append({"allocation_id": allocation.get("allocation_id"), "case": allocation.get("case"),
                     "rep": allocation.get("rep"), "arm": allocation.get("arm"),
                     "status": response.get("status") if isinstance(response, dict) else None,
                     "exact_repair": exact, "false_ready": false_ready,
                     "response_sha256": sha(rowdir / "events.jsonl"), "usage": usage})
    fail(errors, len(seen) == 8, "request ID cardinality is not eight")
    counts = {arm: sum(1 for row in rows if row["arm"] == arm and row["exact_repair"]) for arm in ("CODE_ONLY", "BOUNDED_DETAIL")}
    if errors:
        decision = "STOP_OR_HOLD_AUDIT_ERRORS"
    elif any(row["false_ready"] and row["arm"] == "BOUNDED_DETAIL" for row in rows) or counts["BOUNDED_DETAIL"] < counts["CODE_ONLY"]:
        decision = "FAIL_DETAIL_HARM"
    elif counts["BOUNDED_DETAIL"] > counts["CODE_ONLY"]:
        decision = "PASS_REPAIR_SIGNAL_SCOPED"
    else:
        decision = "HOLD_NO_DISCRIMINATING_SIGNAL"
    output = {"decision": decision, "errors": errors, "rows": rows,
              "exact_repairs": counts, "n_matched_pairs": 4,
              "scope": "descriptive underpowered static repairability only; no execution, latency, cost, task-success, or product claim"}
    print(json.dumps(output, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
