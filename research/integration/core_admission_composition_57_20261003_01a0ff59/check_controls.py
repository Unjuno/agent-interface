"""Directed source mutations and in-memory raw corruptions; original bytes stay intact."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import types
import audit_matrix as auditor
import run_matrix as runner

ROOT = Path(__file__).resolve().parent

def module_from_text(name, text):
    module = types.ModuleType(name)
    sys.modules[name] = module
    exec(compile(text, name, "exec"), module.__dict__)
    return module

def main():
    cases = auditor.read_gzip(ROOT / "raw/cases.jsonl.gz")
    rows = auditor.read_gzip(ROOT / "raw/results.jsonl.gz")
    control = auditor.verify(cases, rows)
    if control["errors"]:
        raise AssertionError("uncorrupted control fails")
    findings = []
    for mutation in ("missing_row", "duplicate_row", "wrong_input_hash", "bool_to_integer", "case_type_change", "input_mutation"):
        changed_cases, changed_rows = cases, rows
        if mutation == "missing_row":
            changed_rows = rows[:-1]
        elif mutation == "duplicate_row":
            changed_rows = rows + [rows[0]]
        elif mutation == "case_type_change":
            changed_cases = deepcopy(cases)
            changed_cases[0]["evidence"]["current_observation_seq"] = 1.0
        else:
            changed_rows = deepcopy(rows)
            row = next(r for r in changed_rows if r["arm"] == "combined")
            if mutation == "wrong_input_hash":
                row["input_sha256"] = "0" * 64
            elif mutation == "bool_to_integer":
                row["output"]["accepted"] = int(row["output"]["accepted"])
            else:
                row["unchanged"] = False
        result = auditor.verify(changed_cases, changed_rows)
        if not result["errors"]:
            raise AssertionError("undetected raw corruption: " + mutation)
        findings.append({"raw_corruption": mutation, "detected": True, "errors": result["errors"][:3]})
    text = (ROOT / "sources/combined.py").read_text(encoding="utf-8")
    changes = [
        ("delete_now_check", '        _bounded_int(now_ns, "now_ns", 0, 2**63 - 1)\n', "", (0, 0, 3, 0, 0)),
        ("delete_os_string_check", 'isinstance(platform.get("os"), str) and ', "", (3, 0, 0, 0, 0)),
        ("delete_frame_string_check", '    _need(all(isinstance(frame, str) for frame in frames), "coordinate_frames must contain strings")\n', "", (13, 0, 0, 0, 0)),
        ("reject_expiry_equality", 'if now_ns > program["authority"]["expires_at_ns"]:', 'if now_ns >= program["authority"]["expires_at_ns"]:', (0, 0, 1, 0, 0)),
    ]
    for name, old, new, indices in changes:
        if text.count(old) != 1:
            raise AssertionError("mutation target is not unique: " + name)
        case = auditor.reconstructed_case(indices)
        module = module_from_text("mutant_" + name, text.replace(old, new, 1))
        observed = runner.evaluate(module, case)["output"]
        expected = auditor.reference(case)
        if auditor.encoded(observed) == auditor.encoded(expected):
            raise AssertionError("ineffective implementation mutation: " + name)
        findings.append({"source_mutation": name, "case_id": case["id"], "detected": True,
                         "observed": observed, "expected": expected})
    result = {"raw_controls": 6, "source_controls": 4, "all_detected": True, "details": findings}
    (ROOT / "CONTROLS.json").open("xb").write(json.dumps(result, indent=2).encode() + b"\n")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
