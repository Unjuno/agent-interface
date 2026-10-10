"""Versioned independent audit correcting A01's omitted-false flag assumption."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit() -> dict:
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8-sig"))
    result = json.loads((HERE / "RESULT.json").read_text(encoding="utf-8-sig"))
    checks = []

    def record(name, ok, detail):
        checks.append({"name": name, "passed": bool(ok), "detail": detail})

    pinned = all((ROOT / entry["path"]).is_file()
                 and digest(ROOT / entry["path"]) == entry["sha256"]
                 for entry in freeze["files"])
    record("frozen_source_and_input_hashes", pinned,
           f"checked {len(freeze['files'])} frozen files")

    source = ROOT / freeze["input_path"]
    events = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines()]
    downs = [row for row in events if row.get("event") == "input_admission"]
    ups = [row for row in events if row.get("event") == "input_release_measurement"]
    down, up = downs[0] if len(downs) == 1 else {}, ups[0] if len(ups) == 1 else {}
    identity_fields = ("id", "step", "key", "owner_id", "intent_token")
    same_identity = bool(down and up) and all(down.get(key) == up.get(key)
                                               for key in identity_fields)
    down_measure = down.get("physical_key_measurement", {})
    up_measure = up.get("physical_key_measurement", {})
    down_edge = down_measure.get("adapter_edge", {})
    up_edge = up_measure.get("adapter_edge", {})
    down_interval = down_edge.get("interval")
    up_interval = up_edge.get("interval")
    boundary = (up_interval[1] if isinstance(up_interval, list) and len(up_interval) == 2
                and type(up_interval[1]) is int else None)
    no_authority = all(
        row.get("grants_input_authority", False) is False
        and row.get("physical_key_measurement", {}).get("grants_input_authority") is False
        and row.get("physical_key_measurement", {}).get("adapter_edge", {}).get(
            "grants_input_authority") is False
        for row in (down, up))
    edge_evidence = (
        same_identity and no_authority
        and down.get("event") == "input_admission"
        and up.get("event") == "input_release_measurement"
        and type(down.get("step")) is int and down["step"] >= 0
        and down_edge.get("edge") == "down"
        and down_edge.get("status") == "CONFIRMED_PHYSICAL_DOWN"
        and up_measure.get("classification") == "CONFIRMED_PHYSICAL_UP"
        and up_measure.get("identity_status") == "RETIRED"
        and up_edge.get("edge") == "up"
        and up_edge.get("status") == "CONFIRMED_PHYSICAL_UP"
        and up_measure.get("actuation_id") == down_measure.get("actuation_id")
        and down_edge.get("actuation_id") == down_measure.get("actuation_id")
        and up_edge.get("actuation_id") == down_measure.get("actuation_id")
        and isinstance(down_interval, list) and len(down_interval) == 2
        and all(type(value) is int for value in down_interval)
        and isinstance(up_interval, list) and len(up_interval) == 2
        and all(type(value) is int for value in up_interval)
        and down_interval[1] <= up_interval[0]
        and up_measure.get("application_consumption_observed") is False
        and up_measure.get("release_attempted") is True
        and boundary == freeze["expected_release_boundary_ns"]
    )
    record("raw_pair_identity_actuation_and_measured_boundary", edge_evidence,
           f"distinct labels={down.get('event')}/{up.get('event')}; "
           f"physical-up upper endpoint={boundary}")

    output_summary = {}
    all_runs = True
    for filename, key in (("WSL_TEST_OUTPUT.txt", "wsl_core"),
                          ("WINDOWS_TEST_OUTPUT.txt", "windows_compatibility")):
        path = HERE / filename
        text = path.read_text(encoding="utf-8-sig") if path.is_file() else ""
        count_match = re.search(r"Ran (\d+) tests? in [^\r\n]+", text)
        exit_code = result.get("exit_codes", {}).get(key)
        ok = (count_match is not None and re.search(r"\nOK(?:\s|$)", text) is not None
              and "\nFAILED" not in text and exit_code == 0)
        if key == "wsl_core":
            compact = re.sub(r"\s+", "", text)
            readiness_case = re.escape(
                "test_measured_tail_yields_to_ready_command_without_consuming_it")
            ok = ok and re.search(readiness_case + r"\(.*?\)\.\.\.ok", compact) is not None
        all_runs &= ok
        output_summary[key] = {"passed": ok,
                               "test_count": int(count_match.group(1)) if count_match else None,
                               "exit_code": exit_code}
    record("retained_platform_test_outputs", all_runs,
           json.dumps(output_summary, sort_keys=True))

    summary_valid = (result.get("experiment_id") == freeze["experiment_id"]
                     and result.get("disposition") == "PASS"
                     and result.get("expected_release_boundary_ns") == boundary
                     and result.get("scope", "").startswith("construction-only"))
    record("result_identity_decision_and_scope", summary_valid,
           "result identity, decision boundary, and construction-only limit")

    prior = HERE / "AUDIT_ATTEMPT_V1.json"
    prior_failure_retained = False
    if prior.is_file():
        prior_data = json.loads(prior.read_text(encoding="utf-8-sig"))
        prior_failure_retained = prior_data.get("disposition") == "FAIL_AUDIT"
    record("first_audit_failure_preserved", prior_failure_retained,
           "version-one audit failure remains available as a separate artifact")
    passed = all(item["passed"] for item in checks)
    return {
        "schema": "v39-perkey-scorer-tail-a01-independent-audit-v2",
        "experiment_id": freeze["experiment_id"],
        "auditor_sha256": digest(Path(__file__).resolve()),
        "prior_audit": {
            "artifact": "AUDIT_ATTEMPT_V1.json",
            "disposition": "FAIL_AUDIT",
            "cause": "v1 required an explicit top-level false authority flag; input_admission omits it and schema defaults it to false",
        },
        "disposition": "PASS_AUDIT" if passed else "FAIL_AUDIT",
        "checks": checks,
        "scope": "Independent reconstruction of frozen source, event, and test-result claims; construction-only.",
        "limits": ["fake-display source trace", "no live game or OS input",
                   "no application-consumption, useful-feedback, recovery, or task-effect evidence"],
    }


if __name__ == "__main__":
    report = audit()
    (HERE / "AUDIT_V2.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                                         encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["disposition"] == "PASS_AUDIT" else 1)
