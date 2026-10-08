"""Raw-only independent check; no candidate import or runner invocation."""
import hashlib
import json
import sys
from pathlib import Path


def main():
    raw_path, out_path = Path(sys.argv[1]), Path(sys.argv[2])
    raw_bytes = raw_path.read_bytes()
    raw = json.loads(raw_bytes)
    input_bytes = Path("/work/cases.json").read_bytes()
    candidate_bytes = Path("/work/candidate.py").read_bytes()
    spec = json.loads(input_bytes)
    expected_boundary = {"decision": "PASS_ENTRYPOINT_ARGV_CONSTRUCTION",
                         "runner_calls": 1, "runner_result": "smoke-runner",
                         "preflight_module": spec["preflight_module"]}
    expected_preflight = {"module": spec["preflight_module"], "imported_before_smoke_runner": True}
    errors = []
    checks = {
        "schema": raw.get("schema") == "entrypoint-argv-smoke-v2-raw-v1",
        "allocation": raw.get("allocation") == spec["allocation"],
        "base": raw.get("base_main_sha") == spec["base_main_sha"],
        "container": raw.get("container") == {"image": spec["image"], "platform": spec["platform"], "network": "none"},
        "image_config": raw.get("image_config") == {"Entrypoint": None, "Cmd": ["python3"]},
        "override": raw.get("entrypoint_override") == ["python3"],
        "resolved_argv": raw.get("resolved_process_argv") == spec["expected_process_argv"],
        "sys_argv": raw.get("sys_argv") == spec["expected_sys_argv"] and raw.get("argv_exact") is True,
        "preflight": raw.get("preflight") == expected_preflight,
        "runner": raw.get("boundary") == expected_boundary,
        "candidate_hash": raw.get("candidate_sha256") == hashlib.sha256(candidate_bytes).hexdigest(),
        "input_hash": raw.get("input_sha256") == hashlib.sha256(input_bytes).hexdigest(),
        "no_forbidden_calls": all(raw.get(k) == 0 for k in ("formal_runner_invocations", "gui_input_calls", "network_calls", "model_calls")),
    }
    errors.extend(name for name, passed in checks.items() if not passed)
    result = {"schema": "entrypoint-argv-smoke-v2-audit-v1",
              "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
              "candidate_sha256": hashlib.sha256(candidate_bytes).hexdigest(),
              "input_sha256": hashlib.sha256(input_bytes).hexdigest(),
              "checks": checks, "errors": errors,
              "decision": "PASS_LOCAL_ARGV_CONSTRUCTION_ONLY" if not errors else "FAIL",
              "scope": "effective Python process argv and preflight ordering only; no Xlib/Xvfb/owner runner/GUI/input"}
    out_path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"decision": result["decision"], "errors": errors}, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
