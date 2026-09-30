"""Independent raw-only check of the local Docker argv construction smoke."""
import hashlib
import json
import sys
from pathlib import Path


def main():
    raw_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])
    raw_bytes = raw_path.read_bytes()
    raw = json.loads(raw_bytes)
    case_bytes = Path("/work/cases.json").read_bytes()
    candidate_bytes = Path("/work/candidate.py").read_bytes()
    cases = json.loads(case_bytes)
    errors = []
    if raw.get("schema") != "entrypoint-argv-smoke-raw-v1": errors.append("schema")
    if raw.get("allocation") != cases["allocation"]: errors.append("allocation")
    if raw.get("base_main_sha") != cases["base_main_sha"]: errors.append("base_main_sha")
    if raw.get("container") != {"image": cases["image"], "platform": cases["platform"], "network": "none"}: errors.append("container")
    if raw.get("image_entrypoint") != ["python3"]: errors.append("entrypoint")
    if raw.get("sys_argv") != cases["expected_argv"] or raw.get("argv_exact") is not True: errors.append("argv")
    if raw.get("preflight") != {"module": "json", "imported_before_runner": True}: errors.append("preflight_order")
    if raw.get("boundary") != {"decision": "PASS_ENTRYPOINT_ARGV_CONSTRUCTION", "runner_calls": 1, "runner_result": "smoke-runner", "preflight_module": "json"}: errors.append("boundary")
    if raw.get("candidate_sha256") != hashlib.sha256(candidate_bytes).hexdigest(): errors.append("candidate_hash")
    if raw.get("input_sha256") != hashlib.sha256(case_bytes).hexdigest(): errors.append("input_hash")
    if any(raw.get(key) != 0 for key in ("formal_runner_invocations", "gui_input_calls", "network_calls", "model_calls")): errors.append("forbidden_calls")
    result = {
        "schema": "entrypoint-argv-smoke-audit-v1",
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "candidate_sha256": hashlib.sha256(candidate_bytes).hexdigest(),
        "input_sha256": hashlib.sha256(case_bytes).hexdigest(),
        "errors": errors,
        "decision": "PASS_LOCAL_ARGV_CONSTRUCTION_ONLY" if not errors else "FAIL",
        "scope": "Python default-entrypoint argv, dependency-preflight ordering, no business/GUI/input behavior",
    }
    out_path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"decision": result["decision"], "errors": errors}, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
