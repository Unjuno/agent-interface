"""Verify that the independent auditor rejects five corrupted raw matrices."""

import json
import pathlib
import subprocess
import sys
import tempfile


def main(raw_path):
    source = [json.loads(line) for line in pathlib.Path(raw_path).read_text().splitlines() if line]
    controls = {}

    duplicate = source + [source[0]]
    controls["duplicate_cell"] = duplicate
    controls["missing_cell"] = source[:-1]
    changed = [dict(row) for row in source]
    changed[0]["decision"] = "FAIL"
    controls["decision_flip"] = changed
    changed_events = json.loads(json.dumps(source))
    changed_events[2]["events"] = changed_events[2]["events"][:2]
    controls["erase_overflow_cause"] = changed_events
    changed_overflow = json.loads(json.dumps(source))
    changed_overflow[2]["overflow"] = False
    controls["false_no_overflow"] = changed_overflow

    audit_path = pathlib.Path(__file__).with_name("audit.py")
    results = {}
    with tempfile.TemporaryDirectory(prefix="5413-corruption-") as temp_dir:
        for name, rows in controls.items():
            candidate = pathlib.Path(temp_dir) / f"{name}.jsonl"
            candidate.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))
            completed = subprocess.run(
                [sys.executable, str(audit_path), str(candidate)],
                capture_output=True,
                text=True,
                check=False,
            )
            results[name] = {"rejected": completed.returncode != 0, "returncode": completed.returncode}
    failures = [name for name, result in results.items() if not result["rejected"]]
    print(json.dumps({"controls": results, "rejected": len(results) - len(failures), "total": len(results), "failures": failures}, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
