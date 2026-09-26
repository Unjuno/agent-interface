"""Twelve effective record corruptions; does not run the validator or matrix."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from audit import audit

HERE = Path(__file__).resolve().parent


def digest(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("records", type=Path)
    args = parser.parse_args()
    data = json.loads(args.records.read_text())
    cases = json.loads((HERE / "cases.json").read_text())
    freeze = json.loads((HERE / "FREEZE.json").read_text())
    baseline = audit(data, cases, freeze)
    if baseline["errors"]:
        raise RuntimeError("controls require a passing baseline")
    rows = []
    names = ["missing_case", "wrong_case_id", "false_valid", "authority", "task_success",
             "wrong_index", "input_changed", "socket_event", "native_import", "wrong_exit",
             "wrong_expansion_count", "source_changed"]
    for name in names:
        changed = deepcopy(data)
        if name == "missing_case":
            changed["rows"].pop()
        elif name == "wrong_case_id":
            changed["rows"][1]["id"] = changed["rows"][0]["id"]
        elif name in {"false_valid", "authority", "task_success", "wrong_index", "wrong_expansion_count"}:
            index = 2 if name == "false_valid" else 8 if name == "wrong_index" else 0
            report = json.loads(changed["rows"][index]["stdout"])
            field, value = {"false_valid": ("static_valid", True), "authority": ("side_effect_authority", True),
                            "task_success": ("task_success", True), "wrong_index": ("source_operation_index", 3),
                            "wrong_expansion_count": ("expanded_operation_count", 42)}[name]
            report[field] = value
            changed["rows"][index]["stdout"] = json.dumps(report) + "\n"
        elif name == "input_changed":
            changed["rows"][0]["input_sha256_after"] = "0" * 64
        elif name == "socket_event":
            changed["rows"][0]["trace"]["events"] = ["socket.__new__"]
        elif name == "native_import":
            changed["rows"][0]["trace"]["native_modules"] = ["Xlib"]
        elif name == "wrong_exit":
            changed["rows"][0]["exit"] = 1
        else:
            key = next(iter(changed["source_hashes_after"]))
            changed["source_hashes_after"][key] = "0" * 64
        result = audit(changed, cases, freeze)
        rows.append({"name": name, "baseline_sha256": digest(data), "changed_sha256": digest(changed),
                     "effective": changed != data, "rejected": bool(result["errors"]), "errors": result["errors"]})
    ok = all(row["effective"] and row["rejected"] for row in rows)
    print(json.dumps({"passed": ok, "controls": rows}, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
