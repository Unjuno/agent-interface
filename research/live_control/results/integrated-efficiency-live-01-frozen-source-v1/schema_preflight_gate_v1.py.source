"""Require endpoint-compatible output schemas before a caller may start a GUI."""
import json
from pathlib import Path

from schema_preflight_v1 import preflight


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")


class SchemaPreflightRefused(RuntimeError):
    def __init__(self, report):
        super().__init__("one or more output schemas are not endpoint compatible")
        self.report = report


def require_compatible(entries, cache_dir, result_dir, workspace):
    """Check every named schema and return only when all are compatible.

    Callers must invoke this function before starting an application process or
    acquiring input authority. The gate itself has no GUI/runtime dependency.
    """
    result_dir = Path(result_dir)
    result_dir.mkdir(parents=True, exist_ok=False)
    results = []
    for entry in entries:
        value = preflight(entry["schema"], cache_dir, result_dir / entry["name"], workspace)
        results.append({"name": entry["name"], "result": value})
    accepted = all(row["result"]["endpoint_status"] == "ENDPOINT_COMPATIBLE" for row in results)
    report = {
        "accepted": accepted,
        "results": results,
        "model_calls": sum(bool(row["result"]["model_call_performed"]) for row in results),
        "fresh_usage_records": sum(row["result"]["usage"] is not None for row in results),
        "authority": "schema compatibility only; grants no GUI or input authority",
    }
    dump(result_dir / "gate-report.json", report)
    if not accepted:
        raise SchemaPreflightRefused(report)
    return report
