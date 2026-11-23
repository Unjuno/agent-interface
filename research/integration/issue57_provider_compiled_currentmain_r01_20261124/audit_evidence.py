"""Independent byte, source, protocol, attempt, and durable-custody audit."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

from research.live_control.calc_durable_allocation_v1 import audit_allocation


PACKET = Path(__file__).resolve().parent
REPO = PACKET.parents[3]
MODES = ("normal", "optimized")
CASES = ("positive", "changed-intermediate")
USAGE = {
    "input_tokens": 1234,
    "cached_input_tokens": 234,
    "cache_write_input_tokens": 0,
    "output_tokens": 56,
    "reasoning_output_tokens": 12,
}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def audit():
    conditions = read_json(PACKET / "CONDITIONS.json")
    require(subprocess.check_output(["git", "rev-parse", "origin/main"],
            cwd=REPO, text=True).strip() == conditions["base_main_sha"],
        "remote main differs from frozen base")
    checked_sources = {}
    for name, expected in conditions["source_sha256"].items():
        actual = sha256((REPO / name).read_bytes())
        require(actual == expected, f"source hash mismatch: {name}")
        checked_sources[name] = actual

    runs = read_json(PACKET / "run_results.json")["runs"]
    require([row["mode"] for row in runs] == list(MODES),
            "normal/optimized run order or count differs")
    case_audits = []
    for run in runs:
        mode = run["mode"]
        require(run["returncode"] == 0, f"{mode} process exit was not zero")
        raw_dir = PACKET / "raw"
        stdout = (raw_dir / f"{mode}.stdout.bin").read_bytes()
        stderr = (raw_dir / f"{mode}.stderr.bin").read_bytes()
        exitcode = (raw_dir / f"{mode}.exitcode.txt").read_text().strip()
        require(sha256(stdout) == run["stdout_sha256"], f"{mode} stdout changed")
        require(sha256(stderr) == run["stderr_sha256"], f"{mode} stderr changed")
        require(exitcode == "0", f"{mode} raw exit receipt is not zero")
        require(b"Ran 1 test" in stderr and b"OK" in stderr,
                f"{mode} unittest summary missing")
        require(b"COMPOSITION_SCENARIOS" in stdout,
                f"{mode} scenario summary missing")

        for case in CASES:
            case_root = PACKET / "attempts" / mode / case
            summary = read_json(case_root / "scenario-summary.json")
            durable_path = case_root / summary["durable_allocation"]
            actual_audit = audit_allocation(durable_path)
            require(actual_audit == summary["durable_audit"],
                    f"{mode}/{case}: durable audit mismatch")
            protocol = [json.loads(line) for line in
                (case_root / "protocol.jsonl").read_text(encoding="utf-8").splitlines()]
            usage_events = [row["message"] for row in protocol
                if row["direction"] == "received" and
                row["message"].get("method") == "thread/tokenUsage/updated"]
            require(usage_events == summary["protocol_usage_events"],
                    f"{mode}/{case}: protocol usage evidence mismatch")
            require(len(usage_events) == 1, f"{mode}/{case}: expected one usage event")
            attempt, = summary["attempt_ledger"]
            usage_event = usage_events[0]
            require(attempt["call_id"] == usage_event["params"]["turnId"],
                    f"{mode}/{case}: provider turn identity did not join")
            require(attempt["thread_id"] == usage_event["params"]["threadId"],
                    f"{mode}/{case}: provider thread identity did not join")
            require(attempt["usage"] == USAGE and
                    summary["accounting"]["usage_totals"] == USAGE,
                    f"{mode}/{case}: usage totals mismatch")

            if case == "positive":
                require(summary["outcome"] == "TASK_SUCCEEDED" and
                        summary["task_effect"] == "succeeded",
                        f"{mode}: positive path did not score success")
                require(summary["actions"] == ["enter_value", "submit"] and
                        summary["admissions"] == ["enter", "submit"],
                        f"{mode}: positive transitions differ")
                require(summary["compiled_receipt"]["outcome"] == "TASK_SUCCEEDED" and
                        summary["compiled_receipt"]["completed_transitions"] == 2,
                        f"{mode}: positive compiled receipt mismatch")
                require(len(summary["independent_score_calls"]) == 1 and
                        summary["durable_audit"]["effect_receipt_persisted"],
                        f"{mode}: independent effect custody missing")
            else:
                require(summary["outcome"] == "EXECUTION_INCOMPLETE" and
                        summary["reason"] == "unknown_state" and
                        summary["delivery"] == "confirmed_partial" and
                        summary["task_effect"] is None,
                        f"{mode}: changed dependency was not retained as partial")
                require(summary["actions"] == ["enter_value"] and
                        summary["admissions"] == ["enter"],
                        f"{mode}: action occurred after changed dependency")
                require(summary["compiled_receipt"]["outcome"] == "SAFE_YIELD" and
                        summary["compiled_receipt"]["completed_transitions"] == 1,
                        f"{mode}: partial compiled receipt mismatch")
                require(summary["independent_score_calls"] == [] and
                        not summary["durable_audit"]["effect_receipt_persisted"],
                        f"{mode}: task success/effect was promoted after partial execution")
            require(summary["durable_audit"]["status"] == "audited" and
                    summary["durable_audit"]["receipt_persisted"],
                    f"{mode}/{case}: execution receipt custody missing")
            case_audits.append({
                "mode": mode,
                "case": case,
                "outcome": summary["outcome"],
                "attempts": len(summary["attempt_ledger"]),
                "usage_joined": True,
                "durable_status": actual_audit["status"],
                "effect_receipt_persisted": actual_audit["effect_receipt_persisted"],
            })

    return {
        "schema": "issue57-provider-compiled-independent-audit-r01",
        "base_main_sha": conditions["base_main_sha"],
        "status": "PASS_SYNTHETIC_COMPOSITION_ONLY",
        "source_hashes_verified": checked_sources,
        "case_audits": case_audits,
        "limits": [
            "The App Server is a local synthetic JSONL peer, not an external provider.",
            "The form state, input, release receipts and independent score are deterministic fixtures.",
            "No live GUI, provider, task allocation, matched economics or recovery reliability was tested.",
        ],
    }


if __name__ == "__main__":
    result = audit()
    (PACKET / "AUDIT.json").write_bytes(
        (json.dumps(result, indent=2) + "\n").encode("utf-8"))
    print(json.dumps(result, sort_keys=True))
