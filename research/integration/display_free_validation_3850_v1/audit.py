"""Read-only audit of retained process outputs; no candidate/runner imports."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def audit(data, cases, freeze):
    errors = []
    checks = 0

    def check(ok, reason):
        nonlocal checks
        checks += 1
        if not ok:
            errors.append(reason)

    specs = {c["id"]: c for c in cases["cases"]}
    expected_ids = [environment + "__" + name
                    for environment in cases["environments"] for name in specs]
    rows = data.get("rows", [])
    check(data.get("complete") is True, "incomplete matrix")
    check([r.get("id") for r in rows] == expected_ids, "case order/coverage")
    check(len(rows) == 36, "36 process denominator")
    check(data.get("source_hashes_before") == freeze["sources"], "source before")
    check(data.get("source_hashes_after") == freeze["sources"], "source after")
    summary = Counter()
    for row in rows:
        rid = row.get("id", "?")
        case = specs.get(row.get("case"))
        if case is None:
            check(False, rid + ": unknown case")
            continue
        try:
            report = json.loads(row.get("stdout", ""))
        except (ValueError, TypeError):
            check(False, rid + ": undecodable stdout")
            continue
        check(isinstance(report, dict), rid + ": report type")
        if not isinstance(report, dict):
            continue
        for key, expected in case["expected"].items():
            check(type(report.get(key)) is type(expected) and report.get(key) == expected,
                  rid + ": expected " + key)
        expected_exit = {"valid": 0, "invalid": 1, "input_error": 2}[case["expected"]["status"]]
        check(type(row.get("exit")) is int and row["exit"] == expected_exit, rid + ": exit")
        check(row.get("stderr") == "", rid + ": stderr")
        check(report.get("schema") == "agent-interface/static-program-validation-v1", rid + ": schema")
        check(report.get("side_effect_authority") is False, rid + ": authority")
        check(report.get("backend_checked") is False, rid + ": backend checked")
        check("task_success" in report and report["task_success"] is None, rid + ": task success")
        check(report.get("runtime_admission") == "not_evaluated", rid + ": admission")
        check("PRIVATE_SENTINEL" not in row.get("stdout", ""), rid + ": payload echo")
        check(len(report.get("detail", "")) <= 256, rid + ": detail bound")
        raw = case["raw_text"]
        expected_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest() if raw is not None else None
        check(row.get("input_sha256_before") == expected_hash, rid + ": input before")
        check(row.get("input_sha256_after") == expected_hash, rid + ": input after")
        check(report.get("input_sha256") == expected_hash, rid + ": input report")
        trace = row.get("trace", {})
        check(trace.get("events") == [], rid + ": effect audit events")
        check(trace.get("native_modules") == [], rid + ": native modules")
        check(trace.get("no_site") == 1, rid + ": site packages disabled")
        check(trace.get("wayland_display") is None, rid + ": wayland unset")
        expected_display = None if row.get("environment") == "no_display" else ":59999"
        check(trace.get("display") == expected_display, rid + ": display setting")
        check(trace.get("exit_code") == expected_exit, rid + ": trace exit")
        check(type(trace.get("pid")) is int and trace["pid"] > 0, rid + ": process identity")
        check(type(trace.get("started_ns")) is int and type(trace.get("ended_ns")) is int
              and trace["started_ns"] <= trace["ended_ns"], rid + ": monotonic bracket")
        summary[report.get("status", "unknown")] += 1
    return {"decision": "PASS_DISPLAY_FREE_VALIDATION_ENGINEERING" if not errors else "HOLD_AUDIT",
            "checks": checks, "errors": errors, "processes": len(rows),
            "outcomes": dict(sorted(summary.items())), "scope": "static module only; not runtime admission"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("records", type=Path)
    args = parser.parse_args()
    result = audit(json.loads(args.records.read_text()), json.loads((HERE / "cases.json").read_text()),
                   json.loads((HERE / "FREEZE.json").read_text()))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not result["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
