"""Run exactly one frozen no-GUI endpoint preflight for MAP01 schema v6."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import traceback


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PREREG = HERE / "map01_schema_v6_preflight_v1_prereg.json"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    temporary = Path(str(path) + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def verify(plan):
    checks = {}
    for name, digest in plan["source_sha256"].items():
        path = REPO / name
        checks[name] = path.is_file() and sha(path) == digest
    output = REPO / plan["output"]
    checks["output_absent"] = not output.exists()
    checks["one_request_no_retry"] = plan["endpoint_request_limit"] == 1 and plan["retry_limit"] == 0
    checks["luna_low_no_image"] = (
        plan["model"] == "gpt-5.6-luna"
        and plan["reasoning_effort"] == "low"
        and plan["image_inputs"] == 0
        and plan["gui_authority"] is False
    )
    return checks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    plan = read(PREREG)
    checks = verify(plan)
    verification = {"passed": all(checks.values()), "checks": checks}
    if args.verify_only:
        print(json.dumps(verification, indent=2))
        return 0 if verification["passed"] else 1
    if not verification["passed"]:
        raise RuntimeError(f"frozen preflight verification failed: {checks}")
    if os.name == "nt" or not Path("/mnt/c").is_dir():
        raise RuntimeError("run the frozen endpoint preflight from WSL")

    # Import only after the frozen files and execution environment have passed.
    import sys
    sys.path.insert(0, str(REPO / "research/live_control"))
    from schema_preflight_v1 import preflight

    output = REPO / plan["output"]
    output.mkdir(parents=True, exist_ok=False)
    workspace = output / "empty-workspace"
    workspace.mkdir()
    result = None
    failure = None
    try:
        result = preflight(
            REPO / plan["schema"],
            output / "cache",
            output / "endpoint-preflight",
            workspace,
        )
    except BaseException as error:
        failure = {
            "type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
        }

    disposition = "RETAIN_FAILURE_AND_HOLD_V33_LIVE"
    if result is not None and result["endpoint_status"] == "ENDPOINT_COMPATIBLE":
        disposition = "SCHEMA_V6_ENDPOINT_COMPATIBLE"
    elif result is not None and result["endpoint_status"] == "ENDPOINT_INCOMPATIBLE":
        disposition = "RETAIN_ENDPOINT_REFUSAL_AND_HOLD_V33_LIVE"
    report = {
        "allocation_id": plan["allocation_id"],
        "verification": verification,
        "endpoint_request_limit": 1,
        "retry_limit": 0,
        "preflight_returned": result is not None,
        "result": result,
        "failure": failure,
        "disposition": disposition,
        "scope": plan["scope"],
    }
    dump(output / "report.json", report)
    print(json.dumps(report, indent=2))
    return 0 if result is not None else 1


if __name__ == "__main__":
    raise SystemExit(main())
