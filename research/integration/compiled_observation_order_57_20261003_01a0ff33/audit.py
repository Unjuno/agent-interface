"""Raw-only identity checks and independent order-rule comparison."""
import copy
import hashlib
import json
from pathlib import Path

from oracle import expected, legacy_expected, same_json, summarize

HERE = Path(__file__).resolve().parent


def check(rows, freeze, cases, freeze_hash):
    errors = []
    expected_cases = {case["id"]: case for case in cases}
    seen = set()
    counts = {source: {"rows": 0, "order_rule_mismatches": 0,
                       "task_succeeded": 0} for source in ("baseline", "candidate")}
    for row in rows:
        try:
            source = row["source"]
            case_id = row["case"]["id"]
            identity = (source, case_id)
            assert identity not in seen and source in counts
            seen.add(identity)
            case = expected_cases[case_id]
            assert same_json(row["case"], case)
            assert row["freeze_sha256"] == freeze_hash
            assert row["source_sha256"] == freeze["files"][f"{source}-source/compiled_gui.py"]["sha256"]
            assert row["input_unchanged"] is True
            calls = row["calls"]
            assert set(calls) == {"observe", "admit", "execute", "verify_effect"}
            assert all(type(value) is list for value in calls.values())
            assert len(calls["execute"]) <= 2
            assert len(calls["verify_effect"]) <= len(calls["execute"])
            assert len(calls["admit"]) == len(calls["execute"])
            for i, payload in enumerate(calls["execute"]):
                assert same_json(payload, {
                    "action": ("enter", "save")[i],
                    "operation": ("enter", "save")[i], "authorization": "one-use",
                    "expected_sequence": i + 1, "valid_until_ns": 1_000_000})
            observe_records = [event for event in row["timeline"] if event["callback"] == "observe"]
            execute_records = [event for event in row["timeline"] if event["callback"] == "execute"]
            assert len(observe_records) == len(calls["observe"])
            assert len(execute_records) == len(calls["execute"])
            for i, event in enumerate(observe_records):
                assert same_json(event, {"callback": "observe", "returned_ns": (10, 100, 200)[i],
                    "response": {"sequence": i + 1, "captured_ns": case["captures"][i],
                    "surface": "form", "predicates": {"phase": i},
                    "evidence_ref": f"frame-{i + 1}", "evidence_digest": f"digest-{i + 1}"}})
            for i, event in enumerate(execute_records):
                assert same_json(event, {"callback": "execute", "returned_ns": (20, 110)[i]})
            result = row["result"]
            actual = summarize(row)
            if result["kind"] == "receipt":
                receipt = result["receipt"]
                assert type(receipt["completed_transitions"]) is int
                assert receipt["completed_transitions"] == len(calls["execute"])
                assert type(receipt["frontier_model_resumptions"]) is int
                assert receipt["frontier_model_resumptions"] == 0
                assert len(receipt["transitions"]) == len(calls["execute"])
                assert receipt["latest_evidence_ref"] == (
                    receipt["observations"][-1]["evidence_ref"] if receipt["observations"] else None)
                assert all(transition["release_verified"] is True for transition in receipt["transitions"])
                assert same_json(receipt["critical_events"][-1], {
                    "event": "runtime_finished", "outcome": receipt["outcome"],
                    "reason": receipt["reason"], "completed_transitions": len(calls["execute"])})
            else:
                assert result["kind"] == "exception"
                assert type(result["exception_type"]) is str and type(result["message"]) is str
            assert same_json(actual, legacy_expected(case) if source == "baseline" else expected(case))
            counts[source]["rows"] += 1
            counts[source]["order_rule_mismatches"] += not same_json(actual, expected(case))
            counts[source]["task_succeeded"] += actual.get("outcome") == "TASK_SUCCEEDED"
        except (AssertionError, KeyError, IndexError, TypeError) as error:
            errors.append({"row_index": len(seen) - 1, "error": type(error).__name__})
    required = {(source, case_id) for source in counts for case_id in expected_cases}
    if seen != required or len(rows) != len(required):
        errors.append({"error": "exact source/case coverage required"})
    return {"errors": errors, "counts": counts}


def main():
    freeze_bytes = (HERE / "FREEZE.json").read_bytes()
    freeze = json.loads(freeze_bytes)
    for name, record in freeze["files"].items():
        assert hashlib.sha256((HERE / name).read_bytes()).hexdigest() == record["sha256"], name
    cases = json.loads((HERE / "cases.json").read_bytes())
    rows = [json.loads(line) for line in (HERE / "raw.jsonl").read_text(encoding="utf-8").splitlines()]
    freeze_hash = hashlib.sha256(freeze_bytes).hexdigest()
    result = check(rows, freeze, cases, freeze_hash)
    expected_counts = freeze["decision"]["expected_counts"]
    controls = []
    witnesses = []
    for name in ("drop_row", "duplicate_case", "source_hash", "capture_type",
                 "completed_type", "execute_sequence_type", "latest_reference",
                 "execution_clock_type"):
        changed = copy.deepcopy(rows)
        if name == "drop_row":
            changed.pop()
        elif name == "duplicate_case":
            changed[-1] = copy.deepcopy(changed[-2])
        elif name == "source_hash":
            changed[0]["source_sha256"] = "0" * 64
        elif name == "capture_type":
            changed[0]["case"]["captures"][0] = False
        elif name == "completed_type":
            changed[0]["result"]["receipt"]["completed_transitions"] = 2.0
        elif name == "execute_sequence_type":
            changed[0]["calls"]["execute"][0]["expected_sequence"] = True
        elif name == "latest_reference":
            changed[0]["result"]["receipt"]["latest_evidence_ref"] = "altered"
        else:
            next(event for event in changed[0]["timeline"]
                 if event["callback"] == "execute")["returned_ns"] = 20.0
        outcome = check(changed, freeze, cases, freeze_hash)
        assert changed != rows or not same_json(changed, rows), name
        assert outcome["errors"], name
        controls.append({"name": name, "rejected": True,
                         "error_count": len(outcome["errors"])})
        affected = len(rows) - 1 if name in ("drop_row", "duplicate_case") else 0
        witnesses.append({"name": name, "row_index": affected,
                          "original": rows[affected],
                          "changed": changed[affected] if affected < len(changed) else None})
    witness_path = HERE / "CONTROLS.json"
    witness_bytes = (json.dumps(witnesses, sort_keys=True, indent=2, ensure_ascii=True,
                               allow_nan=False) + "\n").encode("utf-8")
    if witness_path.exists():
        assert witness_path.read_bytes() == witness_bytes
    else:
        with witness_path.open("xb") as output:
            output.write(witness_bytes)
    result.update(raw_sha256=hashlib.sha256((HERE / "raw.jsonl").read_bytes()).hexdigest(),
                  freeze_sha256=freeze_hash, controls=controls,
                  disposition="PASS_ORDER_GUARD_ENGINEERING_SCOPED" if
                  not result["errors"] and same_json(result["counts"], expected_counts)
                  else "FAIL_ORDER_GUARD_ENGINEERING_SCOPED")
    print(json.dumps(result, sort_keys=True, indent=2))
    if result["disposition"].startswith("FAIL"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
