"""Run the frozen unsupported/accepted/cache-reuse schema preflight block."""
import json
from pathlib import Path

from schema_preflight_v1 import preflight

HERE = Path(__file__).resolve().parent
OUT = HERE / "results/schema-preflight-01"


def dump(path, value): path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")


def main():
    plan = json.loads((OUT / "preregistration.json").read_text(encoding="utf-8"))
    cache = OUT / "cache"; workspace = OUT / "empty-workspace"; results = []
    for case in plan["cases"]:
        schema = HERE.parent / case["schema"] if not case["schema"].startswith("live_control/") else HERE.parent / case["schema"]
        value = preflight(schema, cache, OUT / case["name"], workspace)
        results.append({"name": case["name"], "expected": case["expected"], "result": value})
    reuse = preflight(HERE / "bounded_visual_target_contract_schema_v3.json", cache,
                      OUT / "06-cache-reuse", workspace)
    results.append({"name": "06-cache-reuse", "expected": "ENDPOINT_COMPATIBLE_CACHE_HIT", "result": reuse})
    usage_fields = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens", "output_tokens", "reasoning_output_tokens")
    totals = {key: sum(row["result"]["usage"].get(key, 0) for row in results if row["result"]["usage"] is not None)
              for key in usage_fields}
    checks = {}
    for row in results:
        actual = row["result"]["endpoint_status"] + ("_CACHE_HIT" if row["result"]["cache_hit"] else "")
        checks[row["name"]] = actual == row["expected"]
    checks["three_fresh_compatible_calls"] = sum(row["result"]["endpoint_status"] == "ENDPOINT_COMPATIBLE" and
        row["result"]["model_call_performed"] for row in results) == 3
    checks["two_endpoint_schema_refusals"] = sum(row["result"]["endpoint_status"] == "ENDPOINT_INCOMPATIBLE"
        for row in results) == 2
    checks["reuse_has_no_call_or_usage"] = reuse["cache_hit"] and not reuse["model_call_performed"] and reuse["usage"] is None
    report = {"results": results, "usage_total_fresh_compatible_calls": totals,
        "checks": checks, "passed": all(checks.values()),
        "decision": "RETAIN_SCHEMA_PREFLIGHT_V1" if all(checks.values()) else "HOLD_SCHEMA_PREFLIGHT_V1",
        "scope": plan["scope"]}
    dump(OUT / "report.json", report); print(json.dumps(report, indent=2))


if __name__ == "__main__": main()
