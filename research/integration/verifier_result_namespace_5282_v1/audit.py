"""Independent corpus/raw oracle. Does not import probe or reducer."""
import copy
import hashlib
import itertools
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parent


def oracle(events, namespace):
    names = {"alpha": "target", "beta": "effect", "gamma": "diagnostic", "delta": "target"}
    wanted = {"target": "CURRENT", "effect": "VERIFIED_EFFECT", "diagnostic": "CURRENT"}
    required = {"target", "effect"}
    fields = {"producer", "rid", "check", "subject", "session", "decision", "epoch", "role", "value"}
    buckets = {}
    invalid = False
    for e in events:
        if not isinstance(e, dict) or set(e) != fields:
            invalid = True; continue
        if type(e["epoch"]) is not int or not all(type(e[k]) is str and 0 < len(e[k]) <= 128 for k in fields - {"epoch"}):
            invalid = True; continue
        if len(e["rid"]) > 48 or names.get(e["producer"]) != e["check"] or e["producer"] not in names or e["role"] not in ("CURRENT", "VERIFIED_EFFECT", "HISTORICAL", "PREDICTED") or e["value"] not in ("PASS", "FAIL", "UNKNOWN", "TIMEOUT"):
            invalid = True; continue
        if e["subject"] != e["check"] or e["session"] != "session-vj01" or e["decision"] != "decision-vj01" or e["epoch"] != 7:
            continue
        key = (e["producer"], e["rid"]) if namespace else e["rid"]
        buckets.setdefault(key, []).append((e["check"], e["role"], e["value"]))
    values = {k: set() for k in wanted}
    for records in buckets.values():
        if len(set(records)) != 1:
            invalid = True; continue
        check, role, value = records[0]
        if role == wanted[check]:
            values[check].add(value)
    if any("FAIL" in values[k] and "PASS" not in values[k] for k in required):
        return "F"
    if invalid or any({"PASS", "FAIL"}.issubset(v) for v in values.values()):
        return "U"
    return "P" if all(values[k] == {"PASS"} for k in required) else "U"


def expected():
    for case in json.loads((ROOT / "CASES.json").read_text()):
        for permutation in itertools.permutations(range(len(case["events"]))):
            events = [case["events"][i] for i in permutation]
            row = {"case": case["name"], "order": list(permutation), "events": events}
            for name, namespace in (("bare", False), ("scoped", True)):
                final = oracle(events, namespace)
                row[name] = {"prefix": "".join(oracle(events[:i], namespace) for i in range(len(events)+1)),
                             "final": final, "late": final * 2, "authority": False}
            if row["scoped"]["final"] != case["expected"]:
                raise RuntimeError("HAND_ORACLE_DISAGREEMENT:" + case["name"])
            yield row


def compare(rows):
    for i, (a, b) in enumerate(itertools.zip_longest(rows, expected())):
        if a != b:
            return ["MISMATCH:%d" % i]
    return []


def audit(output):
    freeze = json.loads((ROOT / "FREEZE.json").read_text())
    for n, h in freeze["files"].items():
        b = (ROOT / n).read_bytes()
        assert len(b) == h["bytes"] and hashlib.sha256(b).hexdigest() == h["sha256"], n
    raw = (output / "raw.jsonl").read_bytes()
    summary = json.loads((output / "SUMMARY.json").read_text())
    receipt = json.loads((output.parent / "FORMAL_RECEIPT.json").read_text())
    assert receipt["exit_code"] == 0 and receipt["timeout"] is False
    assert receipt["source_commit"] == freeze["publication_source_commit"]
    assert receipt["start_ns"] <= receipt["end_ns"]
    assert receipt["address_space_limit_bytes"] == 536870912 and receipt["timeout_s"] == 30
    assert summary["sha256"] == hashlib.sha256(raw).hexdigest() and summary["bytes"] == len(raw)
    assert summary["allocation"] == freeze["allocation"] and summary["formal_invocations"] == 1
    assert summary["model_calls"] == summary["gui_calls"] == summary["retries"] == 0
    rows = [json.loads(line) for line in raw.splitlines()]
    errors = compare(rows)
    if len(rows) != freeze["schedules"] or len(rows) != summary["rows"]:
        errors.append("COUNT")
    mutations = {}
    for mode in ("drop", "duplicate", "order", "producer", "local_id", "status", "scoped", "bare", "prefix", "late", "authority", "missing"):
        changed = copy.deepcopy(rows)
        if mode == "drop": changed.pop()
        elif mode == "duplicate": changed.append(copy.deepcopy(changed[-1]))
        elif mode == "order": changed[0]["order"].reverse()
        elif mode == "producer": changed[0]["events"][0]["producer"] = "unknown"
        elif mode == "local_id": changed[0]["events"][0]["rid"] = "other"
        elif mode == "status": changed[0]["events"][0]["value"] = "FAIL"
        elif mode in ("scoped", "bare"): changed[0][mode]["final"] = "U"
        elif mode == "prefix": changed[0]["scoped"]["prefix"] = "U"
        elif mode == "late": changed[0]["scoped"]["late"] = "UU"
        elif mode == "authority": changed[0]["scoped"]["authority"] = True
        else: del changed[0]["scoped"]["final"]
        mutations[mode] = changed != rows and bool(compare(changed))
    if not all(mutations.values()): errors.append("INEFFECTIVE_MUTATION")
    restored = sum(r["bare"]["final"] == "U" and r["scoped"]["final"] == "P" for r in rows)
    if restored == 0: errors.append("NO_DISCRIMINATING_POSITIVE")
    return {"disposition": "PASS_VERIFIER_LOCAL_ID_NAMESPACE_SCOPED" if not errors else "FAIL_OR_HOLD_NAMESPACE",
            "errors": errors, "cases": len({r["case"] for r in rows}), "schedules": len(rows),
            "restored_positive_schedules": restored,
            "restored_failure_schedules": sum(r["bare"]["final"] == "U" and r["scoped"]["final"] == "F" for r in rows),
            "scoped_verdict_counts": {v: sum(r["scoped"]["final"] == v for r in rows) for v in "PFU"},
            "mutations": mutations, "raw_sha256": hashlib.sha256(raw).hexdigest(),
            "authority": False, "model_or_runtime_claim": False}


if __name__ == "__main__":
    result = audit(Path(sys.argv[1]))
    with Path(sys.argv[2]).open("x") as f:
        json.dump(result, f, indent=2); f.write("\n")
    print(json.dumps(result))
    raise SystemExit(bool(result["errors"]))
