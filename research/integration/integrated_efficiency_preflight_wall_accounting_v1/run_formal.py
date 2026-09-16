from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT / "fixture.json"
OUTPUT = ROOT / "RESULT.json"
ARMS = ("plain", "ephemeral", "persistent")
DECISION_PASS = "PASS_PREFLIGHT_WALL_ACCOUNTING_RECONSTRUCTED_SCOPED"


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def parse_raw(source: dict) -> dict:
    data = source["raw_text"].encode("utf-8")
    actual = git_blob_sha(data)
    if actual != source["git_blob_sha"]:
        raise ValueError(f"source blob mismatch for {source['path']}: {actual}")
    return json.loads(source["raw_text"], parse_float=Decimal)


def dstr(value: Decimal) -> str:
    return format(value, "f")


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit("formal output already exists; same-ID rerun forbidden")
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    if fixture.get("schema") != "integrated_efficiency_preflight_wall_fixture_v1":
        raise ValueError("fixture schema mismatch")
    audit = parse_raw(fixture["sources"]["audit"])
    if not audit["passed"] or audit["disposition"] != "RETAIN":
        raise ValueError("retained comparison audit must remain passed/RETAIN")

    rows = {}
    integrity = []
    for arm in ARMS:
        preflight = parse_raw(fixture["sources"][f"preflight_{arm}"])
        process = parse_raw(fixture["sources"][f"process_{arm}"])
        preflight_ms = Decimal(str(preflight["elapsed_ms"]))
        task_ms = Decimal(str(audit["elapsed_ms"][arm]))
        process_ms = Decimal(process["exited_ns"] - process["started_ns"]) / Decimal(1_000_000)
        outer_ms = preflight_ms - process_ms
        checks = {
            "endpoint_compatible": preflight["endpoint_status"] == "ENDPOINT_COMPATIBLE",
            "model_call_performed": preflight["model_call_performed"] is True,
            "preflight_elapsed_positive": preflight_ms > 0,
            "process_exit_zero": process["exit_code"] == 0,
            "process_lifetime_positive": process_ms > 0,
            "process_within_preflight": process_ms <= preflight_ms,
            "model_effort_match": (
                preflight["identity"]["requested_model"] == process["requested_model"]
                and preflight["identity"]["requested_effort"] == process["requested_effort"]
            ),
        }
        integrity.extend(checks.values())
        rows[arm] = {
            "task_phase_elapsed_ms": dstr(task_ms),
            "preflight_elapsed_ms": dstr(preflight_ms),
            "phase_complete_elapsed_ms": dstr(task_ms + preflight_ms),
            "preflight_model_subprocess_lifetime_ms": dstr(process_ms),
            "preflight_outer_minus_subprocess_ms": dstr(outer_ms),
            "retained_final_input_tokens": audit["final_input_tokens"][arm],
            "preflight_input_tokens_already_charged": preflight["usage"]["input_tokens"],
            "checks": checks,
        }

    persistent_total = Decimal(rows["persistent"]["phase_complete_elapsed_ms"])
    ordering = {
        arm: persistent_total < Decimal(rows[arm]["phase_complete_elapsed_ms"])
        for arm in ("plain", "ephemeral")
    }
    task_only_not_full = all(
        Decimal(rows[arm]["phase_complete_elapsed_ms"]) > Decimal(rows[arm]["task_phase_elapsed_ms"])
        for arm in ARMS
    )
    integrity_ok = all(integrity)
    if not integrity_ok:
        decision = "FAIL_INTEGRITY"
    elif not all(ordering.values()):
        decision = "FAIL_LATENCY_ORDER_REVERSED"
    elif not task_only_not_full:
        decision = "HOLD_MISSING_PREFLIGHT_WALL_EVIDENCE"
    else:
        decision = DECISION_PASS

    result = {
        "schema": "integrated_efficiency_preflight_wall_result_v1",
        "task": "INTEGRATED-EFFICIENCY-PREFLIGHT-WALL-ACCOUNTING-20260917-001",
        "base": fixture["base"],
        "formal_invocation": 1,
        "decision": decision,
        "original_retained_disposition": audit["disposition"],
        "original_observed_token_break_even_task": audit["observed_break_even_task"],
        "token_break_even_recomputed": False,
        "reason_token_break_even_not_recomputed": "retained protocol already charges preflight input tokens; this allocation changes only wall-time endpoint accounting",
        "rows": rows,
        "persistent_phase_complete_faster_than": ordering,
        "original_audit_elapsed_is_task_phase_only": task_only_not_full,
        "integrity_ok": integrity_ok,
        "protocol_dependency": fixture["protocol_dependency"],
        "limits": [
            "posthoc retained-evidence reconstruction; no new model or GUI call",
            "preflight model subprocess lifetime includes CLI/process overhead and is not model inference time",
            "sequential phase-sum applies only to the retained preflight-then-task schedule",
            "no population latency, monetary cost, human-tempo, or second-domain speed claim"
        ]
    }
    with OUTPUT.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({
        "decision": decision,
        "phase_complete_elapsed_ms": {arm: rows[arm]["phase_complete_elapsed_ms"] for arm in ARMS},
        "persistent_phase_complete_faster_than": ordering
    }, indent=2))


if __name__ == "__main__":
    main()
