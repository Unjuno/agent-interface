"""Independent raw-only audit; imports neither reducer nor experiment."""
from __future__ import annotations
import argparse
import copy
import csv
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HEADER = ["case", "order", "prefix", "final", "late", "naive", "authority", "rejected"]


def batch(events: list) -> tuple[str, int]:
    required = {"target": "CURRENT", "effect": "VERIFIED_EFFECT"}
    roles = {**required, "diagnostic": "CURRENT"}
    fields = {"rid", "check", "subject", "session", "decision", "epoch", "role", "value"}
    buckets: dict[str, list[dict]] = {}
    broken = False
    rejected = 0
    for item in events:
        if not isinstance(item, dict) or set(item) != fields:
            broken = True
            continue
        if type(item["epoch"]) != int or not all(type(item[k]) == str and 0 < len(item[k]) <= 128 for k in fields if k != "epoch"):
            broken = True
            continue
        if item["check"] not in roles or item["role"] not in ("CURRENT", "VERIFIED_EFFECT", "HISTORICAL", "PREDICTED") or item["value"] not in ("PASS", "FAIL", "UNKNOWN", "TIMEOUT"):
            broken = True
            continue
        if item["session"] != "session-vj01" or item["decision"] != "decision-vj01" or item["epoch"] != 7 or item["subject"] != item["check"]:
            rejected += 1
            continue
        buckets.setdefault(item["rid"], []).append(item)
    answers = {k: [] for k in roles}
    for items in buckets.values():
        serialized = {json.dumps(item, sort_keys=True) for item in items}
        if len(serialized) > 1:
            broken = True
        elif items[0]["role"] == roles[items[0]["check"]]:
            answers[items[0]["check"]].append(items[0]["value"])
    for check in required:
        if "FAIL" in answers[check] and "PASS" not in answers[check]:
            return "F", rejected
    if broken or any("PASS" in a and "FAIL" in a for a in answers.values()):
        return "U", rejected
    if all(set(answers[k]) == {"PASS"} for k in required):
        return "P", rejected
    return "U", rejected


def matrix_event(index: int, code: int) -> dict:
    check = ["target", "effect", "diagnostic"][index]
    role = "VERIFIED_EFFECT" if index == 1 else "CURRENT"
    statuses = {1: "PASS", 2: "FAIL", 3: "UNKNOWN", 4: "TIMEOUT"}
    if code == 5:
        role = "HISTORICAL"
    elif code == 6:
        role = "PREDICTED"
    elif code == 7:
        role = "CURRENT" if index == 1 else "VERIFIED_EFFECT"
    return {"rid": check, "check": check, "subject": check, "session": "session-vj01",
            "decision": "decision-vj01", "epoch": 7, "role": role, "value": statuses.get(code, "PASS")}


def specifications():
    # Separate enumeration and event construction from the producer.
    for number in range(512):
        codes = [number // 64, (number // 8) % 8, number % 8]
        yield "M" + "".join(str(n) for n in codes), [matrix_event(i, c) for i, c in enumerate(codes) if c], None
    for number, spec in enumerate(json.loads((ROOT / "DIRECTED.json").read_text())):
        yield "D%02d" % number, spec["events"], spec["expected"]


def expected_rows():
    for name, events, declared in specifications():
        for indices in itertools.permutations(range(len(events))):
            order = [events[i] for i in indices]
            final, rejected = batch(order)
            if declared is not None and final != declared:
                raise ValueError("DIRECTED_CONTRACT_MISMATCH:" + name)
            prefix = "".join(batch(order[:i])[0] for i in range(len(order)+1))
            last = order[-1] if order and isinstance(order[-1], dict) else {}
            naive = "P" if last.get("value") == "PASS" else "F" if last.get("value") == "FAIL" else "U"
            yield dict(case=name, order="".join(str(i) for i in indices) or "-", prefix=prefix,
                       final=final, late=final * 3, naive=naive, authority="0", rejected=str(rejected))


def check_rows(rows: list[dict]) -> list[str]:
    for i, (row, expected) in enumerate(itertools.zip_longest(rows, expected_rows())):
        if row != expected:
            return ["ROW_MISMATCH:%d" % i]
    return []


def controls(rows: list[dict]) -> dict[str, bool]:
    tests = {}
    for name in ("drop", "duplicate", "swap", "case", "order", "prefix", "final", "late", "naive", "authority", "rejected", "missing_field"):
        changed = copy.deepcopy(rows)
        if name == "drop":
            changed.pop(0)
        elif name == "duplicate":
            changed.insert(0, copy.deepcopy(changed[0]))
        elif name == "swap":
            changed[0], changed[1] = changed[1], changed[0]
        elif name == "missing_field":
            del changed[0]["final"]
        else:
            replacements = {"case": "M999", "order": "9", "prefix": "P", "final": "P", "late": "PPP", "naive": "P", "authority": "1", "rejected": "999"}
            changed[0][name] = replacements[name]
        tests[name] = changed != rows and bool(check_rows(changed))
    return tests


def audit(output: Path) -> dict:
    errors = []
    freeze_bytes = (ROOT / "FREEZE.json").read_bytes()
    freeze = json.loads(freeze_bytes)
    for name, record in freeze["files"].items():
        data = (ROOT / name).read_bytes()
        if len(data) != record["bytes"] or hashlib.sha256(data).hexdigest() != record["sha256"]:
            errors.append("SOURCE:" + name)
    raw = (output / "raw.csv").read_bytes()
    start = json.loads((output / "RUN_STARTED.json").read_text())
    finish = json.loads((output / "RUN_FINISHED.json").read_text())
    if start["freeze_sha256"] != hashlib.sha256(freeze_bytes).hexdigest() or start["allocation"] != freeze["allocation"] or finish["allocation"] != freeze["allocation"]:
        errors.append("ALLOCATION_OR_FREEZE")
    if start["authority"] is not False or finish["authority"] is not False or finish["retries"] != 0 or finish["formal_invocations"] != 1:
        errors.append("EXECUTION_SCOPE")
    if finish["model_calls"] != 0 or finish["gui_calls"] != 0:
        errors.append("UNDECLARED_EXTERNAL_CALL")
    if start["start_ns"] > finish["end_ns"]:
        errors.append("PROCESS_CLOCK")
    if len(raw) != finish["raw_bytes"] or hashlib.sha256(raw).hexdigest() != finish["raw_sha256"]:
        errors.append("RAW_IDENTITY")
    with (output / "raw.csv").open(newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != HEADER:
            errors.append("CSV_SCHEMA")
        rows = list(reader)
    if len(rows) != finish["rows"] or len(rows) != freeze["schedules"]:
        errors.append("ROW_COUNT")
    errors.extend(check_rows(rows))
    mutations = controls(rows) if not errors else {}
    if len(mutations) != 12 or not all(mutations.values()):
        errors.append("CORRUPTION_CONTROLS")
    totals = {v: sum(r["final"] == v for r in rows) for v in "PFU"} if not errors else None
    result = dict(disposition="PASS_FINITE_EVIDENCE_REDUCTION_SCOPED" if not errors else "HOLD_SOURCE_OR_AUDIT",
                  errors=errors, schedules=len(rows), cases=len({r["case"] for r in rows}),
                  verdict_counts=totals, corruption_controls=mutations,
                  naive_false_pass=sum(r["naive"] == "P" and r["final"] != "P" for r in rows) if not errors else None,
                  provisional_pass_then_nonpass=sum("P" in r["prefix"] and r["final"] != "P" for r in rows) if not errors else None,
                  raw_sha256=hashlib.sha256(raw).hexdigest(), authority=False,
                  scope="finite synthetic evidence contract; not verifier truth, latency, task or product safety")
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("output", type=Path)
    p.add_argument("--write", type=Path, required=True)
    args = p.parse_args()
    result = audit(args.output)
    with args.write.open("x") as f:
        json.dump(result, f, indent=2); f.write("\n")
    print(json.dumps(result))
    raise SystemExit(bool(result["errors"]))
