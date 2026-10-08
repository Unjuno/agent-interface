"""Raw-only independent auditor for the seven fake-child boundary cases."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

OUT = Path("/out")
NAMES = ("exit-0", "exit-23", "timeout", "missing-executable",
         "malformed-json", "idle-once", "sorted-once")


def receipt(case: dict, request_id: str):
    text = case["ipc"].get(request_id + ".broker.json")
    return json.loads(text) if isinstance(text, str) else None


def validate(raw: dict) -> list[str]:
    errors = []
    if raw.get("allocation") != "broker-fake-child-boundary-4485-20260928-02":
        errors.append("allocation")
    cases = raw.get("cases")
    if not isinstance(cases, list) or len(cases) != len(NAMES):
        return errors + ["case_count"]
    by_name = {case.get("name"): case for case in cases if isinstance(case, dict)}
    if set(by_name) != set(NAMES):
        errors.append("case_names")
        return errors
    if raw.get("authority_granted") is not False:
        errors.append("global_authority")

    ok = by_name["exit-0"]
    r = receipt(ok, "exit-0")
    if ok.get("process_code") != 0 or ok.get("external_timeout") is not False:
        errors.append("exit_0_process")
    if not r or r.get("returncode") != 0 or r.get("authority_granted") is not False:
        errors.append("exit_0_receipt")
    if ok["ipc"].get("exit-0.response.jsonl") != "fake-response-exit-0\n":
        errors.append("exit_0_response")
    if len(ok.get("calls", [])) != 1 or ok["calls"][0].get("stdin") != "prompt:exit-0\n":
        errors.append("exit_0_child")

    nonzero = by_name["exit-23"]
    r = receipt(nonzero, "exit-23")
    if nonzero.get("process_code") != 23 or not r or r.get("returncode") != 23:
        errors.append("exit_23_propagation")
    if r and r.get("authority_granted") is not False:
        errors.append("exit_23_authority")
    if len(nonzero.get("calls", [])) != 1:
        errors.append("exit_23_child")

    timeout = by_name["timeout"]
    r = receipt(timeout, "timeout")
    if timeout.get("process_code") != 1 or r is None:
        errors.append("timeout_process")
    if r and (r.get("returncode") is not None
              or r.get("error_class") != "TimeoutExpired"
              or r.get("stop_reason") != "HOST_BROKER_SUBPROCESS_TIMEOUT"
              or r.get("authority_granted") is not False):
        errors.append("timeout_receipt")
    if timeout["ipc"].get("timeout.response.jsonl") != "":
        errors.append("timeout_response")
    if len(timeout.get("calls", [])) != 1:
        errors.append("timeout_child")

    missing = by_name["missing-executable"]
    r = receipt(missing, "missing-executable")
    if missing.get("process_code") != 1 or r is None:
        errors.append("missing_process")
    if r and (r.get("returncode") is not None
              or r.get("error_class") != "FileNotFoundError"
              or r.get("stop_reason") != "HOST_BROKER_EXECUTABLE_UNAVAILABLE"
              or r.get("authority_granted") is not False):
        errors.append("missing_receipt")
    if missing["ipc"].get("missing-executable.response.jsonl") != "":
        errors.append("missing_response")
    if missing.get("calls"):
        errors.append("missing_child_called")

    malformed = by_name["malformed-json"]
    if malformed.get("process_code") in (None, 0) or malformed.get("external_timeout"):
        errors.append("malformed_process")
    if malformed.get("calls"):
        errors.append("malformed_child_called")
    if "00.request.json" not in malformed.get("ipc", {}):
        errors.append("malformed_input_missing")
    if any(name.endswith(".broker.json") or name.endswith(".response.jsonl")
           for name in malformed.get("ipc", {})):
        errors.append("malformed_output_emitted")

    idle = by_name["idle-once"]
    if idle.get("external_timeout") is not True or idle.get("process_code") != -9:
        errors.append("idle_not_bounded")
    if idle.get("ipc") or idle.get("calls"):
        errors.append("idle_side_effect")

    sorted_case = by_name["sorted-once"]
    a = receipt(sorted_case, "a")
    if sorted_case.get("process_code") != 0 or not a or a.get("returncode") != 0:
        errors.append("sorted_first")
    if "z.request.json" not in sorted_case.get("ipc", {}):
        errors.append("sorted_later_request_missing")
    if any(key.startswith("z.") and key.endswith((".broker.json", ".response.jsonl"))
           for key in sorted_case.get("ipc", {})):
        errors.append("sorted_second_handled")
    if len(sorted_case.get("calls", [])) != 1:
        errors.append("sorted_child_count")
    elif sorted_case["calls"][0].get("stdin") != "prompt:a\n":
        errors.append("sorted_child_order")
    if a and a.get("authority_granted") is not False:
        errors.append("sorted_authority")
    return errors


def main() -> int:
    raw_path = OUT / "raw.json"
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    baseline = validate(raw)
    mutations = {}

    changed = copy.deepcopy(raw); changed["cases"].pop()
    mutations["drop_case"] = validate(changed)
    changed = copy.deepcopy(raw)
    case = next(c for c in changed["cases"] if c["name"] == "exit-0")
    r = json.loads(case["ipc"]["exit-0.broker.json"]); r["returncode"] = 4
    case["ipc"]["exit-0.broker.json"] = json.dumps(r)
    mutations["wrong_exit_receipt"] = validate(changed)
    changed = copy.deepcopy(raw)
    case = next(c for c in changed["cases"] if c["name"] == "exit-0")
    r = json.loads(case["ipc"]["exit-0.broker.json"]); r["authority_granted"] = True
    case["ipc"]["exit-0.broker.json"] = json.dumps(r)
    mutations["authority_escalation"] = validate(changed)
    changed = copy.deepcopy(raw)
    case = next(c for c in changed["cases"] if c["name"] == "timeout")
    r = json.loads(case["ipc"]["timeout.broker.json"]); r["stop_reason"] = "NONE"
    case["ipc"]["timeout.broker.json"] = json.dumps(r)
    mutations["timeout_relabel"] = validate(changed)
    changed = copy.deepcopy(raw)
    case = next(c for c in changed["cases"] if c["name"] == "malformed-json")
    case["calls"] = [{"stdin": "unexpected"}]
    mutations["malformed_child"] = validate(changed)
    changed = copy.deepcopy(raw)
    case = next(c for c in changed["cases"] if c["name"] == "exit-0")
    del case["ipc"]["exit-0.response.jsonl"]
    mutations["missing_response"] = validate(changed)
    changed = copy.deepcopy(raw)
    case = next(c for c in changed["cases"] if c["name"] == "sorted-once")
    case["ipc"]["z.broker.json"] = json.dumps({"returncode": 0})
    mutations["second_request_handled"] = validate(changed)
    changed = copy.deepcopy(raw)
    case = next(c for c in changed["cases"] if c["name"] == "idle-once")
    case["external_timeout"] = False
    mutations["idle_unbounded"] = validate(changed)

    rejected = {name: bool(errors) for name, errors in mutations.items()}
    failures = list(baseline)
    if any(not value for value in rejected.values()):
        failures.append("mutation_accepted")
    status = "PASS_BROKER_FAKE_CHILD_BOUNDARY_SCOPED" if not failures else "FAIL_AUDIT"
    report = {
        "status": status, "cases": len(raw.get("cases", [])),
        "audit_errors": failures, "corruption_controls_rejected": sum(rejected.values()),
        "corruption_controls_total": len(rejected),
        "control_results": rejected,
        "raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
        "scope": "local fake executable and host broker subprocess boundary only",
        "authority_granted": False,
    }
    (OUT / "audit.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                                    encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    (OUT / "audit.exit").write_text(("0" if not failures else "1") + "\n",
                                    encoding="ascii")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())

