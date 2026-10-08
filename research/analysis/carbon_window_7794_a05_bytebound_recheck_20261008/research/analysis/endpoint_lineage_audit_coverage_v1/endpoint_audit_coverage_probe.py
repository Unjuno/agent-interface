#!/usr/bin/env python3
"""Adversarial coverage probe for frozen endpoint-lineage T0 auditor v1."""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile
import urllib.request
from fractions import Fraction

OWNER = "Unjuno"
REPO = "agent-interface"
REF = "68a4a983118fbbfaecf875c44fe04fadff3b4bd9"
BASE = f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{REF}/research/analysis/endpoint_lineage_46_t0_v1"
EXPECTED = {
    "fixtures.json": "7ab198820c750b5639058ac5c27d999cb0314e0878d9c3412da7c22e913b9f6a",
    "candidate_stdout.json": "860ac08416ed6420d640391b94f8687ffada433ee63899b618ff1117992f7cd4",
    "audit_independent.py": "31f0700e6274f96f335dc047fc4d60fb0998a93a501f6bf20e1d1432fd23360a",
}


def main() -> None:
    frozen = {}
    for name, expected in EXPECTED.items():
        with urllib.request.urlopen(f"{BASE}/{name}", timeout=30) as response:
            data = response.read()
        observed = hashlib.sha256(data).hexdigest()
        if observed != expected:
            raise SystemExit(f"STOP_SOURCE_HASH_MISMATCH:{name}:{observed}")
        frozen[name] = data

    cases = []
    for label, mutation in (
        ("baseline", None),
        ("wrong_naive_sum", ("naive_sum", ["-900", "900"])),
        ("wrong_ordered_segment_interval", ("segment", ["-500", "500"])),
    ):
        with tempfile.TemporaryDirectory(prefix="endpoint-audit-probe-") as dirname:
            root = pathlib.Path(dirname)
            for name in ("fixtures.json", "audit_independent.py"):
                (root / name).write_bytes(frozen[name])
            output = json.loads(frozen["candidate_stdout.json"])
            if mutation:
                kind, value = mutation
                first = output["cases"][0]
                if kind == "naive_sum":
                    first["naive_sum"] = value
                else:
                    first["segments"][0] = value
            (root / "candidate_stdout.json").write_text(
                json.dumps(output, sort_keys=True, separators=(",", ":")) + "\n",
                encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(root / "audit_independent.py")],
                cwd=root, text=True, capture_output=True, check=False)
            cases.append({"case": label, "exit_code": proc.returncode,
                          "stdout": proc.stdout.strip(), "stderr": proc.stderr.strip()})

    v2_source = pathlib.Path(__file__).with_name(
        "endpoint_lineage_audit_complete.py").read_bytes()
    v2_hash = hashlib.sha256(v2_source).hexdigest()

    def numeric_paths(node, prefix=()):
        if isinstance(node, dict):
            for key, value in node.items():
                yield from numeric_paths(value, prefix + (key,))
        elif isinstance(node, list):
            for index, value in enumerate(node):
                yield from numeric_paths(value, prefix + (index,))
        elif isinstance(node, str):
            try:
                Fraction(node)
            except (ValueError, ZeroDivisionError):
                return
            yield prefix

    baseline = json.loads(frozen["candidate_stdout.json"])
    paths = list(numeric_paths(baseline))
    v2_cases = []
    for label, path in [("baseline", None)] + [("mutated", p) for p in paths]:
        with tempfile.TemporaryDirectory(prefix="endpoint-audit-v2-") as dirname:
            root = pathlib.Path(dirname)
            (root / "fixtures.json").write_bytes(frozen["fixtures.json"])
            output = json.loads(frozen["candidate_stdout.json"])
            if path is not None:
                target = output
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = str(Fraction(target[path[-1]]) + 1)
            (root / "candidate_stdout.json").write_text(
                json.dumps(output, sort_keys=True, separators=(",", ":")) + "\n",
                encoding="utf-8")
            auditor = root / "audit_complete.py"
            auditor.write_bytes(v2_source)
            proc = subprocess.run([sys.executable, str(auditor)], cwd=root,
                                  text=True, capture_output=True, check=False)
            v2_cases.append({"case": label, "path": list(path) if path else None,
                             "exit_code": proc.returncode,
                             "stdout": proc.stdout.strip(),
                             "stderr_last_line": proc.stderr.strip().splitlines()[-1]
                             if proc.stderr.strip() else ""})

    v2_pass = (v2_cases[0]["exit_code"] == 0 and len(paths) == 38
               and all(row["exit_code"] != 0 and
                       row["stderr_last_line"].startswith("AssertionError:")
                       for row in v2_cases[1:]))

    result = {"allocation": "ENDPOINT-LINEAGE-AUDIT-COVERAGE-20261001-01",
              "source_ref": REF, "source_sha256": EXPECTED,
              "v1_cases": [{"case": row["case"], "exit_code": row["exit_code"],
                            "stdout": row["stdout"]} for row in cases],
              "v1_disposition": "PASS_V1_ACCEPTS_UNAUDITED_FIELD_MUTATIONS"
              if cases[0]["exit_code"] == 0 and cases[1]["exit_code"] == 0
              and cases[2]["exit_code"] == 0 else "FAIL_PREREGISTERED_GAP_NOT_REPRODUCED",
              "v2_auditor_sha256": v2_hash,
              "v2_numeric_string_fields": len(paths),
              "v2_baseline_stdout": v2_cases[0]["stdout"],
              "v2_mutation_checks": [{"path": row["path"],
                                      "exit_code": row["exit_code"],
                                      "rejection": row["stderr_last_line"]}
                                     for row in v2_cases[1:]],
              "v2_disposition": "PASS_ALL_NUMERIC_FIELD_MUTATIONS_REJECTED"
              if v2_pass else "FAIL_V2_COVERAGE_GATE",
              "probe_sha256": hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
              "scope": "frozen synthetic fixture/auditor coverage only"}
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    if (result["v1_disposition"] != "PASS_V1_ACCEPTS_UNAUDITED_FIELD_MUTATIONS"
            or not v2_pass):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
