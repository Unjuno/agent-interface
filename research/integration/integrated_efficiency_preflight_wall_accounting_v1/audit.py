from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parent
ARMS = ("plain", "ephemeral", "persistent")
EXPECTED_DECISION = "PASS_PREFLIGHT_WALL_ACCOUNTING_RECONSTRUCTED_SCOPED"


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def parse(source: dict) -> dict:
    raw = source["raw_text"].encode("utf-8")
    if git_blob_sha(raw) != source["git_blob_sha"]:
        raise AssertionError("fixture source Git blob mismatch: " + source["path"])
    return json.loads(source["raw_text"], parse_float=Decimal)


def main() -> None:
    fixture = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))
    result = json.loads((ROOT / "RESULT.json").read_text(encoding="utf-8"))
    audit_src = parse(fixture["sources"]["audit"])
    checks = {}
    recomputed = {}
    for arm in ARMS:
        pre = parse(fixture["sources"][f"preflight_{arm}"])
        proc = parse(fixture["sources"][f"process_{arm}"])
        task_ms = Decimal(str(audit_src["elapsed_ms"][arm]))
        pre_ms = Decimal(str(pre["elapsed_ms"]))
        proc_ms = Decimal(proc["exited_ns"] - proc["started_ns"]) / Decimal(1_000_000)
        full_ms = task_ms + pre_ms
        outer_ms = pre_ms - proc_ms
        recomputed[arm] = {
            "task_phase_elapsed_ms": format(task_ms, "f"),
            "preflight_elapsed_ms": format(pre_ms, "f"),
            "phase_complete_elapsed_ms": format(full_ms, "f"),
            "preflight_model_subprocess_lifetime_ms": format(proc_ms, "f"),
            "preflight_outer_minus_subprocess_ms": format(outer_ms, "f")
        }
        row = result["rows"][arm]
        checks[f"{arm}_derived_exact"] = all(row[key] == value for key, value in recomputed[arm].items())
        checks[f"{arm}_preflight_positive"] = pre_ms > 0
        checks[f"{arm}_subprocess_bounded"] = Decimal(0) < proc_ms <= pre_ms
        checks[f"{arm}_source_status"] = (
            pre["endpoint_status"] == "ENDPOINT_COMPATIBLE"
            and pre["model_call_performed"] is True
            and proc["exit_code"] == 0
        )
        checks[f"{arm}_task_elapsed_preserved"] = row["task_phase_elapsed_ms"] == format(task_ms, "f")

    p = Decimal(recomputed["persistent"]["phase_complete_elapsed_ms"])
    checks["persistent_faster_plain"] = p < Decimal(recomputed["plain"]["phase_complete_elapsed_ms"])
    checks["persistent_faster_ephemeral"] = p < Decimal(recomputed["ephemeral"]["phase_complete_elapsed_ms"])
    checks["original_elapsed_is_not_phase_complete"] = all(
        Decimal(recomputed[a]["phase_complete_elapsed_ms"]) > Decimal(recomputed[a]["task_phase_elapsed_ms"])
        for a in ARMS
    )
    checks["decision_exact"] = result["decision"] == EXPECTED_DECISION
    checks["token_break_even_untouched"] = (
        result["original_observed_token_break_even_task"] == audit_src["observed_break_even_task"] == 2
        and result["token_break_even_recomputed"] is False
    )
    passed = all(checks.values())
    payload = {
        "schema": "integrated_efficiency_preflight_wall_audit_v1",
        "passed": passed,
        "decision": result["decision"],
        "checks": checks,
        "recomputed": recomputed,
        "result_sha256": hashlib.sha256((ROOT / "RESULT.json").read_bytes()).hexdigest()
    }
    out = ROOT / "AUDIT.json"
    if out.exists():
        raise SystemExit("audit output already exists")
    with out.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"passed": passed, "decision": result["decision"], "failed": [k for k,v in checks.items() if not v]}, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
