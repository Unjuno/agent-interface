"""Audit the frozen MAP01 schema-v6 endpoint observation after it is run."""
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PREREG = HERE / "map01_schema_v6_preflight_v1_prereg.json"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    plan = read(PREREG)
    output = REPO / plan["output"]
    report = read(output / "report.json")
    checks = {
        "allocation": report["allocation_id"] == plan["allocation_id"],
        "one_request_no_retry": report["endpoint_request_limit"] == 1 and report["retry_limit"] == 0,
        "frozen_sources": all(sha(REPO / name) == digest for name, digest in plan["source_sha256"].items()),
        "no_gui_or_images": not list(output.rglob("*.ait")) and not list(output.rglob("*.png")),
        "empty_workspace": not list((output / "empty-workspace").rglob("*")),
    }
    result = report["result"]
    if result is None:
        checks["retained_wrapper_failure"] = (
            report["failure"] is not None
            and report["disposition"] == "RETAIN_FAILURE_AND_HOLD_V33_LIVE"
        )
    else:
        root = output / "endpoint-preflight"
        process = read(root / "model-call/process.json")
        plan_record = read(root / "model-call/plan.json")
        events = [json.loads(line) for line in (root / "model-call/events.jsonl").read_text(encoding="utf-8").splitlines()]
        turns = [event for event in events if event.get("type") == "turn.completed"]
        messages = [event for event in events if event.get("type") == "item.completed" and event.get("item", {}).get("type") == "agent_message"]
        failures = [event for event in events if event.get("type") in ("error", "turn.failed")]
        checks.update({
            "fresh_call": result["cache_hit"] is False and result["model_call_performed"] is True,
            "exact_model": result["identity"]["requested_model"] == plan["model"],
            "exact_effort": result["identity"]["requested_effort"] == plan["reasoning_effort"],
            "local_schema_valid": result["local_schema_status"] == "VALID",
            "handle_without_image": plan_record["mode"] == process["mode"] == "handle" and plan_record["image_sha256"] is None and "-i" not in plan_record["args"],
        })
        status = result["endpoint_status"]
        if status == "ENDPOINT_COMPATIBLE":
            valid_output = False
            if len(messages) == 1:
                value = json.loads(messages[0]["item"]["text"])
                Draft202012Validator(read(REPO / plan["schema"])).validate(value)
                valid_output = True
            checks["compatible_evidence"] = (
                process["exit_code"] == 0
                and len(turns) == 1
                and valid_output
                and turns[0]["usage"] == result["usage"]
                and report["disposition"] == "SCHEMA_V6_ENDPOINT_COMPATIBLE"
            )
        elif status == "ENDPOINT_INCOMPATIBLE":
            checks["retained_endpoint_refusal"] = (
                process["exit_code"] != 0
                and len(turns) == 0
                and len(failures) >= 1
                and result["usage"] is None
                and report["disposition"] == "RETAIN_ENDPOINT_REFUSAL_AND_HOLD_V33_LIVE"
            )
        else:
            checks["retained_preflight_failure"] = (
                status == "PREFLIGHT_FAILED"
                and report["disposition"] == "RETAIN_FAILURE_AND_HOLD_V33_LIVE"
            )
    audit = {
        "passed": all(checks.values()),
        "checks": checks,
        "observed_status": None if result is None else result["endpoint_status"],
        "usage": None if result is None else result["usage"],
        "scope": plan["scope"],
    }
    (output / "audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))
    return 0 if audit["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
