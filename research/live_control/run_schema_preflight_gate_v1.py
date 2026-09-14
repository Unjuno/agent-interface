"""Run the frozen negative and cached-positive schema authority gates."""
import json
from pathlib import Path
import shutil

from schema_preflight_gate_v1 import SchemaPreflightRefused, require_compatible

HERE = Path(__file__).resolve().parent
OUT = HERE / "results/schema-preflight-gate-01"
SEED = HERE / "results/schema-preflight-01/cache"


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")


def resolve(entries):
    return [{"name": entry["name"], "schema": HERE.parent / entry["schema"]} for entry in entries]


def main():
    plan = json.loads((OUT / "preregistration.json").read_text(encoding="utf-8"))
    cache = OUT / "cache"
    shutil.copytree(SEED, cache)
    refused = None
    try:
        require_compatible(resolve(plan["negative"]), cache, OUT / "negative-gate", OUT / "empty-workspace")
    except SchemaPreflightRefused as error:
        refused = error.report
    positive = require_compatible(resolve(plan["positive"]), cache, OUT / "positive-gate", OUT / "empty-workspace")
    negative_result = refused["results"][0]["result"] if refused else None
    checks = {
        "negative_refused": refused is not None and refused["accepted"] is False,
        "negative_is_remaining_oneof": negative_result is not None and
            negative_result["endpoint_status"] == "ENDPOINT_INCOMPATIBLE" and
            "'oneOf' is not permitted" in json.dumps(negative_result["endpoint_error"]),
        "negative_fresh_request_without_usage": negative_result is not None and
            negative_result["model_call_performed"] is True and negative_result["usage"] is None,
        "positive_accepted": positive["accepted"] is True,
        "positive_all_cache_hits": all(row["result"]["cache_hit"] and
            not row["result"]["model_call_performed"] and row["result"]["usage"] is None
            for row in positive["results"]),
    }
    report = {
        "negative_gate": refused,
        "positive_gate": positive,
        "checks": checks,
        "passed": all(checks.values()),
        "decision": "RETAIN_SCHEMA_AUTHORITY_GATE_V1" if all(checks.values()) else "HOLD_SCHEMA_AUTHORITY_GATE_V1",
        "scope": plan["scope"],
    }
    dump(OUT / "report.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__": main()
